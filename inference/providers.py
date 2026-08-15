"""
Fivoria AI Provider Adapters
Real provider implementations for OpenAI, Anthropic, and other AI providers
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import httpx


class BaseProvider(ABC):
    """Base class for AI model providers"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion"""
        pass
    
    @abstractmethod
    async def embed(self, text: str, model: str) -> List[float]:
        """Generate embedding"""
        pass


class OpenAIProvider(BaseProvider):
    """OpenAI API provider"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        super().__init__(api_key, base_url)
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0
        )
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion using OpenAI API"""
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "finish_reason": data["choices"][0]["finish_reason"],
                "tokens_generated": data["usage"]["completion_tokens"]
            }
        except Exception as e:
            raise Exception(f"OpenAI generation failed: {str(e)}")
    
    async def embed(self, text: str, model: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        try:
            response = await self.client.post(
                "/embeddings",
                json={
                    "model": model,
                    "input": text
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return data["data"][0]["embedding"]
        except Exception as e:
            raise Exception(f"OpenAI embedding failed: {str(e)}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class AnthropicProvider(BaseProvider):
    """Anthropic API provider"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com/v1"):
        super().__init__(api_key, base_url)
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            timeout=60.0
        )
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion using Anthropic API"""
        try:
            # Convert messages to Anthropic format
            system_message = ""
            anthropic_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            response = await self.client.post(
                "/messages",
                json={
                    "model": model,
                    "messages": anthropic_messages,
                    "system": system_message,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["content"][0]["text"],
                "finish_reason": data["stop_reason"],
                "tokens_generated": data["usage"]["output_tokens"]
            }
        except Exception as e:
            raise Exception(f"Anthropic generation failed: {str(e)}")
    
    async def embed(self, text: str, model: str) -> List[float]:
        """Anthropic doesn't have embeddings API"""
        raise NotImplementedError("Anthropic doesn't provide embeddings API")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class OpenRouterProvider(BaseProvider):
    """OpenRouter API provider (unified interface for multiple models)"""
    
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        super().__init__(api_key, base_url)
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://fivoria.ai",
                "X-Title": "Fivoria AI"
            },
            timeout=60.0
        )
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion using OpenRouter API"""
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "finish_reason": data["choices"][0]["finish_reason"],
                "tokens_generated": data["usage"]["completion_tokens"]
            }
        except Exception as e:
            raise Exception(f"OpenRouter generation failed: {str(e)}")
    
    async def embed(self, text: str, model: str) -> List[float]:
        """Generate embedding using OpenRouter API"""
        try:
            response = await self.client.post(
                "/embeddings",
                json={
                    "model": model,
                    "input": text
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return data["data"][0]["embedding"]
        except Exception as e:
            raise Exception(f"OpenRouter embedding failed: {str(e)}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class ProviderFactory:
    """Factory for creating provider instances"""
    
    @staticmethod
    def create_provider(provider_type: str, api_key: str, base_url: Optional[str] = None) -> BaseProvider:
        """Create provider instance based on type"""
        providers = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "openrouter": OpenRouterProvider
        }
        
        provider_class = providers.get(provider_type.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        return provider_class(api_key, base_url)
