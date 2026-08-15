# Fivoria AI Deployment Guide

## Overview

This guide covers deploying the Fivoria AI platform, including model serving, inference gateway, and infrastructure setup.

## Architecture

```
USER
    ↓
AI GATEWAY
    ↓
MODEL ROUTER
    ↓
INFERENCE SERVERS
    ↓
MODEL WEIGHTS
    ↓
GPU CLUSTER
```

## Prerequisites

### Hardware Requirements

**Inference (100B Model)**:
- GPU: 8x A100 80GB (for tensor parallel inference)
- CPU: 64 cores
- RAM: 512GB
- Storage: 2TB NVMe
- Network: 25Gbps+

**Inference (7B Model)**:
- GPU: 1-2x A100 40GB
- CPU: 16 cores
- RAM: 128GB
- Storage: 500GB NVMe

### Software Requirements

- Docker
- Kubernetes (for production)
- NVIDIA Driver 525+
- CUDA 11.8+
- Python 3.10+

## Deployment Methods

### 1. Docker Deployment

#### Build Inference Dockerfile

```bash
cd infrastructure/docker
docker build -f inference.Dockerfile -t fivoria-inference:latest .
```

#### Run Inference Container

```bash
docker run -d \
  --gpus all \
  -p 8000:8000 \
  -v /path/to/model:/model \
  -v /path/to/data:/data \
  fivoria-inference:latest
```

### 2. Kubernetes Deployment

#### Deploy Inference Service

```bash
kubectl apply -f infrastructure/kubernetes/inference-deployment.yaml
```

#### Scale Deployment

```bash
kubectl scale deployment fivoria-inference --replicas=3
```

### 3. Local Deployment

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Start Inference Server

```bash
python -m inference.gateway --model-path ./checkpoints/model --port 8000
```

## Model Serving

### vLLM Serving

```python
from vllm import LLM, SamplingParams

llm = LLM(model="fivoria-ai/fivoria-100b", tensor_parallel_size=8)

sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=1000
)

outputs = llm.generate(["Hello, world!"], sampling_params)
```

### TensorRT-LLM Serving

```bash
# Convert model to TensorRT
trtllmbuild --model_dir ./model --output_dir ./trt_model

# Start TensorRT server
trtllmserve --model_dir ./trt_model --port 8000
```

### Custom Serving

```python
from inference.gateway import InferenceServer

server = InferenceServer(
    model_path="./checkpoints/model",
    device="cuda",
    tensor_parallel_size=8
)

server.start(host="0.0.0.0", port=8000)
```

## AI Gateway

### Configuration

```python
from inference.gateway import GatewayConfig

config = GatewayConfig(
    model_path="./checkpoints/model",
    host="0.0.0.0",
    port=8000,
    max_tokens=4096,
    temperature=0.7,
    rate_limit=100,
    auth_enabled=True
)
```

### Start Gateway

```bash
python -m inference.gateway --config config.yaml
```

### API Endpoints

#### Chat Completions

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "model": "fivoria-100b",
    "max_tokens": 100
  }'
```

#### Embeddings

```bash
curl -X POST http://localhost:8000/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "input": "Hello world",
    "model": "fivoria-100b"
  }'
```

## Model Quantization

### Quantize for Deployment

```python
from model_platform.quantization.quantization import QuantizationPipeline, Precision

pipeline = QuantizationPipeline()

# Convert to INT8
quantized_model = pipeline.quantize_model(
    model,
    Precision.FP32,
    Precision.INT8,
    method="dynamic"
)

# Save quantized model
pipeline.save_quantized_model(quantized_model, Path("./models/int8"))
```

### Benchmark Quantized Model

```python
metrics = pipeline.benchmark_model(quantized_model, (1, 2048), "cuda")
print(f"Throughput: {metrics['throughput_samples_per_sec']}")
print(f"Memory: {metrics['memory_usage_gb']} GB")
```

## Scaling

### Horizontal Scaling

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fivoria-inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fivoria-inference
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Vertical Scaling

- Increase GPU memory per instance
- Use larger GPU models (A100 80GB → H100)
- Increase CPU and memory allocation

## Load Balancing

### Nginx Configuration

```nginx
upstream fivoria_backend {
    least_conn;
    server inference-1:8000;
    server inference-2:8000;
    server inference-3:8000;
}

