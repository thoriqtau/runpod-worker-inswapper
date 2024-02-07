## Building the Worker with a Network Volume

This will store your application on a Runpod Network Volume and
build a light weight Docker image that runs everything
from the Network volume without installing the application
inside the Docker image.

1. [Create a RunPod Account](https://runpod.io?ref=2xxro4sy).
2. Create a [RunPod Network Volume](https://www.runpod.io/console/user/storage).
3. Attach the Network Volume to a Secure Cloud [GPU pod](https://www.runpod.io/console/gpu-secure-cloud).
4. Select a light-weight template such as RunPod Pytorch.
5. Deploy the GPU Cloud pod.
6. Once the pod is up, open a Terminal and install the required
   dependencies. This can either be done by using the installation
   script, or manually.

### Automatic Installation Script

You can run this automatic installation script which will
automatically install all of the dependencies that get installed
manually below, and then you don't need to follow any of the
manual instructions.

```bash
wget https://raw.githubusercontent.com/ashleykleynhans/runpod-worker-inswapper/main/scripts/install.sh
chmod +x install.sh
./install.sh
```

### Manual Installation

You only need to complete the steps below if you did not run the
automatic installation script above.

1. Install the Serverless Worker:
```bash
# Delete Inswapper Serverless Worker
rm -rf /workspace/runpod-worker-inswapper

# Delete venv
rm -rf /workspace/venv

# Clone Inswapper Serverless Worker repo to /workspace
cd /workspace
git clone https://github.com/ashleykleynhans/runpod-worker-inswapper.git
cd runpod-worker-inswapper

# Install Ubuntu updates
apt update
apt -y upgrade

# Create and activate venv
python3 -m venv /workspace/venv
source /workspace/venv/bin/activate

# Install Torch
pip3 install --no-cache-dir torch==2.2.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install Inswapper Serverless Worker Requirements
pip3 install -r requirements.txt
pip3 uninstall -y onnxruntime
pip3 install onnxruntime-gpu
```
2. Download the checkpoints:
```bash
mkdir checkpoints
wget -O ./checkpoints/inswapper_128.onnx https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128.onnx
apt -y install git-lfs
git lfs install
git clone https://huggingface.co/spaces/sczhou/CodeFormer
```
3. Edit the `create_test_json.py` file and ensure that you set `SOURCE_IMAGE` to
   a valid image to upscale (you can upload the image to your pod using
   [runpodctl](https://github.com/runpod/runpodctl/releases)).
4. Create the `test_input.json` file by running the `create_test_json.py` script:
```bash
python3 create_test_json.py
```
5. Run an inference on the `test_input.json` input so that the models can be cached on
   your Network Volume, which will dramatically reduce cold start times for RunPod Serverless:
```bash
python3 -u rp_handler.py
```
6. Create logs directory:
```bash
mkdir -p /workspace/logs
```

## Building the Docker Image

You can either build this Docker image yourself, your alternatively,
you can use my pre-built image:

```
ashleykza/runpod-worker-inswapper:1.4.4
```

1. Sign up for a Docker hub account if you don't already have one.
2. Build the Docker image and push to Docker hub:
```bash
docker build -t dockerhub-username/runpod-worker-inswapper:1.0.0 -f Dockerfile.Network_Volume .
docker login
docker push dockerhub-username/runpod-worker-inswapper:1.0.0
```
