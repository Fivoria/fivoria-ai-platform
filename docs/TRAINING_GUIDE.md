# Fivoria AI Training Guide

## Overview

This guide covers training Fivoria's foundation model from random initialization to a production-ready 100B+ parameter model.

## Prerequisites

### Hardware Requirements

**For 100B Model Training**:
- GPU Cluster: 64+ A100 80GB GPUs
- CPU: 512+ cores
- RAM: 2TB+
- Storage: 100TB+ NVMe
- Network: 100Gbps+ InfiniBand

**For Development (1B Model)**:
- GPU: 4-8 A100 40GB GPUs
- CPU: 64 cores
- RAM: 256GB
- Storage: 10TB NVMe

### Software Requirements

- Python 3.10+
- PyTorch 2.0+
- CUDA 11.8+
- NCCL 2.17+
- Megatron Core (optional, for large-scale training)
- NeMo Framework (optional)

## Training Phases

### Phase 1: Small Model Validation (100M - 1B)

**Objective**: Validate architecture and training pipeline

**Steps**:
1. Initialize model with small config
2. Train on small dataset
3. Validate convergence
4. Test checkpoint recovery
5. Evaluate on benchmarks

**Expected Duration**: 1-3 days on 4 GPUs

### Phase 2: Medium Model (3B - 7B)

**Objective**: Scale validation

**Steps**:
1. Increase model size
2. Use distributed training
4. Optimize hyperparameters
5. Comprehensive evaluation

**Expected Duration**: 1-2 weeks on 8-16 GPUs

### Phase 3: Large Model (13B - 30B)

**Objective**: Infrastructure validation

**Steps**:
1. Enable tensor parallelism
2. Enable pipeline parallelism
3. Optimize memory usage
4. Test fault tolerance
5. Scale evaluation

**Expected Duration**: 2-4 weeks on 32-64 GPUs

### Phase 4: Production Model (70B - 100B+)

**Objective**: Production training

**Steps**:
1. Full distributed training
2. Continuous monitoring
3. Regular checkpointing
4. Comprehensive evaluation
5. Model deployment

**Expected Duration**: 2-6 months on 64-128 GPUs

## Configuration

### Model Configuration

```python
from model_platform.architecture.config import ModelConfig, ModelType

# 100B Model Configuration
config = ModelConfig(
    model_type=ModelType.DENSE,
    vocab_size=100000,
    max_position_embeddings=8192,
    hidden_size=12288,
    num_hidden_layers=80,
    num_attention_heads=96,
    num_key_value_heads=8,  # GQA
    intermediate_size=32768,
    hidden_act="swiglu",
    use_rope=True,
    use_gqa=True,
    use_flash_attention=True
)
```

### Training Configuration

```python
from model_platform.training.trainer import TrainingConfig

training_config = TrainingConfig(
    batch_size=32,
    micro_batch_size=1,
    gradient_accumulation_steps=32,
    learning_rate=1e-4,
    weight_decay=0.01,
    max_steps=1000000,
    warmup_steps=10000,
    checkpoint_interval=1000,
    eval_interval=5000
)
```

### Distributed Configuration

```python
from model_platform.training.distributed import create_distributed_config

dist_config = create_distributed_config(
    world_size=64,
    tensor_parallel=8,
    pipeline_parallel=2,
    micro_batch_size=1,
    global_batch_size=64,
    bf16=True,
    gradient_checkpointing=True
)
```

## Training Pipeline

### 1. Data Preparation

```python
from data_platform.registry.dataset_registry import DatasetRegistry

# Load dataset
registry = DatasetRegistry(Path("./data/registry"))
dataset = registry.get_dataset("fivoria-pretrain-v1")

# Tokenize
from data_platform.tokenization.tokenizer import FivoriaTokenizer

tokenizer = FivoriaTokenizer()
tokens = tokenizer.encode_batch(texts)
```

### 2. Model Initialization

```python
from model_platform.architecture.transformer import FivoriaTransformer

model = FivoriaTransformer(config)
model = model.to("cuda")

# Initialize weights
model.initialize_weights()
```

### 3. Distributed Training Setup

```python
from model_platform.training.distributed import MegatronCoreAdapter, DistributedTrainer

adapter = MegatronCoreAdapter(dist_config)
adapter.initialize()

trainer = DistributedTrainer(
    model=model,
    config=dist_config,
    optimizer=optimizer,
    scheduler=scheduler
)
```

### 4. Training Loop

```python
for step in range(max_steps):
    # Get batch
    batch = dataloader.get_batch()
    
    # Training step
    metrics = trainer.train_step(batch)
    
    # Log metrics
    logger.log_metrics(step, metrics)
    
    # Checkpoint
    if step % checkpoint_interval == 0:
        trainer.save_checkpoint(step, checkpoint_path)
    
    # Evaluate
    if step % eval_interval == 0:
        eval_metrics = evaluator.evaluate(model)
        logger.log_evaluation(eval_metrics)
```

## Checkpointing

### Checkpoint Structure

```
checkpoint_step_10000/
├── model_shard_00001.pt
├── model_shard_00002.pt
├── ...
├── optimizer_state.pt
├── scheduler_state.pt
├── rng_state.pt
├── config.json
└── metadata.json
```

### Checkpoint Management

```python
# Save checkpoint
trainer.save_checkpoint(step=10000, checkpoint_path=Path("./checkpoints"))

# Load checkpoint
trainer.load_checkpoint(checkpoint_path=Path("./checkpoints"))
```

### Recovery

```python
# Automatic recovery on failure
try:
    trainer.train()
except Exception as e:
    logger.error(f"Training failed: {e}")
    latest_checkpoint = find_latest_checkpoint()
    trainer.load_checkpoint(latest_checkpoint)
    trainer.train()
```

