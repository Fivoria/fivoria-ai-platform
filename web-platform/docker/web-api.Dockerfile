# Fivoria Web API Dockerfile
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

# Copy web API service
COPY web-platform/services/web-api/ ./services/web-api/
COPY web-platform/frontend/src/lib/api-client.ts ./services/web-api/

# Copy security and other shared modules
COPY security/ ./security/
COPY knowledge-layer/ ./knowledge-layer/
COPY integrations/ ./integrations/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/models

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "services.web-api.main:app", "--host", "0.0.0.0", "--port", "8000"]
