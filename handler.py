import os
import io
import uuid
import base64
import copy
import cv2
import insightface
import numpy as np
import traceback
import runpod
import requests
import torch
from runpod.serverless.utils.rp_validator import validate
from runpod.serverless.modules.rp_logger import RunPodLogger
from typing import List, Union
from PIL import Image
from restoration import * # Pastikan file restoration.py dan dependencies-nya ada
from schemas.input import INPUT_SCHEMA # Pastikan file schemas/input.py ada

# --- Constants ---
FACE_SWAP_MODEL = 'checkpoints/inswapper_128.onnx'
logger = RunPodLogger()

# ---------------------------------------------------------------------------- #
# Application Functions                                                        #
# ---------------------------------------------------------------------------- #

def get_face_swap_model(model_path: str):
    model = insightface.model_zoo.get_model(model_path)
    return model

def get_face_analyser(model_path: str, torch_device: str, det_size=(320, 320)):
    if torch_device == 'cuda':
        providers = ['CUDAExecutionProvider']
    else:
        providers = ['CPUExecutionProvider']

    face_analyser = insightface.app.FaceAnalysis(
        name="buffalo_l",
        root="./checkpoints",
        providers=providers
    )
    face_analyser.prepare(ctx_id=0, det_size=det_size)
    return face_analyser

def get_many_faces(face_analyser, frame: np.ndarray):
    try:
        face = face_analyser.get(frame)
        return sorted(face, key=lambda x: x.bbox[0])
    except IndexError:
        return None

def swap_face(source_faces, target_faces, source_index, target_index, temp_frame):
    global FACE_SWAPPER
    source_face = source_faces[source_index]
    target_face = target_faces[target_index]
    return FACE_SWAPPER.get(temp_frame, target_face, source_face, paste_back=True)

def process(job_id: str, source_img: Union[Image.Image, List], target_img: Image.Image, source_indexes: str, target_indexes: str):
    global FACE_ANALYSER
    target_img_np = cv2.cvtColor(np.array(target_img), cv2.COLOR_RGB2BGR)
    target_faces = get_many_faces(FACE_ANALYSER, target_img_np)
    
    if not target_faces:
        raise Exception('The target image does not contain any faces!')

    num_target_faces = len(target_faces)
    num_source_images = len(source_img)
    temp_frame = copy.deepcopy(target_img_np)

    if isinstance(source_img, list) and num_source_images == num_target_faces:
        for i in range(num_target_faces):
            source_faces = get_many_faces(FACE_ANALYSER, cv2.cvtColor(np.array(source_img[i]), cv2.COLOR_RGB2BGR))
            if not source_faces:
                raise Exception(f'No source faces found in source image at index {i}!')
            temp_frame = swap_face(source_faces, target_faces, 0, i, temp_frame) # Asumsi 1 wajah per gambar sumber
    elif num_source_images == 1:
        source_faces = get_many_faces(FACE_ANALYSER, cv2.cvtColor(np.array(source_img[0]), cv2.COLOR_RGB2BGR))
        if not source_faces:
            raise Exception('No source faces found!')
        
        num_source_faces = len(source_faces)

        if target_indexes == "-1":
            num_iterations = min(num_source_faces, num_target_faces)
            for i in range(num_iterations):
                source_index = 0 if num_source_faces == 1 else i
                temp_frame = swap_face(source_faces, target_faces, source_index, i, temp_frame)
        else:
            source_indexes_list = source_indexes.split(',')
            target_indexes_list = target_indexes.split(',')
            for s_idx_str, t_idx_str in zip(source_indexes_list, target_indexes_list):
                s_idx, t_idx = int(s_idx_str), int(t_idx_str)
                if s_idx >= num_source_faces or t_idx >= num_target_faces:
                    raise ValueError(f"Index out of range. Source faces: {num_source_faces}, Target faces: {num_target_faces}.")
                temp_frame = swap_face(source_faces, target_faces, s_idx, t_idx, temp_frame)
    else:
        raise Exception('Unsupported face configuration. Number of source images must be 1 or equal to the number of target faces.')

    return Image.fromarray(cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB))

