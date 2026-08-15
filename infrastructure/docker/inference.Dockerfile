# Fivoria AI Inference Docker Image
# Optimized for model serving with vLLM

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

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
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip

# Install PyTorch with CUDA support (runtime only)
RUN pip3 install --no-cache-dir \
    torch==2.1.0 \
    torchvision==0.16.0 \
    --index-url https://download.pytorch.org/whl/cu121

# Install vLLM for optimized inference
RUN pip3 install --no-cache-dir \
    vllm==0.2.6 \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    transformers==4.35.2 \
    tokenizers==0.15.0

# Install monitoring
RUN pip3 install --no-cache-dir \
    prometheus-client==0.19.0

# Set working directory
WORKDIR /workspace

# Copy Fivoria AI platform
COPY fivoria-ai-platform /workspace/fivoria-ai-platform

# Install Fivoria AI platform
RUN cd /workspace/fivoria-ai-platform && \
    pip3 install -e .

# Create directories for models and logs
RUN mkdir -p /workspace/models
RUN mkdir -p /workspace/logs

# Expose ports
EXPOSE 8000  # API
EXPOSE 6006  # Metrics

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python3", "-m", "fivoria_ai.inference.server"]
