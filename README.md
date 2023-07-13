# Inswapper | RunPod Serverless Worker

This is the source code for a [RunPod](https://runpod.io?ref=w18gds2n)
worker that uses [inswapper](
https://huggingface.co/deepinsight/inswapper/tree/main) for face
swapping AI tasks.

## Model

The worker uses the [inswapper_128.onnx](
https://huggingface.co/deepinsight/inswapper/resolve/main/inswapper_128.onnx)
model by [InsightFace](https://insightface.ai/).

## Building the Worker

#### Note: This worker requires a RunPod Network Volume with inswapper preinstalled in order to function correctly.

### Network Volume

1. [Create a RunPod Account](https://runpod.io?ref=w18gds2n).
2. Create a [RunPod Network Volume](https://www.runpod.io/console/user/storage).
3. Attach the Network Volume to a Secure Cloud [GPU pod](https://www.runpod.io/console/gpu-secure-cloud).
4. Select a light-weight template such as RunPod Pytorch.
5. Deploy the GPU Cloud pod.
6. Once the pod is up, open a Terminal and install the required dependencies:
```bash
cd /workspace
git clone https://github.com/ashleykleynhans/runpod-worker-inswapper.git
cd runpod-worker-inswapper
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
mkdir checkpoints
wget -O ./checkpoints/inswapper_128.onnx https://huggingface.co/deepinsight/inswapper/resolve/main/inswapper_128.onnx
apt update
apt -y install git-lfs
git lfs install
git clone https://huggingface.co/spaces/sczhou/CodeFormer
```
7. Edit the `create_test_json.py` file and ensure that you set `SOURCE_IMAGE` to
   a valid image to upscale (you can upload the image to your pod using
   [runpodctl](https://github.com/runpod/runpodctl/releases)).
8. Create the `test_input.json` file by running the `create_test_json.py` script:
```bash
python3 create_test_json.py
```
9. Run an inference on the `test_input.json` input so that the models can be cached on
   your Network Volume, which will dramatically reduce cold start times for RunPod Serverless:
```bash
python3 -u rp_handler.py
```

### Dockerfile

The worker is built using a Dockerfile. The Dockerfile specifies the
base image, environment variables, and system package dependencies

## Running the Worker

The worker can be run using the `start.sh` script. This script starts the
init system and runs the serverless handler script.

## API

The worker provides an API for inference. The API payload looks like this:

```json
{
  "input": {
    "source_image": "base64 encoded source image content",
    "target_image": "base64 encoded target image content",
  }
}
```

## Serverless Handler

The serverless handler (`rp_handler.py`) is a Python script that handles
inference requests.  It defines a function handler(event) that takes an
inference request, runs the inference using the [inswapper](
https://huggingface.co/deepinsight/inswapper/tree/main) model (and
CodeFormer where applicable), and returns the output as a JSON response in
the following format:

```json
{
  "output": {
    "status": "ok",
    "image": "base64 encoded output image"
  }
}
```
