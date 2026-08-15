"""
Model configuration for Fivoria AI models
Supports scaling from 100M to 100B+ parameters
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum


class ArchitectureType(Enum):
    """Model architecture types"""
    DENSE = "dense"
    MOE = "moe"  # Mixture of Experts


class AttentionType(Enum):
    """Attention implementation types"""
    STANDARD = "standard"
    FLASH = "flash"
    MEMORY_EFFICIENT = "memory_efficient"


class NormalizationType(Enum):
    """Normalization types"""
    LAYERNORM = "layernorm"
    RMSNORM = "rmsnorm"


class ActivationType(Enum):
    """Activation functions"""
    GELU = "gelu"
    SWIGLU = "swiglu"
    RELU = "relu"
    SILU = "silu"


class PositionalEncodingType(Enum):
    """Positional encoding types"""
    ROPE = "rope"  # Rotary Position Embedding
    ALIBI = "alibi"  # Attention with Linear Biases
    LEARNED = "learned"
    SINUSOIDAL = "sinusoidal"


class PrecisionType(Enum):
    """Training precision types"""
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    FP8 = "fp8"


@dataclass
class ModelConfig:
    """
    Complete model configuration
    
    This configuration determines the parameter count and architecture
    of the model. By changing these values, you can scale from
    100M to 100B+ parameters.
    """
    
    # === Size Parameters ===
    num_layers: int = 32
    hidden_dim: int = 4096
    num_attention_heads: int = 32
    num_kv_heads: int = 8  # For Grouped Query Attention (GQA)
    ffn_dim: int = 16384
    vocab_size: int = 128000
    max_seq_len: int = 8192
    
    # === Architecture Choices ===
    architecture_type: ArchitectureType = ArchitectureType.DENSE
    attention_type: AttentionType = AttentionType.FLASH
    normalization: NormalizationType = NormalizationType.RMSNORM
    activation: ActivationType = ActivationType.SWIGLU
    positional_encoding: PositionalEncodingType = PositionalEncodingType.ROPE
    
    # === MoE Parameters (if architecture_type == MOE) ===
    num_experts: int = 8
    top_k_experts: int = 2
    shared_experts: int = 2
    
    # === Training Parameters ===
    precision: PrecisionType = PrecisionType.BF16
    use_gradient_checkpointing: bool = True
    gradient_checkpointing_interval: int = 1
    
    # === Parallelism Configuration ===
    tensor_parallel_size: int = 1
    pipeline_parallel_size: int = 1
    data_parallel_size: int = 1
    context_parallel_size: int = 1
    expert_parallel_size: int = 1  # For MoE
    
    # === Regularization ===
    dropout: float = 0.0
    attention_dropout: float = 0.0
    hidden_dropout: float = 0.0
    
    # === Initialization ===
    init_std: float = 0.02
    init_range: float = 0.02
    
    # === Additional Settings ===
    use_bias: bool = False
    tie_word_embeddings: bool = False
    scale_attn_by_inverse_layer_idx: bool = False
    scale_attn_by_root_layer_idx: bool = False
    
    def estimate_parameters(self) -> int:
        """
        Estimate total parameter count
        
        Returns:
            Estimated number of parameters
        """
        # Embedding parameters
        embedding_params = self.vocab_size * self.hidden_dim
        
        # Layer parameters (per layer)
        if self.architecture_type == ArchitectureType.DENSE:
            # Attention
            qkv_params = self.hidden_dim * 3 * self.hidden_dim
            o_proj_params = self.hidden_dim * self.hidden_dim
            attention_params = qkv_params + o_proj_params
            
            # FFN
            gate_up_params = self.hidden_dim * 2 * self.ffn_dim
            down_params = self.ffn_dim * self.hidden_dim
            ffn_params = gate_up_params + down_params
            
            # Layer norm (negligible)
            norm_params = 4 * self.hidden_dim
            
            per_layer_params = attention_params + ffn_params + norm_params
        else:  # MoE
            # Attention (same as dense)
            qkv_params = self.hidden_dim * 3 * self.hidden_dim
            o_proj_params = self.hidden_dim * self.hidden_dim
            attention_params = qkv_params + o_proj_params
            
            # MoE FFN
            gate_params = self.hidden_dim * self.num_experts
            expert_params = self.num_experts * (self.hidden_dim * 2 * self.ffn_dim + self.ffn_dim * self.hidden_dim)
            shared_params = self.shared_experts * (self.hidden_dim * 2 * self.ffn_dim + self.ffn_dim * self.hidden_dim)
            ffn_params = gate_params + expert_params + shared_params
            
            norm_params = 4 * self.hidden_dim
            per_layer_params = attention_params + ffn_params + norm_params
        
        # Total parameters
        total_params = embedding_params + self.num_layers * per_layer_params
        
        # Output layer (if not tied)
        if not self.tie_word_embeddings:
            total_params += self.vocab_size * self.hidden_dim
        
        return total_params
    
    def estimate_memory(self, precision: Optional[PrecisionType] = None) -> Dict[str, float]:
        """
        Estimate memory requirements in GB
        
        Args:
            precision: Precision type (uses config default if None)
        
        Returns:
            Dictionary with memory estimates
        """
        if precision is None:
            precision = self.precision
        
        params = self.estimate_parameters()
        
        # Bytes per parameter based on precision
        bytes_per_param = {
            PrecisionType.FP32: 4,
            PrecisionType.FP16: 2,
            PrecisionType.BF16: 2,
            PrecisionType.FP8: 1,
        }[precision]
        
        # Model weights memory
        weights_memory_gb = (params * bytes_per_param) / (1024**3)
        
        # Gradients memory (same as weights)
        gradients_memory_gb = weights_memory_gb
        
        # Optimizer states (AdamW: 2x weights for momentum + variance)
        optimizer_memory_gb = 2 * weights_memory_gb
        
        # Activations (rough estimate, depends on sequence length and batch size)
        # This is a simplified estimate
        activations_memory_gb = (self.hidden_dim * self.max_seq_len * bytes_per_param * 4) / (1024**3)
        
        # Total training memory (rough estimate)
        total_training_memory_gb = weights_memory_gb + gradients_memory_gb + optimizer_memory_gb + activations_memory_gb
        
        return {
            "parameters": params,
            "weights_gb": weights_memory_gb,
            "gradients_gb": gradients_memory_gb,
            "optimizer_gb": optimizer_memory_gb,
            "activations_gb": activations_memory_gb,
            "total_training_gb": total_training_memory_gb,
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "num_layers": self.num_layers,
            "hidden_dim": self.hidden_dim,
            "num_attention_heads": self.num_attention_heads,
            "num_kv_heads": self.num_kv_heads,
            "ffn_dim": self.ffn_dim,
            "vocab_size": self.vocab_size,
            "max_seq_len": self.max_seq_len,
            "architecture_type": self.architecture_type.value,
            "attention_type": self.attention_type.value,
            "normalization": self.normalization.value,
            "activation": self.activation.value,
            "positional_encoding": self.positional_encoding.value,
            "num_experts": self.num_experts if self.architecture_type == ArchitectureType.MOE else None,
            "top_k_experts": self.top_k_experts if self.architecture_type == ArchitectureType.MOE else None,
            "precision": self.precision.value,
            "use_gradient_checkpointing": self.use_gradient_checkpointing,
            "tensor_parallel_size": self.tensor_parallel_size,
            "pipeline_parallel_size": self.pipeline_parallel_size,
            "data_parallel_size": self.data_parallel_size,
            "estimated_parameters": self.estimate_parameters(),
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> "ModelConfig":
        """Create from dictionary"""
        return cls(
            num_layers=config_dict["num_layers"],
            hidden_dim=config_dict["hidden_dim"],
            num_attention_heads=config_dict["num_attention_heads"],
            num_kv_heads=config_dict.get("num_kv_heads", config_dict["num_attention_heads"]),
            ffn_dim=config_dict["ffn_dim"],
            vocab_size=config_dict["vocab_size"],
            max_seq_len=config_dict["max_seq_len"],
            architecture_type=ArchitectureType(config_dict.get("architecture_type", "dense")),
            attention_type=AttentionType(config_dict.get("attention_type", "flash")),
            normalization=NormalizationType(config_dict.get("normalization", "rmsnorm")),
            activation=ActivationType(config_dict.get("activation", "swiglu")),
            positional_encoding=PositionalEncodingType(config_dict.get("positional_encoding", "rope")),
            num_experts=config_dict.get("num_experts", 8),
            top_k_experts=config_dict.get("top_k_experts", 2),
            precision=PrecisionType(config_dict.get("precision", "bf16")),
            use_gradient_checkpointing=config_dict.get("use_gradient_checkpointing", True),
            tensor_parallel_size=config_dict.get("tensor_parallel_size", 1),
            pipeline_parallel_size=config_dict.get("pipeline_parallel_size", 1),
            data_parallel_size=config_dict.get("data_parallel_size", 1),
        )


# Predefined configurations for different model sizes

def get_100M_config() -> ModelConfig:
    """100M parameter model (proof of concept)"""
    return ModelConfig(
        num_layers=12,
        hidden_dim=768,
        num_attention_heads=12,
        num_kv_heads=12,
        ffn_dim=3072,
        vocab_size=50000,
        max_seq_len=2048,
        precision=PrecisionType.BF16,
    )


def get_1B_config() -> ModelConfig:
    """1B parameter model"""
    return ModelConfig(
        num_layers=24,
        hidden_dim=2048,
        num_attention_heads=32,
        num_kv_heads=32,
        ffn_dim=8192,
        vocab_size=100000,
        max_seq_len=4096,
        precision=PrecisionType.BF16,
    )


def get_3B_config() -> ModelConfig:
    """3B parameter model"""
    return ModelConfig(
        num_layers=32,
        hidden_dim=3072,
        num_attention_heads=32,
        num_kv_heads=8,
        ffn_dim=12288,
        vocab_size=100000,
        max_seq_len=4096,
        precision=PrecisionType.BF16,
    )


def get_7B_config() -> ModelConfig:
    """7B parameter model"""
    return ModelConfig(
        num_layers=32,
        hidden_dim=4096,
        num_attention_heads=32,
        num_kv_heads=8,
        ffn_dim=16384,
        vocab_size=128000,
        max_seq_len=8192,
        precision=PrecisionType.BF16,
    )


def get_13B_config() -> ModelConfig:
    """13B parameter model"""
    return ModelConfig(
        num_layers=40,
        hidden_dim=5120,
        num_attention_heads=40,
        num_kv_heads=10,
        ffn_dim=20480,
        vocab_size=128000,
        max_seq_len=8192,
        precision=PrecisionType.BF16,
    )


def get_30B_config() -> ModelConfig:
    """30B parameter model"""
    return ModelConfig(
        num_layers=48,
        hidden_dim=6656,
        num_attention_heads=52,
        num_kv_heads=13,
        ffn_dim=26624,
        vocab_size=128000,
        max_seq_len=16384,
        precision=PrecisionType.BF16,
    )


def get_70B_config() -> ModelConfig:
    """70B parameter model"""
    return ModelConfig(
        num_layers=80,
        hidden_dim=8192,
        num_attention_heads=64,
        num_kv_heads=8,
        ffn_dim=32768,
        vocab_size=128000,
        max_seq_len=16384,
        precision=PrecisionType.BF16,
    )


def get_100B_config() -> ModelConfig:
    """100B parameter model"""
    return ModelConfig(
        num_layers=96,
        hidden_dim=12288,
        num_attention_heads=96,
        num_kv_heads=8,
        ffn_dim=49152,
        vocab_size=128000,
        max_seq_len=32768,
        precision=PrecisionType.BF16,
    )


def get_100B_moe_config() -> ModelConfig:
    """100B parameter Mixture-of-Experts model"""
    return ModelConfig(
        num_layers=64,
        hidden_dim=6144,
        num_attention_heads=48,
        num_kv_heads=8,
        ffn_dim=16384,
        vocab_size=128000,
        max_seq_len=32768,
        architecture_type=ArchitectureType.MOE,
        num_experts=64,
        top_k_experts=2,
        shared_experts=2,
        precision=PrecisionType.BF16,
    )


if __name__ == "__main__":
    # Demo: Show parameter estimates for different model sizes
    configs = [
        ("100M", get_100M_config()),
        ("1B", get_1B_config()),
        ("7B", get_7B_config()),
        ("70B", get_70B_config()),
        ("100B", get_100B_config()),
        ("100B MoE", get_100B_moe_config()),
    ]
    
    print("Model Size Estimates:")
    print("=" * 80)
    for name, config in configs:
        params = config.estimate_parameters()
        memory = config.estimate_memory()
        print(f"\n{name}:")
        print(f"  Parameters: {params:,}")
        print(f"  Weights (BF16): {memory['weights_gb']:.2f} GB")
        print(f"  Training Memory: {memory['total_training_memory_gb']:.2f} GB")
