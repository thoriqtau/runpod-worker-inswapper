#!/usr/bin/env python3
# Replace the first 2 faces from a source image containing 3 faces
# into all the faces in a target image containing 2 faces
import io
import uuid
import base64
import json
import requests
import time
from PIL import Image


SOURCE_IMAGE = '../../data/hp-3faces.jpeg'
TARGET_IMAGE = '../../data/swap_src.jpeg'
SOURCE_INDEXES = '-1'
TARGET_INDEXES = '-1'
BACKGROUND_ENHANCE = True
FACE_RESTORE = False
FACE_UPSAMPLE = True
UPSCALE = 1
CODEFORMER_FIDELITY = 0.5
OUTPUT_FORMAT = 'JPEG'


def encode_image_to_base64(image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        encoded_data = base64.b64encode(image_data).decode('utf-8')
        return encoded_data


def save_result_image(resp_json):
    img = Image.open(io.BytesIO(base64.b64decode(resp_json['output']['image'])))
    file_extension = 'jpeg' if OUTPUT_FORMAT == 'JPEG' else 'png'
    output_file = f'{uuid.uuid4()}.{file_extension}'

    with open(output_file, 'wb') as f:
        print(f'Saving image: {output_file}')
        img.save(f, format=OUTPUT_FORMAT)


if __name__ == '__main__':
    runpod_endpoint_base_url = f'http://127.0.0.1:8000'

    # Load the images and encode them to base64
    source_image_base64 = encode_image_to_base64(SOURCE_IMAGE)
    target_image_base64 = encode_image_to_base64(TARGET_IMAGE)

    # Create the payload dictionary
    payload = {
        "input": {
            "source_image": source_image_base64,
            "target_image": target_image_base64,
            "source_indexes": SOURCE_INDEXES,
            "target_indexes": TARGET_INDEXES,
            "background_enhance": BACKGROUND_ENHANCE,
            "face_restore": FACE_RESTORE,
            "face_upsample": FACE_UPSAMPLE,
            "upscale": UPSCALE,
            "codeformer_fidelity": CODEFORMER_FIDELITY,
            "output_format": OUTPUT_FORMAT
        }
    }

    r = requests.post(
        f'{runpod_endpoint_base_url}/runsync',
        # headers={
        #     'Authorization': f'Bearer {runpod_api_key}'
        # },
        json=payload
    )

    print(f'Status code: {r.status_code}')

    if r.status_code == 200:
        resp_json = r.json()

        if 'output' in resp_json and 'image' in resp_json['output']:
            save_result_image(resp_json)
        else:
            job_status = resp_json['status']
            print(f'Job status: {job_status}')

            if job_status == 'IN_QUEUE' or job_status == 'IN_PROGRESS':
                request_id = resp_json['id']
                request_in_queue = True

                while request_in_queue:
                    r = requests.get(
                        f'{runpod_endpoint_base_url}/status/{request_id}',
                        # headers={
                        #     'Authorization': f'Bearer {runpod_api_key}'
                        # }
                    )

                    print(f'Status code from RunPod status endpoint: {r.status_code}')

                    if r.status_code == 200:
                        resp_json = r.json()
                        job_status = resp_json['status']

                        if job_status == 'IN_QUEUE' or job_status == 'IN_PROGRESS':
                            print(f'RunPod request {request_id} is {job_status}, sleeping for 5 seconds...')
                            time.sleep(5)
                        elif job_status == 'FAILED':
                            request_in_queue = False
                            print(f'RunPod request {request_id} failed')
                        elif job_status == 'COMPLETED':
                            request_in_queue = False
                            print(f'RunPod request {request_id} completed')
                            save_result_image(resp_json)
                        elif job_status == 'TIMED_OUT':
                            request_in_queue = False
                            print(f'ERROR: RunPod request {request_id} timed out')
                        else:
                            request_in_queue = False
                            print(f'ERROR: Invalid status response from RunPod status endpoint')
                            print(json.dumps(resp_json, indent=4, default=str))
            elif job_status == 'COMPLETED' and resp_json['output']['status'] == 'error':
                print(f'ERROR: {resp_json["output"]["message"]}')
            else:
                print(json.dumps(resp_json, indent=4, default=str))
    else:
        print(f'ERROR: {r.content}')
