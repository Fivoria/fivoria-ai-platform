"""
Distributed Training Module
Implements distributed training with Megatron Core integration
"""

import os
import torch
import torch.distributed as dist
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ParallelismType(Enum):
    """Types of parallelism"""
    DATA_PARALLEL = "data_parallel"
    TENSOR_PARALLEL = "tensor_parallel"
    PIPELINE_PARALLEL = "pipeline_parallel"
    CONTEXT_PARALLEL = "context_parallel"
    EXPERT_PARALLEL = "expert_parallel"  # For MoE


@dataclass
class DistributedConfig:
    """Configuration for distributed training"""
    world_size: int  # Total number of GPUs
    tensor_parallel_size: int = 1
    pipeline_parallel_size: int = 1
    data_parallel_size: int = 1
    context_parallel_size: int = 1
    expert_parallel_size: int = 1  # For MoE
    
    # Micro-batch and gradient accumulation
    micro_batch_size: int = 1
    global_batch_size: int = 32
    gradient_accumulation_steps: int = 4
    
    # Precision
    bf16: bool = True
    fp16: bool = False
    fp8: bool = False
    
    # Memory optimization
    gradient_checkpointing: bool = True
    activation_checkpointing: bool = True
    sequence_parallel: bool = True
    
    # Checkpointing
    checkpoint_interval: int = 1000
    checkpoint_path: str = "./checkpoints"
    
    # Communication
    nccl_backend: str = "nccl"
    
    def __post_init__(self):
        """Validate configuration"""
        # Validate parallelism sizes
        assert self.tensor_parallel_size * self.pipeline_parallel_size * self.data_parallel_size == self.world_size, \
            "Product of parallelism sizes must equal world_size"
        
        # Calculate gradient accumulation if not set
        if self.gradient_accumulation_steps == 0:
            self.gradient_accumulation_steps = self.global_batch_size // (self.micro_batch_size * self.data_parallel_size)


class DistributedManager:
    """Manages distributed training setup and coordination"""

    def __init__(self, config: DistributedConfig):
        self.config = config
        self.rank = 0
        self.local_rank = 0
        self.world_size = 1
        self.is_initialized = False

    def initialize(self):
        """Initialize distributed training"""
        if self.is_initialized:
            return
        
        # Get environment variables
        self.rank = int(os.environ.get("RANK", 0))
        self.local_rank = int(os.environ.get("LOCAL_RANK", 0))
        self.world_size = int(os.environ.get("WORLD_SIZE", 1))
        
        if self.world_size > 1:
            # Initialize process group
            dist.init_process_group(
                backend=self.config.nccl_backend,
                world_size=self.world_size,
                rank=self.rank
            )
            
            # Set device for this process
            torch.cuda.set_device(self.local_rank)
            
            logger.info(f"Initialized distributed training: rank={self.rank}, world_size={self.world_size}")
        
        self.is_initialized = True

    def cleanup(self):
        """Cleanup distributed training"""
        if self.is_initialized and self.world_size > 1:
            dist.destroy_process_group()
            self.is_initialized = False

    def barrier(self):
        """Synchronize all processes"""
        if self.is_initialized and self.world_size > 1:
            dist.barrier()

    def all_reduce(self, tensor: torch.Tensor, op=dist.ReduceOp.SUM) -> torch.Tensor:
        """All-reduce operation across all processes"""
        if self.is_initialized and self.world_size > 1:
            dist.all_reduce(tensor, op=op)
        return tensor

    def broadcast(self, tensor: torch.Tensor, src: int = 0) -> torch.Tensor:
        """Broadcast tensor from source process"""
        if self.is_initialized and self.world_size > 1:
            dist.broadcast(tensor, src=src)
        return tensor

    def get_model_parallel_group(self) -> Optional[dist.ProcessGroup]:
        """Get tensor parallel process group"""
        # Placeholder for Megatron Core integration
        # In actual implementation, this would create and return process groups
        return None

    def get_pipeline_parallel_group(self) -> Optional[dist.ProcessGroup]:
        """Get pipeline parallel process group"""
        # Placeholder for Megatron Core integration
        return None

    def get_data_parallel_group(self) -> Optional[dist.ProcessGroup]:
        """Get data parallel process group"""
        # Placeholder for Megatron Core integration
        return None


