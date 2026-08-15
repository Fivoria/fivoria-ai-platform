"""
Fivoria AI Transformer Architecture
Configurable transformer supporting both dense and MoE architectures
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
from dataclasses import dataclass

from .config import ModelConfig, ArchitectureType, AttentionType, NormalizationType, ActivationType


class RMSNorm(nn.Module):
    """Root Mean Square Layer Normalization"""
    
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        rms = torch.sqrt(torch.mean(x.pow(2), dim=-1, keepdim=True) + self.eps)
        return self.weight * (x / rms)


class SwiGLU(nn.Module):
    """Swish-Gated Linear Unit activation"""
    
    def __init__(self, dim: int, hidden_dim: int):
        super().__init__()
        self.gate = nn.Linear(dim, hidden_dim, bias=False)
        self.up = nn.Linear(dim, hidden_dim, bias=False)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        gate = F.silu(self.gate(x))
        return gate * self.up(x)


class RotaryEmbedding(nn.Module):
    """
    Rotary Position Embedding (RoPE)
    
    Implements rotary position embeddings for attention
    """
    
    def __init__(self, dim: int, max_seq_len: int = 8192):
        super().__init__()
        self.dim = dim
        inv_freq = 1.0 / (10000 ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq)
        self.max_seq_len = max_seq_len
        self._build_cache(max_seq_len)
    
    def _build_cache(self, seq_len: int):
        t = torch.arange(seq_len, device=self.inv_freq.device).type_as(self.inv_freq)
        freqs = torch.einsum("i,j->ij", t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        self.register_buffer("cos", emb.cos()[None, None, :, :])
        self.register_buffer("sin", emb.sin()[None, None, :, :])
    
    def forward(self, x: torch.Tensor, seq_len: int) -> Tuple[torch.Tensor, torch.Tensor]:
        if seq_len > self.max_seq_len:
            self._build_cache(seq_len)
        
        return (
            self.cos[:, :, :seq_len, :],
            self.sin[:, :, :seq_len, :],
        )


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    """Rotate half the hidden dims of the input"""
    x1, x2 = x[..., :x.shape[-1] // 2], x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(q: torch.Tensor, k: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """Apply rotary position embeddings to query and key"""
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


class MultiHeadAttention(nn.Module):
    """
    Multi-Head Attention with Grouped Query Attention (GQA) support
    """
    
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.hidden_dim = config.hidden_dim
        self.num_heads = config.num_attention_heads
        self.num_kv_heads = config.num_kv_heads
        self.head_dim = config.hidden_dim // config.num_attention_heads
        self.num_kv_groups = config.num_attention_heads // config.num_kv_heads
        
        # QKV projection
        self.qkv_proj = nn.Linear(
            config.hidden_dim,
            (config.num_attention_heads + 2 * config.num_kv_heads) * self.head_dim,
            bias=config.use_bias,
        )
        
        # Output projection
        self.o_proj = nn.Linear(config.hidden_dim, config.hidden_dim, bias=config.use_bias)
        
        # Rotary embeddings
        self.rotary_emb = RotaryEmbedding(self.head_dim, config.max_seq_len)
        
        self.attention_dropout = config.attention_dropout
    
    def forward(
        self,
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        use_cache: bool = False,
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        batch_size, seq_len, _ = x.shape
        
        # QKV projection
        qkv = self.qkv_proj(x)
        qkv = qkv.view(batch_size, seq_len, -1, self.head_dim)
        
        # Split Q, K, V
        q, k, v = torch.split(qkv, [self.num_heads, self.num_kv_heads, self.num_kv_heads], dim=2)
        
        # Apply rotary embeddings
        cos, sin = self.rotary_emb(x, seq_len)
        q, k = apply_rotary_pos_emb(q, k, cos, sin)
        
        # Handle past key value (for generation)
        if past_key_value is not None:
            past_k, past_v = past_key_value
            k = torch.cat([past_k, k], dim=1)
            v = torch.cat([past_v, v], dim=1)
            seq_len = k.shape[1]
        
        # Grouped Query Attention: repeat K, V for each group
        if self.num_kv_groups > 1:
            k = k.repeat_interleave(self.num_kv_groups, dim=2)
            v = v.repeat_interleave(self.num_kv_groups, dim=2)
        
        # Transpose for attention: [batch, heads, seq_len, head_dim]
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)
        
        # Attention computation
        attn_weights = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        
        if attention_mask is not None:
            attn_weights = attn_weights + attention_mask
        
        attn_weights = F.softmax(attn_weights, dim=-1)
        attn_weights = F.dropout(attn_weights, p=self.attention_dropout, training=self.training)
        
        # Attention output
        attn_output = torch.matmul(attn_weights, v)
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, -1)
        
        # Output projection
        output = self.o_proj(attn_output)
        
        if use_cache:
            past_key_value = (k.transpose(1, 2), v.transpose(1, 2))
            return output, past_key_value
        
        return output, None


class MLP(nn.Module):
    """
    Feed-Forward Network with SwiGLU activation
    """
    
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        
        if config.activation == ActivationType.SWIGLU:
            self.gate_up_proj = nn.Linear(config.hidden_dim, 2 * config.ffn_dim, bias=config.use_bias)
            self.down_proj = nn.Linear(config.ffn_dim, config.hidden_dim, bias=config.use_bias)
            self.activation = ActivationType.SWIGLU
        else:
            self.gate_proj = nn.Linear(config.hidden_dim, config.ffn_dim, bias=config.use_bias)
            self.up_proj = nn.Linear(config.ffn_dim, config.hidden_dim, bias=config.use_bias)
            self.activation = ActivationType.GELU
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.activation == ActivationType.SWIGLU:
            gate_up = self.gate_up_proj(x)
            gate, up = gate_up.chunk(2, dim=-1)
            x = F.silu(gate) * up
        else:
            x = self.gate_proj(x)
            x = F.gelu(x)
            x = self.up_proj(x)
        
        x = self.down_proj(x)
        return x


class MoELayer(nn.Module):
    """
    Mixture of Experts Layer
    """
    
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.num_experts = config.num_experts
        self.top_k = config.top_k_experts
        self.shared_experts = config.shared_experts
        
        # Gate network
        self.gate = nn.Linear(config.hidden_dim, config.num_experts, bias=False)
        
        # Expert networks
        self.experts = nn.ModuleList([
            MLP(config) for _ in range(config.num_experts)
        ])
        
        # Shared experts (always activated)
        if self.shared_experts > 0:
            self.shared_expert_networks = nn.ModuleList([
                MLP(config) for _ in range(self.shared_experts)
            ])
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, hidden_dim = x.shape
        
        # Compute gate scores
        gate_logits = self.gate(x)  # [batch, seq_len, num_experts]
        gate_scores = F.softmax(gate_logits, dim=-1)
        
        # Select top-k experts
        topk_scores, topk_indices = torch.topk(gate_scores, self.top_k, dim=-1)
        
        # Normalize top-k scores
        topk_scores = topk_scores / topk_scores.sum(dim=-1, keepdim=True)
        
        # Process through experts
        expert_outputs = []
        for i in range(self.num_experts):
            expert_output = self.experts[i](x)
            expert_outputs.append(expert_output)
        
        expert_outputs = torch.stack(expert_outputs, dim=2)  # [batch, seq_len, num_experts, hidden]
        
        # Weighted sum of expert outputs
        output = torch.zeros_like(x)
        for k in range(self.top_k):
            expert_idx = topk_indices[:, :, k:k+1]
            weight = topk_scores[:, :, k:k+1]
            selected_expert_output = torch.gather(expert_outputs, 2, expert_idx.expand(-1, -1, -1, hidden_dim))
            output += weight * selected_expert_output.squeeze(2)
        
        # Add shared experts
        if self.shared_experts > 0:
            shared_output = sum(expert(x) for expert in self.shared_expert_networks)
            output += shared_output / self.shared_experts
        
        return output


class TransformerBlock(nn.Module):
    """
    Transformer Block with attention and MLP/MoE
    """
    
    def __init__(self, config: ModelConfig, layer_idx: int):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx
        
        # Pre-normalization
        self.input_layernorm = RMSNorm(config.hidden_dim) if config.normalization == NormalizationType.RMSNORM else nn.LayerNorm(config.hidden_dim)
        
        # Self-attention
        self.self_attn = MultiHeadAttention(config)
        
        # Post-attention normalization
        self.post_attention_layernorm = RMSNorm(config.hidden_dim) if config.normalization == NormalizationType.RMSNORM else nn.LayerNorm(config.hidden_dim)
        
        # MLP or MoE
        if config.architecture_type == ArchitectureType.MOE:
            self.mlp = MoELayer(config)
        else:
            self.mlp = MLP(config)
        
        self.hidden_dropout = config.hidden_dropout
    
    def forward(
        self,
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        use_cache: bool = False,
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        # Pre-norm + Attention
        residual = x
        x = self.input_layernorm(x)
        x, present_key_value = self.self_attn(
            x,
            attention_mask=attention_mask,
            past_key_value=past_key_value,
            use_cache=use_cache,
        )
        x = residual + F.dropout(x, p=self.hidden_dropout, training=self.training)
        
        # Post-norm + MLP/MoE
        residual = x
        x = self.post_attention_layernorm(x)
        x = self.mlp(x)
        x = residual + F.dropout(x, p=self.hidden_dropout, training=self.training)
        
        return x, present_key_value


class FivoriaTransformer(nn.Module):
    """
    Fivoria AI Transformer Model
    
    Configurable transformer supporting:
    - Dense and MoE architectures
    - Multiple attention types
    - Grouped Query Attention (GQA)
    - Rotary Position Embeddings (RoPE)
    - Gradient checkpointing
    """
    
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        
        # Embeddings
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_dim)
        
        # Transformer blocks
        self.layers = nn.ModuleList([
            TransformerBlock(config, i) for i in range(config.num_layers)
        ])
        
        # Final normalization
        self.norm = RMSNorm(config.hidden_dim) if config.normalization == NormalizationType.RMSNORM else nn.LayerNorm(config.hidden_dim)
        
        # Output projection
        if not config.tie_word_embeddings:
            self.lm_head = nn.Linear(config.hidden_dim, config.vocab_size, bias=False)
        else:
            self.lm_head = None
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        """Initialize weights"""
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=self.config.init_std)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=self.config.init_std)
        elif isinstance(module, nn.LayerNorm):
            nn.init.ones_(module.weight)
            nn.init.zeros_(module.bias)
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        past_key_values: Optional[list] = None,
        use_cache: bool = False,
    ) -> Tuple[torch.Tensor, Optional[list]]:
        """
        Forward pass
        
        Args:
            input_ids: [batch, seq_len]
            attention_mask: [batch, seq_len]
            past_key_values: List of past key values for each layer
            use_cache: Whether to return cache for generation
        
        Returns:
            logits: [batch, seq_len, vocab_size]
            past_key_values: List of present key values
        """
        batch_size, seq_len = input_ids.shape
        
        # Embed tokens
        hidden_states = self.embed_tokens(input_ids)
        
        # Process through transformer blocks
        present_key_values = [] if use_cache else None
        
        for idx, layer in enumerate(self.layers):
            past_key_value = past_key_values[idx] if past_key_values is not None else None
            
            if self.config.use_gradient_checkpointing and self.training:
                hidden_states, present_key_value = torch.utils.checkpoint.checkpoint(
                    layer,
                    hidden_states,
                    attention_mask,
                    past_key_value,
                    use_cache,
                )
            else:
                hidden_states, present_key_value = layer(
                    hidden_states,
                    attention_mask=attention_mask,
                    past_key_value=past_key_value,
                    use_cache=use_cache,
                )
            
            if use_cache:
                present_key_values.append(present_key_value)
        
        # Final normalization
        hidden_states = self.norm(hidden_states)
        
        # Output projection
        if self.lm_head is not None:
            logits = self.lm_head(hidden_states)
        else:
            logits = torch.matmul(hidden_states, self.embed_tokens.weight.transpose(0, 1))
        
        return logits, present_key_values


if __name__ == "__main__":
    # Demo: Create a small model and test forward pass
    from .config import get_100M_config
    
    config = get_100M_config()
    model = FivoriaTransformer(config)
    
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Test forward pass
    batch_size = 2
    seq_len = 128
    input_ids = torch.randint(0, config.vocab_size, (batch_size, seq_len))
    
    logits, _ = model(input_ids)
    print(f"Output shape: {logits.shape}")
