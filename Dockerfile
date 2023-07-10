FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_PREFER_BINARY=1 \
    PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Upgrade apt packages and install required dependencies
RUN apt update && \
    apt upgrade -y && \
    apt install -y \
      python3-dev \
      fonts-dejavu-core \
      rsync \
      git \
      jq \
      moreutils \
      aria2 \
      wget \
      curl \
      libglib2.0-0 \
      libsm6 \
      libgl1 \
      libxrender1 \
      libxext6 \
      ffmpeg \
      libgoogle-perftools-dev \
      procps && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean -y

# Set Python and pip
RUN ln -s /usr/bin/python3.10 /usr/bin/python && \
    curl https://bootstrap.pypa.io/get-pip.py | python && \
    rm -f get-pip.py

# Install Torch
RUN --mount=type=cache,target=/cache --mount=type=cache,target=/root/.cache/pip \
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install additional Python dependencies for RunPod worker
COPY requirements.txt /requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --upgrade pip && \
    pip3 install --upgrade -r /requirements.txt --no-cache-dir && \
    rm /requirements.txt && \
    pip3 cache purge

# Add RunPod Handler and Docker container start script
ADD rp_handler.py start.sh ./

# Start the container
RUN chmod +x /start.sh
CMD /start.sh
