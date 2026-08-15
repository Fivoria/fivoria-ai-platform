"""
Fivoria AI Gateway
API gateway for AI model serving with routing, rate limiting, and observability
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime, timedelta
import time
from collections import defaultdict
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import provider adapters
from inference.providers import ProviderFactory, BaseProvider


# Pydantic models

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = Field(..., description="Model identifier")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    max_tokens: Optional[int] = Field(default=2048, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=0.7, description="Sampling temperature")
    stream: Optional[bool] = Field(default=False, description="Whether to stream responses")
    tools: Optional[List[Dict]] = Field(default=None, description="Available tools")


class ChatResponse(BaseModel):
    id: str
    model: str
    choices: List[Dict]
    usage: Dict
    created: int


class EmbeddingRequest(BaseModel):
    model: str = Field(..., description="Model identifier")
    input: str = Field(..., description="Text to embed")


class EmbeddingResponse(BaseModel):
    id: str
    model: str
    embeddings: List[List[float]]
    usage: Dict


class ErrorResponse(BaseModel):
    error: str
    message: str


# Rate limiting

class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True


# Add httpx to requirements
# Add python-dotenv to requirements

class ModelRouter:
    """Router for different model providers"""
    
    def __init__(self):
        self.models: Dict[str, Dict] = {}
        self.fallback_models: Dict[str, str] = {}
    
    def register_model(self, model_id: str, config: Dict):
        """Register a model"""
        self.models[model_id] = config
    
    def set_fallback(self, primary: str, fallback: str):
        """Set fallback model"""
        self.fallback_models[primary] = fallback
    
    def get_model_config(self, model_id: str) -> Optional[Dict]:
        """Get model configuration"""
        return self.models.get(model_id)
    
    def route_request(self, model_id: str) -> str:
        """Route request to appropriate model"""
        # Check if model is available
        if model_id in self.models and self.models[model_id].get("available", True):
            return model_id
        
        # Check for fallback
        if model_id in self.fallback_models:
            fallback = self.fallback_models[model_id]
            if fallback in self.models and self.models[fallback].get("available", True):
                return fallback
        
        raise ValueError(f"No available model for {model_id}")


# Real inference engine with provider adapters

class InferenceEngine:
    """Real inference engine using provider adapters"""
    
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        self.model_providers: Dict[str, str] = {}  # Maps model_id to provider_type
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize providers from environment variables"""
        # OpenAI
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.providers['openai'] = ProviderFactory.create_provider('openai', openai_key)
            self.model_providers['gpt-4'] = 'openai'
            self.model_providers['gpt-4-turbo'] = 'openai'
            self.model_providers['gpt-3.5-turbo'] = 'openai'
            self.model_providers['text-embedding-ada-002'] = 'openai'
        
        # Anthropic
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            self.providers['anthropic'] = ProviderFactory.create_provider('anthropic', anthropic_key)
            self.model_providers['claude-3-opus'] = 'anthropic'
            self.model_providers['claude-3-sonnet'] = 'anthropic'
            self.model_providers['claude-3-haiku'] = 'anthropic'
        
        # OpenRouter
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if openrouter_key:
            self.providers['openrouter'] = ProviderFactory.create_provider('openrouter', openrouter_key)
            # OpenRouter supports many models, map common ones
            self.model_providers['openai/gpt-4'] = 'openrouter'
            self.model_providers['anthropic/claude-3-opus'] = 'openrouter'
            self.model_providers['meta-llama/llama-3-70b'] = 'openrouter'
    
    async def generate(self, model: str, messages: List[Dict], **kwargs) -> Dict:
        """Generate response using appropriate provider"""
        # Check if model is mapped to a provider
        provider_type = self.model_providers.get(model)
        
        if not provider_type:
            # Try to infer provider from model name
            if model.startswith('gpt-'):
                provider_type = 'openai'
            elif model.startswith('claude-'):
                provider_type = 'anthropic'
            elif '/' in model:
                provider_type = 'openrouter'
            else:
                # Default to first available provider
                provider_type = list(self.providers.keys())[0] if self.providers else None
        
        if not provider_type or provider_type not in self.providers:
            raise ValueError(f"No provider available for model: {model}")
        
        provider = self.providers[provider_type]
        
        return await provider.generate(
            messages=messages,
            model=model,
            **kwargs
        )
    
    async def embed(self, model: str, text: str) -> List[float]:
        """Generate embedding using appropriate provider"""
        provider_type = self.model_providers.get(model, 'openai')
        
        if provider_type not in self.providers:
            raise ValueError(f"No provider available for model: {model}")
        
        provider = self.providers[provider_type]
        
        return await provider.embed(text=text, model=model)
    
    async def close(self):
        """Close all provider connections"""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()


# FastAPI app

