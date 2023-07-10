#!/usr/bin/env python3
import io
import uuid
import base64
import json
import requests
from PIL import Image

RUNPOD_API_KEY = 'INSERT_API_KEY_HERE'
SERVERLESS_API_ID = 'INSERT_API_ID_HERE'
RUNPOD_ENDPOINT_URL = f'https://api.runpod.ai/v2/{SERVERLESS_API_ID}/runsync'
SOURCE_IMAGE = '/Users/ashley/src/inswapper/data/src.jpg'
TARGET_IMAGE = '/Users/ashley/src/inswapper/data/target.jpg'


def encode_image_to_base64(image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        encoded_data = base64.b64encode(image_data).decode('utf-8')
        return encoded_data


if __name__ == '__main__':
    # Load the images and encode them to base64
    source_image_base64 = encode_image_to_base64(SOURCE_IMAGE)
    target_image_base64 = encode_image_to_base64(TARGET_IMAGE)

    # Create the payload dictionary
    payload = {
        "input": {
            "source_image": source_image_base64,
            "target_image": target_image_base64
        }
    }

    r = requests.post(
        RUNPOD_ENDPOINT_URL,
        headers={

        },
        json=payload
    )

    print(f'Status code: {r.status_code}')

    if r.status_code == 200:
        print(json.dump(r.json(), indent=4, default=str))

        img = Image.open(io.BytesIO(base64.b64decode(resp_json['image'])))
        output_file = f'{uuid.uuid4()}.jpg'

        with open(output_file, 'wb') as f:
            print(f'Saving image: {output_file}')
            img.save(f, format='JPEG')
    else:
        print(f'ERROR: {r.content}')