"""
Fivoria AI Training Engine
Supports distributed training with checkpointing and recovery
"""

import torch
import torch.nn as nn
import torch.distributed as dist
from torch.utils.data import DataLoader
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import json
import os

from ..architecture.config import ModelConfig
from ..architecture.transformer import FivoriaTransformer


@dataclass
class TrainingState:
    """Training state for checkpointing"""
    model_weights: Dict[str, torch.Tensor]
    optimizer_state: Dict[str, Any]
    scheduler_state: Dict[str, Any]
    rng_state: Dict[str, Any]
    training_step: int
    consumed_tokens: int
    loss: float
    timestamp: str
    git_commit: str
    config: Dict


class CheckpointManager:
    """
    Checkpoint management for training recovery
    """
    
    def __init__(self, checkpoint_dir: str, max_checkpoints: int = 5):
        self.checkpoint_dir = checkpoint_dir
        self.max_checkpoints = max_checkpoints
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    def save(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: Optional[torch.optim.lr_scheduler._LRScheduler],
        training_step: int,
        consumed_tokens: int,
        loss: float,
        config: ModelConfig,
    ):
        """
        Save training checkpoint
        
        Args:
            model: Model to save
            optimizer: Optimizer state
            scheduler: Learning rate scheduler state
            training_step: Current training step
            consumed_tokens: Total tokens consumed
            loss: Current loss
            config: Model configuration
        """
        checkpoint_path = os.path.join(self.checkpoint_dir, f"checkpoint-{training_step}")
        
        # Save model weights
        model_state = {k: v.cpu() for k, v in model.state_dict().items()}
        
        # Save RNG state
        rng_state = {
            "cpu": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        }
        
        # Create training state
        training_state = TrainingState(
            model_weights=model_state,
            optimizer_state=optimizer.state_dict(),
            scheduler_state=scheduler.state_dict() if scheduler else None,
            rng_state=rng_state,
            training_step=training_step,
            consumed_tokens=consumed_tokens,
            loss=loss,
            timestamp=datetime.utcnow().isoformat(),
            git_commit=self._get_git_commit(),
            config=config.to_dict(),
        )
        
        # Save checkpoint
        torch.save(training_state, checkpoint_path)
        
        # Save metadata
        metadata = {
            "step": training_step,
            "tokens": consumed_tokens,
            "loss": loss,
            "timestamp": datetime.utcnow().isoformat(),
        }
        with open(f"{checkpoint_path}.metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Clean old checkpoints
        self._cleanup_old_checkpoints()
        
        print(f"Checkpoint saved: {checkpoint_path}")
    
    def load(self, checkpoint_path: str, model: nn.Module, optimizer: torch.optim.Optimizer):
        """
        Load training checkpoint
        
        Args:
            checkpoint_path: Path to checkpoint
            model: Model to load weights into
            optimizer: Optimizer to load state into
        
        Returns:
            Training state
        """
        training_state = torch.load(checkpoint_path, map_location="cpu")
        
        # Load model weights
        model.load_state_dict(training_state.model_weights)
        
        # Load optimizer state
        optimizer.load_state_dict(training_state.optimizer_state)
        
        # Restore RNG state
        torch.set_rng_state(training_state.rng_state["cpu"])
        if training_state.rng_state["cuda"] is not None:
            torch.cuda.set_rng_state_all(training_state.rng_state["cuda"])
        
        print(f"Checkpoint loaded: {checkpoint_path}")
        print(f"  Step: {training_state.training_step}")
        print(f"  Tokens: {training_state.consumed_tokens:,}")
        print(f"  Loss: {training_state.loss}")
        
        return training_state
    
    def _cleanup_old_checkpoints(self):
        """Remove old checkpoints keeping only max_checkpoints"""
        checkpoints = []
        for file in os.listdir(self.checkpoint_dir):
            if file.startswith("checkpoint-") and not file.endswith(".metadata.json"):
                step = int(file.split("-")[1])
                path = os.path.join(self.checkpoint_dir, file)
                checkpoints.append((step, path))
        
        checkpoints.sort(key=lambda x: x[0], reverse=True)
        
        # Remove old checkpoints
        for step, path in checkpoints[self.max_checkpoints:]:
            os.remove(path)
            if os.path.exists(f"{path}.metadata.json"):
                os.remove(f"{path}.metadata.json")
    
    def _get_git_commit(self) -> str:
        """Get current git commit hash"""
        try:
            import subprocess
            return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        except:
            return "unknown"


class Trainer:
    """
    Training engine for Fivoria AI models
    """
    
    def __init__(
        self,
        model: FivoriaTransformer,
        optimizer: torch.optim.Optimizer,
        scheduler: Optional[torch.optim.lr_scheduler._LRScheduler],
        dataloader: DataLoader,
        config: ModelConfig,
        checkpoint_dir: str,
        log_interval: int = 100,
        checkpoint_interval: int = 1000,
    ):
        self.model = model
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.dataloader = dataloader
        self.config = config
        self.checkpoint_manager = CheckpointManager(checkpoint_dir)
        self.log_interval = log_interval
        self.checkpoint_interval = checkpoint_interval
        
        self.training_step = 0
        self.consumed_tokens = 0
        self.device = next(model.parameters()).device
    
    def train_step(self, batch: Dict[str, torch.Tensor]) -> float:
        """
        Single training step
        
        Args:
            batch: Training batch with input_ids and labels
        
        Returns:
            Loss value
        """
        self.model.train()
        
        # Move batch to device
        input_ids = batch["input_ids"].to(self.device)
        labels = batch["labels"].to(self.device)
        attention_mask = batch.get("attention_mask", None)
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.device)
        
        # Forward pass
        logits, _ = self.model(input_ids, attention_mask=attention_mask)
        
        # Calculate loss
        # Shift logits for next-token prediction
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()
        
        loss_fn = nn.CrossEntropyLoss(ignore_index=-100)
        loss = loss_fn(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
        
        # Backward pass
        loss.backward()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        
        # Optimizer step
        self.optimizer.step()
        self.optimizer.zero_grad()
        
        # Scheduler step
        if self.scheduler is not None:
            self.scheduler.step()
        
        # Track tokens
        batch_size, seq_len = input_ids.shape
        self.consumed_tokens += batch_size * seq_len
        
        return loss.item()
    
    def train(self, max_steps: int, resume_from: Optional[str] = None):
        """
        Main training loop
        
        Args:
            max_steps: Maximum training steps
            resume_from: Path to checkpoint to resume from
        """
        # Resume from checkpoint if specified
        if resume_from is not None:
            training_state = self.checkpoint_manager.load(resume_from, self.model, self.optimizer)
            self.training_step = training_state.training_step
            self.consumed_tokens = training_state.consumed_tokens
            print(f"Resumed from step {self.training_step}")
        
        # Training loop
        self.model.train()
        while self.training_step < max_steps:
            for batch in self.dataloader:
                if self.training_step >= max_steps:
                    break
                
                # Training step
                loss = self.train_step(batch)
                
                # Logging
                if self.training_step % self.log_interval == 0:
                    lr = self.optimizer.param_groups[0]["lr"]
                    print(f"Step {self.training_step}: Loss={loss:.4f}, LR={lr:.6f}, Tokens={self.consumed_tokens:,}")
                
                # Checkpointing
                if self.training_step % self.checkpoint_interval == 0:
                    self.checkpoint_manager.save(
                        self.model,
                        self.optimizer,
                        self.scheduler,
                        self.training_step,
                        self.consumed_tokens,
                        loss,
                        self.config,
                    )
                
                self.training_step += 1
        
        # Final checkpoint
        self.checkpoint_manager.save(
            self.model,
            self.optimizer,
            self.scheduler,
            self.training_step,
            self.consumed_tokens,
            loss,
            self.config,
        )
        
        print(f"Training completed at step {self.training_step}")


def create_optimizer(model: nn.Module, config: ModelConfig) -> torch.optim.Optimizer:
    """
    Create optimizer for training
    
    Args:
        model: Model to optimize
        config: Model configuration
    
    Returns:
        Optimizer
    """
    # Separate weight decay for different parameter types
    no_decay = ["bias", "layer_norm", "layernorm", "norm"]
    
    optimizer_grouped_parameters = [
        {
            "params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
            "weight_decay": 0.01,
        },
        {
            "params": [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)],
            "weight_decay": 0.0,
        },
    ]
    
    optimizer = torch.optim.AdamW(
        optimizer_grouped_parameters,
        lr=1e-4,
        betas=(0.9, 0.95),
        eps=1e-8,
    )
    
    return optimizer


