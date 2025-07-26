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
from runpod.serverless.utils.rp_validator import validate
from runpod.serverless.modules.rp_logger import RunPodLogger
from typing import List, Union
from PIL import Image
from restoration import *
from schemas.input import INPUT_SCHEMA

FACE_SWAP_MODEL = 'checkpoints/inswapper_128.onnx'
TMP_PATH = '/tmp/inswapper'
logger = RunPodLogger()

# ---------------------------------------------------------------------------- #
# Application Functions                                                        #
# ---------------------------------------------------------------------------- #
def get_face_swap_model(model_path: str):
    model = insightface.model_zoo.get_model(model_path)
    return model

def get_face_analyser(model_path: str, torch_device: str, det_size=(320, 320)):
    if torch_device == 'cuda':
        providers=['CUDAExecutionProvider']
    else:
        providers=['CPUExecutionProvider']

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
    global MODEL, FACE_ANALYSER
    target_img = cv2.cvtColor(np.array(target_img), cv2.COLOR_RGB2BGR)
    target_faces = get_many_faces(FACE_ANALYSER, target_img)
    num_target_faces = len(target_faces)
    num_source_images = len(source_img)

    if target_faces is not None:
        if num_target_faces == 0:
            raise Exception('The target image does not contain any faces!')

        temp_frame = copy.deepcopy(target_img)

        if isinstance(source_img, list) and num_source_images == num_target_faces:
            for i in range(num_target_faces):
                source_faces = get_many_faces(FACE_ANALYSER, cv2.cvtColor(np.array(source_img[i]), cv2.COLOR_RGB2BGR))
                if source_faces is None:
                    raise Exception('No source faces found!')
                temp_frame = swap_face(source_faces, target_faces, i, i, temp_frame)
        elif num_source_images == 1:
            source_faces = get_many_faces(FACE_ANALYSER, cv2.cvtColor(np.array(source_img[0]), cv2.COLOR_RGB2BGR))
            num_source_faces = len(source_faces)
            if source_faces is None or num_source_faces == 0:
                raise Exception('No source faces found!')

            if target_indexes == "-1":
                num_iterations = min(num_source_faces, num_target_faces)
                for i in range(num_iterations):
                    source_index = 0 if num_source_faces == 1 else i
                    temp_frame = swap_face(source_faces, target_faces, source_index, i, temp_frame)
            else:
                source_indexes = source_indexes.split(',')
                target_indexes = target_indexes.split(',')
                for s_idx, t_idx in zip(source_indexes, target_indexes):
                    temp_frame = swap_face(source_faces, target_faces, int(s_idx), int(t_idx), temp_frame)
        else:
            raise Exception('Unsupported face configuration')

        result = temp_frame
    else:
        raise Exception('No target faces found!')

    return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))

def face_swap(job_id: str, src_img_path, target_img_path, source_indexes, target_indexes, background_enhance, face_restore, face_upsample, upscale, codeformer_fidelity, output_format):
    global TORCH_DEVICE, CODEFORMER_DEVICE, CODEFORMER_NET
    source_img_paths = src_img_path.split(';')
    source_img = [Image.open(img_path) for img_path in source_img_paths]
    target_img = Image.open(target_img_path)

    result_image = process(job_id, source_img, target_img, source_indexes, target_indexes)

    if face_restore:
        result_image = cv2.cvtColor(np.array(result_image), cv2.COLOR_RGB2BGR)
        result_image = face_restoration(result_image, background_enhance, face_upsample, upscale, codeformer_fidelity, upsampler, CODEFORMER_NET, CODEFORMER_DEVICE)
        result_image = Image.fromarray(result_image)

    output_buffer = io.BytesIO()
    result_image.save(output_buffer, format=output_format)
    image_data = output_buffer.getvalue()
    return base64.b64encode(image_data).decode('utf-8')

def determine_file_extension(image_data):
    if image_data.startswith('/9j/'):
        return '.jpg'
    elif image_data.startswith('iVBORw0Kg'):
        return '.png'
    return '.png'

def face_swap_api(job_id: str, job_input: dict):
    if not os.path.exists(TMP_PATH):
        os.makedirs(TMP_PATH)

    unique_id = uuid.uuid4()

    def download_image(url, prefix):
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        image_data = response.content
        ext = determine_file_extension(base64.b64encode(image_data).decode('utf-8'))
        path = f'{TMP_PATH}/{prefix}_{unique_id}{ext}'
        with open(path, 'wb') as f:
            f.write(image_data)
        return path

    try:
        source_image_path = download_image(job_input['source_image'], 'source')
        target_image_path = download_image(job_input['target_image'], 'target')

        result_image = face_swap(job_id, source_image_path, target_image_path,
                                 job_input['source_indexes'], job_input['target_indexes'],
                                 job_input['background_enhance'], job_input['face_restore'],
                                 job_input['face_upsample'], job_input['upscale'],
                                 job_input['codeformer_fidelity'], job_input['output_format'])

        os.remove(source_image_path)
        os.remove(target_image_path)

        return { 'image': result_image }

    except Exception as e:
        logger.error(f'Error: {e}', job_id)
        if os.path.exists(source_image_path):
            os.remove(source_image_path)
        if os.path.exists(target_image_path):
            os.remove(target_image_path)
        return {
            'error': str(e),
            'output': traceback.format_exc(),
            'refresh_worker': True
        }

def handler(event):
    job_id = event['id']
    validated_input = validate(event['input'], INPUT_SCHEMA)

    if 'errors' in validated_input:
        return { 'error': validated_input['errors'] }

    return face_swap_api(job_id, validated_input['validated_input'])

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    MODEL = os.path.join(script_dir, FACE_SWAP_MODEL)
    model_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), MODEL)
    logger.info(f'Face swap model: {MODEL}')

    if torch.cuda.is_available():
        TORCH_DEVICE = 'cuda'
    else:
        TORCH_DEVICE = 'cpu'

    logger.info(f'Torch device: {TORCH_DEVICE.upper()}')
    FACE_ANALYSER = get_face_analyser(MODEL, TORCH_DEVICE)
    FACE_SWAPPER = get_face_swap_model(model_path)

    check_ckpts()
    logger.info('Setting upsampler to RealESRGAN_x2plus')
    upsampler = set_realesrgan()
    CODEFORMER_DEVICE = torch.device(TORCH_DEVICE)

    CODEFORMER_NET = ARCH_REGISTRY.get('CodeFormer')(dim_embd=512, codebook_size=1024, n_head=8, n_layers=9, connect_list=['32', '64', '128', '256']).to(CODEFORMER_DEVICE)

    ckpt_path = os.path.join(script_dir, 'CodeFormer/CodeFormer/weights/CodeFormer/codeformer.pth')
    logger.info(f'Loading CodeFormer model: {ckpt_path}')
    codeformer_checkpoint = torch.load(ckpt_path)['params_ema']
    CODEFORMER_NET.load_state_dict(codeformer_checkpoint)
    CODEFORMER_NET.eval()

    logger.info('Starting RunPod Serverless...')
    runpod.serverless.start({ 'handler': handler })
