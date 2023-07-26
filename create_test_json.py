#!/usr/bin/env python3
import base64
import json

SOURCE_IMAGE = 'data/swap_src.jpeg'
TARGET_IMAGE = 'data/swap_dest.jpeg'
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


if __name__ == '__main__':
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

    # Save the payload to a JSON file
    with open('test_input.json', 'w') as output_file:
        json.dump(payload, output_file)

    print('Payload saved to: test_input.json')