def create_scheduler(optimizer: torch.optim.Optimizer, num_training_steps: int) -> torch.optim.lr_scheduler._LRScheduler:
    """
    Create learning rate scheduler
    
    Args:
        optimizer: Optimizer
        num_training_steps: Total training steps
    
    Returns:
        Learning rate scheduler
    """
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=num_training_steps,
        eta_min=1e-6,
    )
    
    return scheduler


if __name__ == "__main__":
    # Demo: Create a simple training setup
    from ..architecture.config import get_100M_config
    from torch.utils.data import Dataset
    
    config = get_100M_config()
    model = FivoriaTransformer(config)
    
    # Create dummy dataset
    class DummyDataset(Dataset):
        def __len__(self):
            return 1000
        
        def __getitem__(self, idx):
            return {
                "input_ids": torch.randint(0, config.vocab_size, (256,)),
                "labels": torch.randint(0, config.vocab_size, (256,)),
            }
    
    dataset = DummyDataset()
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)
    
    optimizer = create_optimizer(model, config)
    scheduler = create_scheduler(optimizer, num_training_steps=1000)
    
    trainer = Trainer(
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        dataloader=dataloader,
        config=config,
        checkpoint_dir="./checkpoints",
        log_interval=10,
        checkpoint_interval=100,
    )
    
    # Train for 100 steps
    trainer.train(max_steps=100)