app = FastAPI(
    title="Fivoria AI Gateway",
    description="API gateway for Fivoria AI models",
    version="1.0.0"
)

# Initialize components
security = HTTPBearer()
rate_limiter = RateLimiter(requests_per_minute=60)
model_router = ModelRouter()
inference_engine = InferenceEngine()

# Register models
model_router.register_model("fivoria-100b", {
    "name": "Fivoria 100B",
    "available": True,
    "endpoint": "http://inference-service:8000",
    "max_tokens": 32768,
    "context_length": 32768,
    "provider": "openrouter",  # Use OpenRouter for Fivoria models
    "model_id": "meta-llama/llama-3-70b"  # Map to actual model
})

model_router.register_model("fivoria-7b", {
    "name": "Fivoria 7B",
    "available": True,
    "endpoint": "http://inference-service:8000",
    "max_tokens": 8192,
    "context_length": 8192,
    "provider": "openrouter",
    "model_id": "meta-llama/llama-3-8b"
})

# Register real provider models
if 'openai' in inference_engine.providers:
    model_router.register_model("gpt-4", {
        "name": "GPT-4",
        "available": True,
        "max_tokens": 8192,
        "context_length": 8192,
        "provider": "openai",
        "model_id": "gpt-4"
    })
    
    model_router.register_model("gpt-3.5-turbo", {
        "name": "GPT-3.5 Turbo",
        "available": True,
        "max_tokens": 4096,
        "context_length": 4096,
        "provider": "openai",
        "model_id": "gpt-3.5-turbo"
    })

if 'anthropic' in inference_engine.providers:
    model_router.register_model("claude-3-opus", {
        "name": "Claude 3 Opus",
        "available": True,
        "max_tokens": 4096,
        "context_length": 200000,
        "provider": "anthropic",
        "model_id": "claude-3-opus-20240229"
    })

# Set fallback model
model_router.set_fallback("fivoria-100b", "fivoria-7b")


# Dependencies

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify API key"""
    token = credentials.credentials
    
    # In production, verify against database
    # For demo, accept any token
    return token


async def check_rate_limit(api_key: str = Depends(verify_api_key)) -> str:
    """Check rate limit"""
    if not rate_limiter.is_allowed(api_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    return api_key


# Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "models": {
            "fivoria-100b": model_router.models.get("fivoria-100b", {}).get("available", False),
            "fivoria-7b": model_router.models.get("fivoria-7b", {}).get("available", False),
        }
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"ready": True}


@app.get("/models")
async def list_models():
    """List available models"""
    return {
        "data": [
            {
                "id": model_id,
                "name": config.get("name", model_id),
                "available": config.get("available", False),
                "max_tokens": config.get("max_tokens"),
                "context_length": config.get("context_length")
            }
            for model_id, config in model_router.models.items()
        ]
    }


@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(
    request: ChatRequest,
    api_key: str = Depends(check_rate_limit)
):
    """Chat completions endpoint"""
    try:
        # Route to appropriate model
        model_id = model_router.route_request(request.model)
        
        # Get model config to check if it has a specific model_id for the provider
        model_config = model_router.get_model_config(model_id)
        actual_model_id = model_config.get("model_id", model_id) if model_config else model_id
        
        # Convert messages to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Generate response
        start_time = time.time()
        result = await inference_engine.generate(
            actual_model_id,
            messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Build response
        response = ChatResponse(
            id=f"chatcmpl-{int(time.time())}",
            model=model_id,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result["content"]
                },
                "finish_reason": result["finish_reason"]
            }],
            usage={
                "prompt_tokens": sum(len(msg.content.split()) for msg in request.messages),
                "completion_tokens": result["tokens_generated"],
                "total_tokens": sum(len(msg.content.split()) for msg in request.messages) + result["tokens_generated"]
            },
            created=int(time.time())
        )
        
        return response
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def embeddings(
    request: EmbeddingRequest,
    api_key: str = Depends(check_rate_limit)
):
    """Embeddings endpoint"""
    try:
        # Generate embedding
        embedding = await inference_engine.embed(request.model, request.input)
        
        response = EmbeddingResponse(
            id=f"embedding-{int(time.time())}",
            model=request.model,
            embeddings=[embedding],
            usage={
                "prompt_tokens": len(request.input.split()),
                "total_tokens": len(request.input.split())
            }
        )
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """Get model information"""
    config = model_router.get_model_config(model_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "id": model_id,
        "name": config.get("name", model_id),
        "available": config.get("available", False),
        "max_tokens": config.get("max_tokens"),
        "context_length": config.get("context_length")
    }


# Metrics endpoint (for observability)

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics"""
    return {
        "requests_total": sum(len(reqs) for reqs in rate_limiter.requests.values()),
        "models_available": sum(1 for config in model_router.models.values() if config.get("available", False)),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