class MegatronCoreAdapter:
    """Adapter for Megatron Core distributed training"""

    def __init__(self, config: DistributedConfig):
        self.config = config
        self.megatron_available = self._check_megatron_available()
        self.manager = DistributedManager(config)

    def _check_megatron_available(self) -> bool:
        """Check if Megatron Core is available"""
        try:
            import megatron
            import megatron.core
            return True
        except ImportError:
            logger.warning("Megatron Core not available. Using PyTorch distributed.")
            return False

    def initialize(self):
        """Initialize distributed training with Megatron Core"""
        self.manager.initialize()

        if self.megatron_available:
            self._initialize_megatron()
        else:
            self._initialize_pytorch_distributed()

    def _initialize_megatron(self):
        """Initialize Megatron Core distributed training"""
        try:
            from megatron.core import tensor_parallel, pipeline_parallel
            from megatron.core import parallel_state
            
            # Initialize tensor parallel
            if self.config.tensor_parallel_size > 1:
                tensor_parallel.initialize_model_parallel(
                    tensor_model_parallel_size=self.config.tensor_parallel_size
                )
            
            # Initialize pipeline parallel
            if self.config.pipeline_parallel_size > 1:
                pipeline_parallel.initialize_model_parallel(
                    pipeline_model_parallel_size=self.config.pipeline_parallel_size
                )
            
            logger.info("Megatron Core distributed training initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Megatron Core: {e}")
            raise

    def _initialize_pytorch_distributed(self):
        """Initialize PyTorch distributed training (fallback)"""
        logger.info("Using PyTorch distributed training")

    def get_model_parallel_rank(self) -> int:
        """Get tensor parallel rank"""
        if self.megatron_available:
            try:
                from megatron.core import parallel_state
                return parallel_state.get_tensor_model_parallel_rank()
            except:
                pass
        return 0

    def get_model_parallel_world_size(self) -> int:
        """Get tensor parallel world size"""
        if self.megatron_available:
            try:
                from megatron.core import parallel_state
                return parallel_state.get_tensor_model_parallel_world_size()
            except:
                pass
        return 1

    def get_pipeline_parallel_rank(self) -> int:
        """Get pipeline parallel rank"""
        if self.megatron_available:
            try:
                from megatron.core import parallel_state
                return parallel_state.get_pipeline_model_parallel_rank()
            except:
                pass
        return 0

    def get_data_parallel_rank(self) -> int:
        """Get data parallel rank"""
        return self.manager.rank

    def get_data_parallel_world_size(self) -> int:
        """Get data parallel world size"""
        return self.manager.world_size

    def all_reduce_tensor(self, tensor: torch.Tensor) -> torch.Tensor:
        """All-reduce tensor across tensor parallel group"""
        if self.megatron_available:
            try:
                from megatron.core import tensor_parallel
                return tensor_parallel.all_reduce(tensor)
            except:
                pass
        return self.manager.all_reduce(tensor)

    def cleanup(self):
        """Cleanup distributed training"""
        if self.megatron_available:
            try:
                from megatron.core import tensor_parallel, pipeline_parallel
                tensor_parallel.destroy_model_parallel()
                pipeline_parallel.destroy_model_parallel()
            except:
                pass
        self.manager.cleanup()