## Monitoring

### Metrics to Track

- Training loss
- Validation loss
- Learning rate
- Throughput (tokens/sec)
- GPU utilization
- GPU memory
- Gradient norms
- Checkpoint time

### Experiment Tracking

```python
from model_platform.experiments.experiment_tracking import MLflowTracker

tracker = MLflowTracker("./mlruns")
run = tracker.start_run("fivoria-100b-pretrain")

tracker.log_metric(run.run_id, "loss", loss_value, step=step)
tracker.log_parameter(run.run_id, "learning_rate", lr)
```

### Observability

```python
from observability.metrics import MetricsSystem

metrics = MetricsSystem()
metrics.record_training_loss(loss)
metrics.record_gpu_utilization(gpu_util)
metrics.record_throughput(tokens_per_sec)
```

## Evaluation

### Pre-training Evaluation

```python
from model_platform.evaluation.benchmarks import BenchmarkSuite

suite = BenchmarkSuite()
results = suite.evaluate(model, dataset="validation")
```

### Post-training Evaluation

```python
# SFT Evaluation
sft_results = suite.evaluate_sft(model, test_data)

# Preference Evaluation
pref_results = suite.evaluate_preference(model, test_data)

# Safety Evaluation
safety_results = suite.evaluate_safety(model, test_data)
```

## Post-Training

### Supervised Fine-Tuning (SFT)

```python
from model_platform.training.post_training import PostTrainingConfig, PostTrainingPipeline, PostTrainingType

config = PostTrainingConfig(
    training_type=PostTrainingType.SFT,
    model_path="./checkpoints/base_model",
    output_path="./checkpoints/sft_model",
    train_data_path="./data/sft_train.json",
    learning_rate=5e-5,
    batch_size=4
)

pipeline = PostTrainingPipeline(config)
pipeline.run(model)
```

### Preference Optimization (DPO)

```python
config = PostTrainingConfig(
    training_type=PostTrainingType.PREFERENCE,
    model_path="./checkpoints/sft_model",
    output_path="./checkpoints/dpo_model",
    train_data_path="./data/preference_data.json"
)

pipeline = PostTrainingPipeline(config)
pipeline.run(model)
```

### Safety Training

```python
config = PostTrainingConfig(
    training_type=PostTrainingType.SAFETY,
    model_path="./checkpoints/dpo_model",
    output_path="./checkpoints/safe_model",
    train_data_path="./data/safety_data.json"
)

pipeline = PostTrainingPipeline(config)
pipeline.run(model)
```

## Optimization

### Memory Optimization

- Gradient checkpointing
- Activation checkpointing
- Sequence parallelism
- Mixed precision (BF16/FP8)
- Optimized attention (Flash Attention)

### Throughput Optimization

- Gradient accumulation
- Overlapping compute/communication
- Optimized data loading
- Prefetching
- Mixed precision

### Scaling Optimization

- Tensor parallelism
- Pipeline parallelism
- Data parallelism
- Expert parallelism (for MoE)
- Context parallelism

## Troubleshooting

### Training Instability

**Symptoms**: Loss spikes, NaN values

**Solutions**:
- Reduce learning rate
- Enable gradient clipping
- Check data quality
- Increase warmup steps
- Use mixed precision

### Memory Issues

**Symptoms**: OOM errors

**Solutions**:
- Reduce batch size
- Enable gradient checkpointing
- Reduce sequence length
- Use tensor parallelism
- Use pipeline parallelism

### Slow Training

**Symptoms**: Low throughput

**Solutions**:
- Increase batch size
- Enable mixed precision
- Optimize data loading
- Use faster storage
- Check GPU utilization

### Poor Convergence

**Symptoms**: Loss not decreasing

**Solutions**:
- Adjust learning rate
- Check data quality
- Increase training steps
- Try different optimizer
- Review model architecture

## Best Practices

### Hyperparameter Tuning

- Start with proven baselines
- Tune learning rate first
- Use learning rate schedulers
- Monitor validation loss
- Use systematic search

### Data Management

- Use versioned datasets
- Track data provenance
- Validate data quality
- Monitor contamination
- Balance data mix

### Checkpoint Management

- Save frequently
- Verify checksums
- Keep multiple versions
- Test recovery
- Archive old checkpoints

### Safety

- Monitor training for anomalies
- Validate model outputs
- Test for safety violations
- Implement guardrails
- Human review

## Deployment

### Model Export

```python
from model_platform.quantization.quantization import QuantizationPipeline, Precision

pipeline = QuantizationPipeline()

# Convert to BF16
bf16_model = pipeline.convert_precision(model, Precision.BF16)

# Quantize to INT8
int8_model = pipeline.quantize_model(model, Precision.FP32, Precision.INT8)
```

### Model Serving

```python
from inference.gateway import start_server

start_server(
    model_path="./checkpoints/final_model",
    host="0.0.0.0",
    port=8000
)
```

## Cost Estimation

### Compute Cost

**100B Model Training**:
- GPU-hours: ~100,000 A100-hours
- Cost: ~$500,000 - $1,000,000
- Duration: 2-6 months

**1B Model Training**:
- GPU-hours: ~1,000 A100-hours
- Cost: ~$5,000 - $10,000
- Duration: 1-2 weeks

### Storage Cost

- Raw data: ~10TB
- Processed data: ~5TB
- Checkpoints: ~50TB
- Total: ~65TB

## References

- Megatron Core: https://github.com/NVIDIA/Megatron-LM
- NeMo Framework: https://github.com/NVIDIA/NeMo
- PyTorch: https://pytorch.org/
