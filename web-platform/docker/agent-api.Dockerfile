# Fivoria Agent API Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent API service
COPY web-platform/services/agent-api/ ./services/agent-api/

# Copy knowledge layer and other shared modules
COPY knowledge-layer/ ./knowledge-layer/
COPY model-platform/ ./model-platform/
COPY data-platform/ ./data-platform/
COPY security/ ./security/
COPY integrations/ ./integrations/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/models /app/checkpoints

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "services.agent-api.main:app", "--host", "0.0.0.0", "--port", "8001"]