class DistributedTrainer:
    """Distributed trainer with Megatron Core integration"""

    def __init__(
        self,
        model: torch.nn.Module,
        config: DistributedConfig,
        optimizer: torch.optim.Optimizer,
        scheduler: Any,
        device: str = "cuda"
    ):
        self.model = model
        self.config = config
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.device = device
        
        self.megatron_adapter = MegatronCoreAdapter(config)
        self.megatron_adapter.initialize()
        
        # Move model to device
        self.model = self.model.to(device)
        
        # Wrap model with distributed wrappers if needed
        self.model = self._wrap_model()

    def _wrap_model(self) -> torch.nn.Module:
        """Wrap model with distributed wrappers"""
        if self.config.tensor_parallel_size > 1 and self.megatron_adapter.megatron_available:
            # Use Megatron Core tensor parallel wrapper
            try:
                from megatron.core import tensor_parallel
                # Placeholder for actual Megatron wrapping
                logger.info("Model wrapped with Megatron tensor parallel")
            except Exception as e:
                logger.error(f"Failed to wrap model with Megatron: {e}")
        
        elif self.config.data_parallel_size > 1 and self.megatron_adapter.world_size > 1:
            # Use PyTorch DDP
            self.model = torch.nn.parallel.DistributedDataParallel(
                self.model,
                device_ids=[self.megatron_adapter.manager.local_rank]
            )
            logger.info("Model wrapped with DDP")
        
        return self.model

    def train_step(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Single training step with distributed support"""
        self.model.train()
        
        # Forward pass
        outputs = self.model(**batch)
        loss = outputs.get('loss', outputs)
        
        # Scale loss for gradient accumulation
        loss = loss / self.config.gradient_accumulation_steps
        
        # Backward pass
        loss.backward()
        
        # Gradient synchronization
        if self.config.data_parallel_size > 1:
            # All-reduce gradients
            for param in self.model.parameters():
                if param.grad is not None:
                    self.megatron_adapter.manager.all_reduce(param.grad)
                    param.grad.div_(self.megatron_adapter.manager.world_size)
        
        # Update weights
        if (self.optimizer.step_count() + 1) % self.config.gradient_accumulation_steps == 0:
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(),
                max_norm=1.0
            )
            
            # Optimizer step
            self.optimizer.step()
            self.scheduler.step()
            self.optimizer.zero_grad()
        
        return {
            'loss': loss.item() * self.config.gradient_accumulation_steps,
            'learning_rate': self.scheduler.get_last_lr()[0]
        }

    def save_checkpoint(self, step: int, checkpoint_path: Path):
        """Save distributed checkpoint"""
        self.megatron_adapter.manager.barrier()
        
        if self.megatron_adapter.manager.rank == 0:
            checkpoint = {
                'step': step,
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'scheduler_state_dict': self.scheduler.state_dict(),
                'config': self.config.__dict__
            }
            
            checkpoint_file = checkpoint_path / f"checkpoint_step_{step}.pt"
            checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            torch.save(checkpoint, checkpoint_file)
            logger.info(f"Saved checkpoint to {checkpoint_file}")

    def load_checkpoint(self, checkpoint_path: Path):
        """Load distributed checkpoint"""
        checkpoint_file = checkpoint_path / "checkpoint_step_latest.pt"
        
        if checkpoint_file.exists():
            checkpoint = torch.load(checkpoint_file, map_location=self.device)
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
            
            logger.info(f"Loaded checkpoint from {checkpoint_file}, step {checkpoint['step']}")
            return checkpoint['step']
        
        return 0

    def cleanup(self):
        """Cleanup distributed training"""
        self.megatron_adapter.cleanup()


def create_distributed_config(
    world_size: int,
    tensor_parallel: int = 1,
    pipeline_parallel: int = 1,
    micro_batch_size: int = 1,
    global_batch_size: int = 32,
    **kwargs
) -> DistributedConfig:
    """Create distributed configuration"""
    data_parallel = world_size // (tensor_parallel * pipeline_parallel)
    
    return DistributedConfig(
        world_size=world_size,
        tensor_parallel_size=tensor_parallel,
        pipeline_parallel_size=pipeline_parallel,
        data_parallel_size=data_parallel,
        micro_batch_size=micro_batch_size,
        global_batch_size=global_batch_size,
        **kwargs
    )


def main():
    """Example usage"""
    config = create_distributed_config(
        world_size=8,
        tensor_parallel=2,
        pipeline_parallel=2,
        micro_batch_size=2,
        global_batch_size=64
    )
    
    adapter = MegatronCoreAdapter(config)
    adapter.initialize()
    
    print(f"Tensor parallel rank: {adapter.get_model_parallel_rank()}")
    print(f"Data parallel rank: {adapter.get_data_parallel_rank()}")
    
    adapter.cleanup()


if __name__ == "__main__":
    main()