server {
    listen 80;
    server_name api.fivoria.ai;

    location /v1/ {
        proxy_pass http://fivoria_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Kubernetes Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fivoria-inference
spec:
  selector:
    app: fivoria-inference
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

## Monitoring

### Prometheus Metrics

```python
from observability.metrics import MetricsSystem

metrics = MetricsSystem()
metrics.setup_prometheus(port=9090)
```

### Grafana Dashboard

- Request rate
- Latency percentiles
- GPU utilization
- Memory usage
- Error rate

## Security

### API Authentication

```python
from security.auth import AuthManager

auth = AuthManager()
api_key = auth.generate_api_key(user_id="user-001")
```

### Rate Limiting

```python
from inference.gateway import RateLimiter

limiter = RateLimiter(max_requests=100, window=60)
```

### Network Security

- Use TLS/SSL
- Implement firewall rules
- Network policies in Kubernetes
- VPC isolation

## Backup and Recovery

### Model Backup

```bash
# Backup model weights
aws s3 sync ./checkpoints s3://fivoria-backups/checkpoints/
```

### Configuration Backup

```bash
# Backup configuration
kubectl get configmap fivoria-config -o yaml > backup-config.yaml
```

### Disaster Recovery

1. Restore from backup
2. Verify checksums
3. Test model loading
4. Start inference servers
5. Verify API endpoints

## Cost Optimization

### GPU Utilization

- Use batch inference
- Enable continuous batching.
- Optimize KV cache
- Use quantization

### Infrastructure Costs

- Use spot/preemptible instances
- Auto-scale based on demand
- Use reserved instances for baseline
- Optimize storage costs

## Troubleshooting

### High Latency

**Symptoms**: Slow response times

**Solutions**:
- Increase GPU count
- Enable tensor parallelism
- Use quantization
- Optimize batch size
- Check network latency

### Out of Memory

**Symptoms**: OOM errors

**Solutions**:
- Reduce batch size
- Use quantization
- Enable KV cache offloading
- Increase GPU memory
- Use gradient checkpointing

### Low Throughput

**Symptoms**: Low requests per second

**Solutions**:
- Increase instance count
- Optimize batching
- Use faster GPUs
- Enable continuous batching
- Check I/O bottlenecks

## Best Practices

### Model Versioning

- Use semantic versioning
- Tag model releases
- Maintain multiple versions
- Test before promotion
- Document changes

### A/B Testing

```python
# Deploy multiple model versions
version_a = deploy_model("fivoria-100b-v1.0")
version_b = deploy_model("fivoria-100b-v1.1")

# Route traffic
router.route(50% to version_a, 50% to version_b)
```

### Canary Deployments

```bash
# Deploy to single instance first
kubectl patch deployment fivoria-inference -p '{"spec":{"replicas":1}}'

# Monitor metrics
# If successful, scale up
kubectl scale deployment fivoria-inference --replicas=10
```

### Blue-Green Deployments

```bash
# Deploy new version to green environment
kubectl apply -f deployment-green.yaml

# Switch traffic
kubectl patch service fivoria-inference -p '{"spec":{"selector":{"version":"green"}}}'
```

## Maintenance

### Rolling Updates

```bash
# Update model without downtime
kubectl set image deployment/fivoria-inference \
  fivoria-inference=fivoria-inference:v2.0 \
  --record
```

### Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Performance Tuning

### Batch Size Optimization

```python
# Find optimal batch size
for batch_size in [1, 2, 4, 8, 16]:
    throughput = benchmark_batch_size(batch_size)
    print(f"Batch {batch_size}: {throughput} req/s")
```

### Sequence Length Optimization

```python
# Optimize for typical sequence lengths
typical_lengths = [128, 256, 512, 1024, 2048]
for length in typical_lengths:
    latency = benchmark_sequence_length(length)
    print(f"Length {length}: {latency}ms")
```

## References

- vLLM: https://github.com/vllm-project/vllm
- TensorRT-LLM: https://github.com/NVIDIA/TensorRT-LLM
- Kubernetes: https://kubernetes.io/
