# Fivoria AI Training Docker Image
# Supports distributed training with PyTorch and CUDA

FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    curl \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip

# Install PyTorch with CUDA support
RUN pip3 install --no-cache-dir \
    torch==2.1.0 \
    torchvision==0.16.0 \
    torchaudio==2.1.0 \
    --index-url https://download.pytorch.org/whl/cu121

# Install additional ML libraries
RUN pip3 install --no-cache-dir \
    numpy==1.24.3 \
    scipy==1.11.4 \
    scikit-learn==1.3.2 \
    pandas==2.1.3 \
    tqdm==4.66.1 \
    tensorboard==2.15.1 \
    wandb==0.16.1 \
    transformers==4.35.2 \
    datasets==2.15.0 \
    tokenizers==0.15.0 \
    accelerate==0.25.0 \
    deepspeed==0.12.6

# Install distributed training libraries
RUN pip3 install --no-cache-dir \
    apex==0.1.0 \
    flash-attn==2.3.3

# Set working directory
WORKDIR /workspace

# Copy Fivoria AI platform
COPY fivoria-ai-platform /workspace/fivoria-ai-platform

# Install Fivoria AI platform
RUN cd /workspace/fivoria-ai-platform && \
    pip3 install -e .

# Create directories for checkpoints and data
RUN mkdir -p /workspace/checkpoints
RUN mkdir -p /workspace/data
RUN mkdir -p /workspace/logs

# Expose port for monitoring
EXPOSE 6006  # TensorBoard

# Default command
CMD ["python3", "-m", "fivoria_ai.training.train"]
