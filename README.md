# Inswapper | RunPod Worker

This is the source code for a RunPod worker that uses 
[inswapper](https://huggingface.co/deepinsight/inswapper/tree/main) for
face swapping AI tasks.

## Model

The worker uses the [inswapper_128.onnx](
https://huggingface.co/deepinsight/inswapper/resolve/main/inswapper_128.onnx)
model by [InsightFace](https://insightface.ai/).

## Building the Worker

The worker is built using a Dockerfile. The Dockerfile specifies the
base image, environment variables, system package dependencies,
Python dependencies, and the steps to install and setup the inswapper
and CodeFormer models.

The Python dependencies are specified in requirements.txt.
The primary dependency is `runpod==0.10.0`.

## Running the Worker

The worker can be run using the start.sh script. This script starts the
init system and runs the serverless handler script.

## API

The worker provides an API for inference.

## Serverless Handler

The serverless handler (`rp_handler.py`) is a Python script that handles
inference requests.  It defines a function handler(event) that takes an
inference request, runs the inference using the inswapper model (and
CodeFormer where applicable), and returns the output.
