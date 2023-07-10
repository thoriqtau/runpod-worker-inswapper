import os
import io
import uuid
import base64
import copy
import cv2
import insightface
import numpy as np
from typing import List, Union
from PIL import Image
from werkzeug.utils import secure_filename
from restoration import *

TMP_PATH = '/tmp/inswapper'
script_dir = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------- #
# Application Functions                                                        #
# ---------------------------------------------------------------------------- #
def get_face_swap_model(model_path: str):
    model = insightface.model_zoo.get_model(model_path)
    return model


def get_face_analyser(model_path: str,
                      det_size=(320, 320)):
    face_analyser = insightface.app.FaceAnalysis(name="buffalo_l", root="./checkpoints")
    face_analyser.prepare(ctx_id=0, det_size=det_size)
    return face_analyser


def get_one_face(face_analyser,
                 frame:np.ndarray):
    face = face_analyser.get(frame)
    try:
        return min(face, key=lambda x: x.bbox[0])
    except ValueError:
        return None


def get_many_faces(face_analyser,
                   frame:np.ndarray):
    """
    get faces from left to right by order
    """
    try:
        face = face_analyser.get(frame)
        return sorted(face, key=lambda x: x.bbox[0])
    except IndexError:
        return None


def swap_face(face_swapper,
              source_face,
              target_face,
              temp_frame):
    """
    paste source_face on target image
    """
    return face_swapper.get(temp_frame, target_face, source_face, paste_back=True)


def process(source_img: Union[Image.Image, List],
            target_img: Image.Image,
            model: str):

    # load face_analyser
    face_analyser = get_face_analyser(model)

    # load face_swapper
    model_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), model)
    face_swapper = get_face_swap_model(model_path)

    # read target image
    target_img = cv2.cvtColor(np.array(target_img), cv2.COLOR_RGB2BGR)

    # detect faces that will be replaced in target_img
    target_faces = get_many_faces(face_analyser, target_img)
    if target_faces is not None:
        temp_frame = copy.deepcopy(target_img)
        if isinstance(source_img, list) and len(source_img) == len(target_faces):
            # replace faces in target image from the left to the right by order
            for i in range(len(target_faces)):
                target_face = target_faces[i]
                source_face = get_one_face(face_analyser, cv2.cvtColor(np.array(source_img[i]), cv2.COLOR_RGB2BGR))
                if source_face is None:
                    raise Exception("No source face found!")
                temp_frame = swap_face(face_swapper, source_face, target_face, temp_frame)
        else:
            # replace all faces in target image to same source_face
            source_img = cv2.cvtColor(np.array(source_img), cv2.COLOR_RGB2BGR)
            source_face = get_one_face(face_analyser, source_img)
            if source_face is None:
                raise Exception("No source face found!")
            for target_face in target_faces:
                temp_frame = swap_face(face_swapper, source_face, target_face, temp_frame)
        result = temp_frame
    else:
        print("No target faces found!")

    result_image = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    return result_image


def face_swap(src_img_path, target_img_path):
    source_img_paths = src_img_path.split(';')
    source_img = [Image.open(img_path) for img_path in source_img_paths]
    target_img = Image.open(target_img_path)

    # download from https://huggingface.co/deepinsight/inswapper/tree/main
    model = os.path.join(script_dir, 'checkpoints/inswapper_128.onnx')
    result_image = process(source_img, target_img, model)

    # make sure the ckpts downloaded successfully
    check_ckpts()

    # https://huggingface.co/spaces/sczhou/CodeFormer
    upsampler = set_realesrgan()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    codeformer_net = ARCH_REGISTRY.get('CodeFormer')(
        dim_embd=512,
        codebook_size=1024,
        n_head=8,
        n_layers=9,
        connect_list=['32', '64', '128', '256'],
    ).to(device)

    ckpt_path = os.path.join(script_dir, 'CodeFormer/CodeFormer/weights/CodeFormer/codeformer.pth')
    checkpoint = torch.load(ckpt_path)['params_ema']
    codeformer_net.load_state_dict(checkpoint)
    codeformer_net.eval()
    result_image = cv2.cvtColor(np.array(result_image), cv2.COLOR_RGB2BGR)

    background_enhance = True
    face_upsample = True
    upscale = 1
    codeformer_fidelity = 0.5

    result_image = face_restoration(
        result_image,
        background_enhance,
        face_upsample,
        upscale,
        codeformer_fidelity,
        upsampler,
        codeformer_net,
        device
    )

    result_image = Image.fromarray(result_image)
    output_buffer = io.BytesIO()
    result_image.save(output_buffer, format='JPEG')
    image_data = output_buffer.getvalue()

    return base64.b64encode(image_data).decode('utf-8')


def face_swap_api():
    if not os.path.exists(TMP_PATH):
        os.makedirs(TMP_PATH)

    # Get the source image file
    source_file = request.files['source_image']
    source_filename = secure_filename(source_file.filename)
    source_unique_id = uuid.uuid4()
    source_file_extension = os.path.splitext(source_filename)[1]
    source_image_path = f'{TMP_PATH}/{source_unique_id}{source_file_extension}'
    source_file.save(source_image_path)

    # Get the target image file
    target_file = request.files['target_image']
    target_filename = secure_filename(target_file.filename)
    target_unique_id = uuid.uuid4()
    target_file_extension = os.path.splitext(target_filename)[1]
    target_image_path = f'{TMP_PATH}/{target_unique_id}{target_file_extension}'
    target_file.save(target_image_path)

    try:
        result_image = face_swap(source_image_path, target_image_path)
    except Exception as e:
        raise Exception('Face swap failed')

    # Clean up temporary images
    os.remove(source_image_path)
    os.remove(target_image_path)

    return make_response(jsonify(
        {
            'status': 'ok',
            'image': result_image
        }
    ), 200)
# ---------------------------------------------------------------------------- #
# RunPod Handler                                                               #
# ---------------------------------------------------------------------------- #
def handler(event):
    '''
    This is the handler function that will be called by the serverless.
    '''

    return face_swap_api(event["input"])


if __name__ == "__main__":
    print("Starting RunPod Serverless...")
    runpod.serverless.start(
        {
            'handler': handler
        }
    )