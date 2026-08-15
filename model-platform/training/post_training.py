"""
Post-Training Module
Implements SFT, preference optimization, and safety training
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PostTrainingType(Enum):
    """Types of post-training"""
    SFT = "supervised_fine_tuning"
    PREFERENCE = "preference_optimization"
    SAFETY = "safety_training"
    REASONING = "reasoning_training"
    CODING = "coding_training"
    TOOL_USE = "tool_use_training"


@dataclass
class PostTrainingConfig:
    """Configuration for post-training"""
    training_type: PostTrainingType
    model_path: str
    output_path: str
    train_data_path: str
    eval_data_path: str
    
    # Training hyperparameters
    learning_rate: float = 5e-5
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    max_steps: int = 10000
    warmup_steps: int = 500
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    
    # LoRA configuration
    use_lora: bool = True
    lora_rank: int = 8
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    
    # Evaluation
    eval_steps: int = 500
    save_steps: int = 1000
    
    # Safety-specific
    safety_threshold: float = 0.5
    refusal_probability: float = 0.1


class SFTTrainer:
    """Supervised Fine-Tuning Trainer"""

    def __init__(self, model: nn.Module, config: PostTrainingConfig, device: str = "cuda"):
        self.model = model
        self.config = config
        self.device = device
        self.model = self.model.to(device)
        
        # Apply LoRA if configured
        if config.use_lora:
            self.model = self._apply_lora()

    def _apply_lora(self) -> nn.Module:
        """Apply LoRA to model"""
        try:
            from peft import LoraConfig, get_peft_model
            
            lora_config = LoraConfig(
                r=self.config.lora_rank,
                lora_alpha=self.config.lora_alpha,
                lora_dropout=self.config.lora_dropout,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                task_type="CAUSAL_LM"
            )
            
            model = get_peft_model(self.model, lora_config)
            logger.info("Applied LoRA to model")
            return model
        except ImportError:
            logger.warning("PEFT not available, training full model")
            return self.model

    def compute_loss(self, batch: Dict[str, torch.Tensor]) -> torch.Tensor:
        """Compute SFT loss"""
        input_ids = batch['input_ids'].to(self.device)
        attention_mask = batch['attention_mask'].to(self.device)
        labels = batch['labels'].to(self.device)
        
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        
        return outputs.loss

    def train_step(self, batch: Dict[str, torch.Tensor], optimizer: torch.optim.Optimizer) -> Dict[str, float]:
        """Single training step"""
        self.model.train()
        
        loss = self.compute_loss(batch)
        loss = loss / self.config.gradient_accumulation_steps
        loss.backward()
        
        if (optimizer.step_count() + 1) % self.config.gradient_accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
            optimizer.step()
            optimizer.zero_grad()
        
        return {'loss': loss.item() * self.config.gradient_accumulation_steps}


class PreferenceTrainer:
    """Preference Optimization Trainer (DPO)"""

    def __init__(self, model: nn.Module, ref_model: nn.Module, config: PostTrainingConfig, device: str = "cuda"):
        self.model = model
        self.ref_model = ref_model
        self.config = config
        self.device = device
        
        self.model = self.model.to(device)
        self.ref_model = self.ref_model.to(device)
        self.ref_model.eval()
        
        # Freeze reference model
        for param in self.ref_model.parameters():
            param.requires_grad = False

    def compute_dpo_loss(
        self,
        chosen_input_ids: torch.Tensor,
        chosen_attention_mask: torch.Tensor,
        rejected_input_ids: torch.Tensor,
        rejected_attention_mask: torch.Tensor,
        beta: float = 0.1
    ) -> torch.Tensor:
        """Compute DPO loss"""
        # Get log probabilities from policy model
        with torch.no_grad():
            chosen_ref_logps = self._get_log_probs(self.ref_model, chosen_input_ids, chosen_attention_mask)
            rejected_ref_logps = self._get_log_probs(self.ref_model, rejected_input_ids, rejected_attention_mask)
        
        chosen_logps = self._get_log_probs(self.model, chosen_input_ids, chosen_attention_mask)
        rejected_logps = self._get_log_probs(self.model, rejected_input_ids, rejected_attention_mask)
        
        # Compute DPO loss
        chosen_logratios = chosen_logps - chosen_ref_logps
        rejected_logratios = rejected_logps - rejected_ref_logps
        
        losses = -torch.logsigmoid(beta * (chosen_logratios - rejected_logratios))
        
        return losses.mean()

    def _get_log_probs(self, model: nn.Module, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """Get log probabilities from model"""
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        
        # Shift for next token prediction
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = input_ids[..., 1:].contiguous()
        
        # Compute log probabilities
        log_probs = torch.log_softmax(shift_logits, dim=-1)
        per_token_logps = torch.gather(log_probs, 2, shift_labels.unsqueeze(-1)).squeeze(-1)
        
        # Mask padding tokens
        mask = attention_mask[..., 1:].bool()
        per_token_logps = per_token_logps * mask
        
        # Sum over sequence
        return per_token_logps.sum(dim=-1)

    def train_step(self, batch: Dict[str, torch.Tensor], optimizer: torch.optim.Optimizer) -> Dict[str, float]:
        """Single training step"""
        self.model.train()
        
        loss = self.compute_dpo_loss(
            batch['chosen_input_ids'].to(self.device),
            batch['chosen_attention_mask'].to(self.device),
            batch['rejected_input_ids'].to(self.device),
            batch['rejected_attention_mask'].to(self.device)
        )
        
        loss = loss / self.config.gradient_accumulation_steps
        loss.backward()
        
        if (optimizer.step_count() + 1) % self.config.gradient_accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
            optimizer.step()
            optimizer.zero_grad()
        
        return {'loss': loss.item() * self.config.gradient_accumulation_steps}


class SafetyTrainer:
    """Safety Training Trainer"""

    def __init__(self, model: nn.Module, config: PostTrainingConfig, device: str = "cuda"):
        self.model = model
        self.config = config
        self.device = device
        self.model = self.model.to(device)

    def compute_safety_loss(
        self,
        safe_input_ids: torch.Tensor,
        safe_attention_mask: torch.Tensor,
        unsafe_input_ids: torch.Tensor,
        unsafe_attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """Compute safety loss"""
        # Get logits for safe and unsafe prompts
        safe_outputs = self.model(safe_input_ids.to(self.device), attention_mask=safe_attention_mask.to(self.device))
        unsafe_outputs = self.model(unsafe_input_ids.to(self.device), attention_mask=unsafe_attention_mask.to(self.device))
        
        # Compute refusal token probability (placeholder)
        # In production, this would use specific refusal tokens
        safe_logits = safe_outputs.logits
        unsafe_logits = unsafe_outputs.logits
        
        # Simple loss: maximize safe responses, minimize unsafe
        safe_loss = -safe_logits.mean()
        unsafe_loss = unsafe_logits.mean()
        
        return safe_loss + unsafe_loss * self.config.safety_threshold

    def train_step(self, batch: Dict[str, torch.Tensor], optimizer: torch.optim.Optimizer) -> Dict[str, float]:
        """Single training step"""
        self.model.train()
        
        loss = self.compute_safety_loss(
            batch['safe_input_ids'],
            batch['safe_attention_mask'],
            batch['unsafe_input_ids'],
            batch['unsafe_attention_mask']
        )
        
        loss = loss / self.config.gradient_accumulation_steps
        loss.backward()
        
        if (optimizer.step_count() + 1) % self.config.gradient_accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
            optimizer.step()
            optimizer.zero_grad()
        
        return {'loss': loss.item() * self.config.gradient_accumulation_steps}


class PostTrainingPipeline:
    """Complete post-training pipeline"""

    def __init__(self, config: PostTrainingConfig):
        self.config = config

    def run(self, model: nn.Module):
        """Run post-training pipeline"""
        logger.info(f"Starting {self.config.training_type.value} training")
        
        # Select trainer based on type
        if self.config.training_type == PostTrainingType.SFT:
            trainer = SFTTrainer(model, self.config)
        elif self.config.training_type == PostTrainingType.PREFERENCE:
            # Need reference model for preference training
            ref_model = self._load_reference_model()
            trainer = PreferenceTrainer(model, ref_model, self.config)
        elif self.config.training_type == PostTrainingType.SAFETY:
            trainer = SafetyTrainer(model, self.config)
        else:
            raise ValueError(f"Unsupported training type: {self.config.training_type}")
        
        # Create optimizer
        optimizer = torch.optim.AdamW(
            trainer.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )
        
        # Create scheduler
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=self.config.max_steps
        )
        
        # Training loop
        for step in range(self.config.max_steps):
            # Get batch (placeholder)
            batch = self._get_batch(step)
            
            # Training step
            metrics = trainer.train_step(batch, optimizer)
            
            # Scheduler step
            if (step + 1) % self.config.gradient_accumulation_steps == 0:
                scheduler.step()
            
            # Logging
            if step % 100 == 0:
                logger.info(f"Step {step}: {metrics}")
            
            # Save checkpoint
            if step % self.config.save_steps == 0 and step > 0:
                self._save_checkpoint(trainer.model, step)
        
        # Save final model
        self._save_model(trainer.model)
        logger.info("Post-training completed")

    def _load_reference_model(self) -> nn.Module:
        """Load reference model for preference training"""
        # Placeholder - would load from checkpoint
        logger.warning("Reference model loading not implemented")
        return None

    def _get_batch(self, step: int) -> Dict[str, torch.Tensor]:
        """Get training batch"""
        # Placeholder - would load from dataset
        return {
            'input_ids': torch.randint(0, 1000, (4, 128)),
            'attention_mask': torch.ones(4, 128),
            'labels': torch.randint(0, 1000, (4, 128))
        }

    def _save_checkpoint(self, model: nn.Module, step: int):
        """Save training checkpoint"""
        checkpoint_path = Path(self.config.output_path) / f"checkpoint_step_{step}"
        checkpoint_path.mkdir(parents=True, exist_ok=True)
        
        torch.save(model.state_dict(), checkpoint_path / "model.pt")
        logger.info(f"Saved checkpoint at step {step}")

    def _save_model(self, model: nn.Module):
        """Save final model"""
        output_path = Path(self.config.output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        torch.save(model.state_dict(), output_path / "final_model.pt")
        logger.info(f"Saved final model to {output_path}")


def main():
    """Example usage"""
    config = PostTrainingConfig(
        training_type=PostTrainingType.SFT,
        model_path="./checkpoints/base_model.pt",
        output_path="./checkpoints/sft_model",
        train_data_path="./data/sft_train.json",
        eval_data_path="./data/sft_eval.json"
    )
    
    # Placeholder model
    model = nn.Linear(1000, 1000)
    
    pipeline = PostTrainingPipeline(config)
    # pipeline.run(model)


if __name__ == "__main__":
    main()
