# roop inswapper | RunPod Serverless Worker

This is the source code for a [RunPod](https://runpod.io?ref=2xxro4sy)
Serverless worker that uses roop ([inswapper](
https://huggingface.co/deepinsight/inswapper/tree/main)) for face
swapping AI tasks.

## Model

The worker uses the [inswapper_128.onnx](
https://huggingface.co/deepinsight/inswapper/resolve/main/inswapper_128.onnx)
model by [InsightFace](https://insightface.ai/).

## Local Testing (not required if you don't want to test locally)

### Clone the repo, create a venv and install the requirements

```bash
git clone https://github.com/ashleykleynhans/runpod-worker-inswapper.git
cd runpod-worker-inswapper
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Start the local RunPod Handler API

Use `--rp_serve_api` command line argument to serve the API locally.

```bash
python3 -u rp_handler.py --rp_serve_api
```

**NOTE:** You need to keep the RunPod Handler API running in order to
run the tests, so open a new terminal window to run the tests. 

### Set your test data files

You can either overwrite the `data/src.png` and `data/target.png` image
files with your own source and target files, or alternatively, you can
edit the`tests/test_local_endpoint.py` to reference the source and
target images somewhere else on your system.

### Run a local test

1. Ensure that the RunPod Handler API is still running.
2. Go the directory containing this worker code, activate the venv,
   change directory to the `tests` directory and run the
   `test_local_endpoint.py` script.
```bash
cd runpod-worker-inswapper
source venv/bin/activate
cd tests
python3 test_local_endpoint.py
```
3. This will display the HTTP status code and the filename
   of the output image, for example:
```
Status code: 200
Saving image: 792a7e9f-9c36-4d35-b408-0d45d8e2bbcb.jpg
```

You can then open the output image (in this case
`792a7e9f-9c36-4d35-b408-0d45d8e2bbcb.jpg`) to view the
results of the face swap.

## Building the Worker

### Option 1: Network Volume

This will store your application on a Runpod Network Volume and
build a light weight Docker image that runs everything
from the Network volume without installing the application
inside the Docker image.

1. [Create a RunPod Account](https://runpod.io?ref=2xxro4sy).
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
10. Sign up for a Docker hub account if you don't already have one.
11. Build the Docker image and push to Docker hub:
```bash
docker build -t dockerhub-username/runpod-worker-inswapper:1.0.0 -f Dockerfile.Network_Volume .
docker login
docker push dockerhub-username/runpod-worker-inswapper:1.0.0
```

### Option 2: Standalone

This is the simpler option.  No network volume is required.
The entire application will be stored within the Docker image
but will obviously create a more bulky Docker image as a result.

```bash
docker build -t dockerhub-username/runpod-worker-inswapper:1.0.0 -f Dockerfile.Standalone .
docker login
docker push dockerhub-username/runpod-worker-inswapper:1.0.0
```

## Dockerfile

There are 2 different Dockerfile configurations

1. Network_Volume - See Option 1 Above.
2. Standalone - See Option 2 Above (No Network Volume is required for this option).

The worker is built using one of the two Dockerfile configurations
depending on your specific requirements.

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

## Testing your RunPod Endpoint

### Configure your RunPod Credentials

1. Copy the `.env.example` file to `.env`:
```bash
cd tests
cp .env.example .env
```
2. Edit the `.env` file and add your RunPod API key to
`RUNPOD_API_KEY` and your RunPod Endpoint ID to
`RUNPOD_ENDPOINT_ID`.
3. Run the test script:
```bash
python3 test_runpod_endpoint.py
```
4. This will display the HTTP status code and the filename
   of the output image, for example:
```
Status code: 200
Saving image: 792a7e9f-9c36-4d35-b408-0d45d8e2bbcb.jpg
```

You can then open the output image (in this case
`792a7e9f-9c36-4d35-b408-0d45d8e2bbcb.jpg`) to view the
results of the face swap.

## Acknowledgements

- [Inswapper](https://github.com/haofanwang/inswapper)
- [Roop](https://github.com/s0md3v/roop)
- [Insightface](https://github.com/deepinsight)
- [CodeFormer](https://huggingface.co/spaces/sczhou/CodeFormer)
- [Real-ESRGAN (ai-forever)](https://github.com/ai-forever/Real-ESRGAN)
- [Generative Labs YouTube Tutorials](https://www.youtube.com/@generativelabs)

## Additional Resources

- [Generative Labs YouTube Tutorials](https://www.youtube.com/@generativelabs)
- [Getting Started With RunPod Serverless](https://trapdoor.cloud/getting-started-with-runpod-serverless/)
- [Serverless | Create a Custom Basic API](https://blog.runpod.io/serverless-create-a-basic-api/)

## Community and Contributing

Pull requests and issues on [GitHub](https://github.com/ashleykleynhans/runpod-worker-inswapper)
are welcome. Bug fixes and new features are encouraged.

You can contact me and get help with deploying your Serverless
worker to RunPod on the RunPod Discord Server below,
my username is **ashleyk**.

<a target="_blank" href="https://discord.gg/pJ3P2DbUUq">![Discord Banner 2](https://discordapp.com/api/guilds/912829806415085598/widget.png?style=banner2)</a>

## Appreciate my work?

<a href="https://www.buymeacoffee.com/ashleyk" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
