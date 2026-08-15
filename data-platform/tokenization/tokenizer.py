"""
Fivoria AI Tokenizer
Custom multilingual tokenizer supporting text, code, mathematics, and special tokens.
"""

import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class TokenizerConfig:
    """Tokenizer configuration"""
    vocab_size: int = 128000
    max_sequence_length: int = 32768
    special_tokens: Dict[str, str] = None
    
    def __post_init__(self):
        if self.special_tokens is None:
            self.special_tokens = {
                "<pad>": "<pad>",
                "<unk>": "<unk>",
                "<bos>": "<bos>",
                "<eos>": "<eos>",
                "<tool_call>": "<tool_call>",
                "<tool_response>": "<tool_response>",
                "<code_start>": "<code_start>",
                "<code_end>": "<code_end>",
                "<math_start>": "<math_start>",
                "<math_end>": "<math_end>",
                "<doc_boundary>": "<doc_boundary>",
                "<conv_boundary>": "<conv_boundary>",
            }


class FivoriaTokenizer:
    """
    Fivoria AI Tokenizer
    
    Features:
    - Multilingual support
    - Code tokenization
    - Mathematics tokenization
    - Special tokens for tools, code, math, documents
    - Efficient encoding/decoding
    """
    
    def __init__(self, config: TokenizerConfig, vocab_path: Optional[str] = None):
        self.config = config
        self.vocab = {}
        self.reverse_vocab = {}
        self.special_tokens = config.special_tokens
        
        if vocab_path and Path(vocab_path).exists():
            self.load_vocab(vocab_path)
        else:
            self._init_base_vocab()
    
    def _init_base_vocab(self):
        """Initialize base vocabulary with special tokens and common characters"""
        # Add special tokens first
        for idx, token in enumerate(self.special_tokens.values()):
            self.vocab[token] = idx
            self.reverse_vocab[idx] = token
        
        # Add common ASCII characters
        idx = len(self.vocab)
        for char in range(32, 127):  # Printable ASCII
            token = chr(char)
            self.vocab[token] = idx
            self.reverse_vocab[idx] = token
            idx += 1
        
        # Add common Unicode ranges (basic multilingual support)
        # Latin extended, Cyrillic, Greek, CJK, Arabic, etc.
        # This is a simplified version - production would use proper subword tokenization
        common_unicode_ranges = [
            (0x00C0, 0x017F),  # Latin Extended
            (0x0400, 0x04FF),  # Cyrillic
            (0x0370, 0x03FF),  # Greek
            (0x4E00, 0x4FFF),  # CJK Unified Ideographs (subset)
            (0x0600, 0x06FF),  # Arabic
        ]
        
        for start, end in common_unicode_ranges:
            for code_point in range(start, min(end, start + 1000)):  # Limit for demo
                token = chr(code_point)
                if token not in self.vocab:
                    self.vocab[token] = idx
                    self.reverse_vocab[idx] = token
                    idx += 1
    
    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """
        Encode text to token IDs
        
        Args:
            text: Input text
            add_special_tokens: Whether to add BOS/EOS tokens
        
        Returns:
            List of token IDs
        """
        tokens = []
        
        if add_special_tokens:
            tokens.append(self.vocab[self.special_tokens["<bos>"]])
        
        # Simple character-level tokenization for demo
        # Production would use BPE/WordPiece/SentencePiece
        for char in text:
            if char in self.vocab:
                tokens.append(self.vocab[char])
            else:
                tokens.append(self.vocab[self.special_tokens["<unk>"]])
        
        if add_special_tokens:
            tokens.append(self.vocab[self.special_tokens["<eos>"]])
        
        return tokens
    
    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        """
        Decode token IDs to text
        
        Args:
            token_ids: List of token IDs
            skip_special_tokens: Whether to skip special tokens in output
        
        Returns:
            Decoded text
        """
        text = ""
        for token_id in token_ids:
            if token_id in self.reverse_vocab:
                token = self.reverse_vocab[token_id]
                if skip_special_tokens and token in self.special_tokens.values():
                    continue
                text += token
        return text
    
    def tokenize_code(self, code: str) -> List[int]:
        """
        Tokenize code with special markers
        
        Args:
            code: Source code string
        
        Returns:
            List of token IDs
        """
        tokens = []
        tokens.append(self.vocab[self.special_tokens["<code_start>"]])
        tokens.extend(self.encode(code, add_special_tokens=False))
        tokens.append(self.vocab[self.special_tokens["<code_end>"]])
        return tokens
    
    def tokenize_math(self, math_text: str) -> List[int]:
        """
        Tokenize mathematical expressions with special markers
        
        Args:
            math_text: Mathematical expression
        
        Returns:
            List of token IDs
        """
        tokens = []
        tokens.append(self.vocab[self.special_tokens["<math_start>"]])
        tokens.extend(self.encode(math_text, add_special_tokens=False))
        tokens.append(self.vocab[self.special_tokens["<math_end>"]])
        return tokens
    
    def save_vocab(self, path: str):
        """Save vocabulary to file"""
        vocab_data = {
            "vocab": self.vocab,
            "special_tokens": self.special_tokens,
            "config": {
                "vocab_size": self.config.vocab_size,
                "max_sequence_length": self.config.max_sequence_length
            }
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(vocab_data, f, ensure_ascii=False, indent=2)
    
    def load_vocab(self, path: str):
        """Load vocabulary from file"""
        with open(path, 'r', encoding='utf-8') as f:
            vocab_data = json.load(f)
        
        self.vocab = vocab_data["vocab"]
        self.special_tokens = vocab_data["special_tokens"]
        self.reverse_vocab = {v: k for k, v in self.vocab.items()}
        
        config_data = vocab_data["config"]
        self.config.vocab_size = config_data["vocab_size"]
        self.config.max_sequence_length = config_data["max_sequence_length"]
    
    def get_vocab_size(self) -> int:
        """Get vocabulary size"""
        return len(self.vocab)
    
    def truncate(self, token_ids: List[int], max_length: Optional[int] = None) -> List[int]:
        """
        Truncate token IDs to max length
        
        Args:
            token_ids: List of token IDs
            max_length: Maximum length (uses config default if None)
        
        Returns:
            Truncated token IDs
        """
        if max_length is None:
            max_length = self.config.max_sequence_length
        return token_ids[:max_length]


class TokenizerTrainer:
    """
    Train tokenizer on corpus
    
    In production, this would use BPE/WordPiece/SentencePiece training
    """
    
    def __init__(self, config: TokenizerConfig):
        self.config = config
    
    def train(self, corpus: List[str], output_path: str):
        """
        Train tokenizer on corpus
        
        Args:
            corpus: List of text documents
            output_path: Path to save trained tokenizer
        """
        # In production, this would:
        # 1. Analyze corpus statistics
        # 2. Train BPE/WordPiece/SentencePiece
        # 3. Optimize vocabulary
        # 4. Benchmark compression ratio
        # 5. Evaluate token efficiency per language
        
        # For demo, create basic tokenizer
        tokenizer = FivoriaTokenizer(self.config)
        
        # Add frequent tokens from corpus
        char_freq = {}
        for text in corpus:
            for char in text:
                char_freq[char] = char_freq.get(char, 0) + 1
        
        # Add most frequent characters
        sorted_chars = sorted(char_freq.items(), key=lambda x: x[1], reverse=True)
        idx = len(tokenizer.vocab)
        
        for char, freq in sorted_chars[:1000]:  # Top 1000
            if char not in tokenizer.vocab:
                tokenizer.vocab[char] = idx
                tokenizer.reverse_vocab[idx] = char
                idx += 1
        
        tokenizer.save_vocab(output_path)
        return tokenizer
    
    def evaluate(self, tokenizer: FivoriaTokenizer, test_corpus: List[str]) -> Dict:
        """
        Evaluate tokenizer performance
        
        Args:
            tokenizer: Trained tokenizer
            test_corpus: Test corpus
        
        Returns:
            Evaluation metrics
        """
        total_chars = 0
        total_tokens = 0
        
        for text in test_corpus:
            tokens = tokenizer.encode(text, add_special_tokens=False)
            total_chars += len(text)
            total_tokens += len(tokens)
        
        compression_ratio = total_chars / total_tokens if total_tokens > 0 else 0
        
        return {
            "total_chars": total_chars,
            "total_tokens": total_tokens,
            "compression_ratio": compression_ratio,
            "vocab_size": tokenizer.get_vocab_size()
        }


def create_tokenizer(vocab_size: int = 128000, vocab_path: Optional[str] = None) -> FivoriaTokenizer:
    """
    Factory function to create tokenizer
    
    Args:
        vocab_size: Vocabulary size
        vocab_path: Path to existing vocabulary (optional)
    
    Returns:
        FivoriaTokenizer instance
    """
    config = TokenizerConfig(vocab_size=vocab_size)
    return FivoriaTokenizer(config, vocab_path)


if __name__ == "__main__":
    # Demo usage
    config = TokenizerConfig(vocab_size=10000)
    tokenizer = FivoriaTokenizer(config)
    
    # Test encoding/decoding
    text = "Hello, world! This is a test."
    tokens = tokenizer.encode(text)
    decoded = tokenizer.decode(tokens)
    
    print(f"Original: {text}")
    print(f"Tokens: {tokens}")
    print(f"Decoded: {decoded}")
    
    # Test code tokenization
    code = "def hello():\n    print('Hello, World!')"
    code_tokens = tokenizer.tokenize_code(code)
    print(f"Code tokens: {code_tokens}")
    
    # Test math tokenization
    math_expr = "E = mc^2"
    math_tokens = tokenizer.tokenize_math(math_expr)
    print(f"Math tokens: {math_tokens}")
