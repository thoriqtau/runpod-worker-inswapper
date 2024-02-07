#!/usr/bin/env bash

TORCH_VERSION="2.2.0"

echo "Deleting Inswapper Serverless Worker"
rm -rf /workspace/runpod-worker-inswapper

echo "Deleting venv"
rm -rf /workspace/venv

echo "Cloning Inswapper Serverless Worker repo to /workspace"
cd /workspace
git clone https://github.com/ashleykleynhans/runpod-worker-inswapper.git
cd runpod-worker-inswapper

echo "Installing Ubuntu updates"
apt update
apt -y upgrade

echo "Creating and activating venv"
python3 -m venv /workspace/venv
source /workspace/venv/bin/activate

echo "Installing Torch"
pip3 install --no-cache-dir torch==${TORCH_VERSION} torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo "Installing Inswapper Serverless Worker"
pip3 install -r requirements.txt

echo "Downloading checkpoints"
mkdir checkpoints
wget -O ./checkpoints/inswapper_128.onnx https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128.onnx
apt -y install git-lfs
git lfs install
git clone https://huggingface.co/spaces/sczhou/CodeFormer

echo "Running handler using test_input.json to download remaining checkpoints"
python3 create_test_json.py
python3 -u rp_handler.py