def open_image_from_input(source: str) -> Image.Image:
    """
    Opens an image from a URL or a base64 string.
    """
    if source.startswith('http'):
        try:
            response = requests.get(source, timeout=15)
            response.raise_for_status()
            image_data = response.content
            return Image.open(io.BytesIO(image_data)).convert("RGB")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to download image from URL: {e}")
    else:
        # Asumsikan input adalah base64 jika bukan URL
        try:
            image_data = base64.b64decode(source)
            return Image.open(io.BytesIO(image_data)).convert("RGB")
        except Exception as e:
            raise Exception(f"Failed to decode base64 image: {e}")


def face_swap_api(job_id: str, job_input: dict):
    global TORCH_DEVICE, CODEFORMER_DEVICE, CODEFORMER_NET, upsampler

    try:
        source_image_urls = job_input['source_image'].split(';')
        
        source_images = [open_image_from_input(url) for url in source_image_urls]
        target_image = open_image_from_input(job_input['target_image'])
        
        result_image = process(
            job_id, source_images, target_image,
            job_input['source_indexes'], job_input['target_indexes']
        )

        if job_input.get('face_restore', False):
            result_image_np = cv2.cvtColor(np.array(result_image), cv2.COLOR_RGB2BGR)
            restored_img_np = face_restoration(
                result_image_np, 
                job_input.get('background_enhance', False), 
                job_input.get('face_upsample', False), 
                job_input.get('upscale', 1), 
                job_input.get('codeformer_fidelity', 0.5),
                upsampler, 
                CODEFORMER_NET, 
                CODEFORMER_DEVICE
            )
            result_image = Image.fromarray(cv2.cvtColor(restored_img_np, cv2.COLOR_BGR2RGB))

        output_buffer = io.BytesIO()
        output_format = job_input.get('output_format', 'PNG').upper()
        if output_format not in ['PNG', 'JPEG', 'WEBP']:
            output_format = 'PNG'
            
        result_image.save(output_buffer, format=output_format)
        image_data = output_buffer.getvalue()
        
        return {'image': base64.b64encode(image_data).decode('utf-8')}

    except Exception as e:
        logger.error(f'Error: {e}', job_id)
        return {
            'error': str(e),
            'output': traceback.format_exc(),
            'refresh_worker': True
        }

def handler(event):
    job_id = event.get('id', 'local_test')
    validated_input = validate(event['input'], INPUT_SCHEMA)

    if 'errors' in validated_input:
        return {'error': validated_input['errors']}

    return face_swap_api(job_id, validated_input['validated_input'])

# --- Main Execution Block ---
if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if torch.cuda.is_available():
        TORCH_DEVICE = 'cuda'
    else:
        TORCH_DEVICE = 'cpu'
    
    logger.info(f'Using Torch device: {TORCH_DEVICE.upper()}')

    model_path = os.path.join(script_dir, FACE_SWAP_MODEL)
    logger.info(f'Loading Face Swap model: {model_path}')
    FACE_SWAPPER = get_face_swap_model(model_path)
    
    logger.info('Loading Face Analyser model...')
    FACE_ANALYSER = get_face_analyser(model_path, TORCH_DEVICE)
    
    # Setup for face restoration
    check_ckpts() # Pastikan fungsi ini ada di restoration.py
    logger.info('Setting up RealESRGAN_x2plus upsampler...')
    upsampler = set_realesrgan() # Pastikan fungsi ini ada di restoration.py
    CODEFORMER_DEVICE = torch.device(TORCH_DEVICE)

    logger.info('Loading CodeFormer model...')
    CODEFORMER_NET = ARCH_REGISTRY.get('CodeFormer')(dim_embd=512, codebook_size=1024, n_head=8, n_layers=9, connect_list=['32', '64', '128', '256']).to(CODEFORMER_DEVICE)
    ckpt_path = 'CodeFormer/weights/CodeFormer/codeformer.pth'
    codeformer_checkpoint = torch.load(ckpt_path)['params_ema']
    CODEFORMER_NET.load_state_dict(codeformer_checkpoint)
    CODEFORMER_NET.eval()
    
    logger.info('Initialization complete. Starting RunPod Serverless...')
    runpod.serverless.start({'handler': handler})
