"""
Fivoria AI Model Gateway Service
Connects to the Fivoria inference gateway and provides unified model interface
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
import sys
import os
import json
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import existing Fivoria components
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from inference.gateway import ModelRouter, InferenceEngine

app = FastAPI(
    title="Fivoria AI Model Gateway",
    description="Model gateway for Fivoria AI Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize model router and inference engine
model_router = ModelRouter()
inference_engine = InferenceEngine()

# Register default models
model_router.register_model("fivoria-base", {
    "name": "Fivoria Base",
    "available": True,
    "max_tokens": 4096,
    "context_length": 8192,
    "provider": "openrouter",
    "model_id": "meta-llama/llama-3-8b"
})

model_router.register_model("fivoria-large", {
    "name": "Fivoria Large",
    "available": True,
    "max_tokens": 8192,
    "context_length": 16384,
    "provider": "openrouter",
    "model_id": "meta-llama/llama-3-70b"
})

# Register provider models if API keys are available
if os.getenv('OPENAI_API_KEY'):
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

if os.getenv('ANTHROPIC_API_KEY'):
    model_router.register_model("claude-3-opus", {
        "name": "Claude 3 Opus",
        "available": True,
        "max_tokens": 4096,
        "context_length": 200000,
        "provider": "anthropic",
        "model_id": "claude-3-opus-20240229"
    })

# Pydantic models
class ChatCompletionRequest(BaseModel):
    model: str = "fivoria-base"
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None

class EmbeddingRequest(BaseModel):
    model: str = "fivoria-embeddings"
    input: List[str]

class ModelInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    context_length: int = 8192
    max_tokens: int = 4096

# Model registry
AVAILABLE_MODELS = [
    ModelInfo(
        id="fivoria-base",
        name="Fivoria Base",
        description="Base Fivoria model for general tasks",
        context_length=8192,
        max_tokens=4096
    ),
    ModelInfo(
        id="fivoria-large",
        name="Fivoria Large",
        description="Large Fivoria model for complex tasks",
        context_length=16384,
        max_tokens=8192
    ),
    ModelInfo(
        id="fivoria-embeddings",
        name="Fivoria Embeddings",
        description="Embedding model for semantic search",
        context_length=512,
        max_tokens=512
    )
]

# Add provider models if available
if os.getenv('OPENAI_API_KEY'):
    AVAILABLE_MODELS.extend([
        ModelInfo(
            id="gpt-4",
            name="GPT-4",
            description="OpenAI GPT-4 model",
            context_length=8192,
            max_tokens=8192
        ),
        ModelInfo(
            id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            description="OpenAI GPT-3.5 Turbo model",
            context_length=4096,
            max_tokens=4096
        )
    ])

if os.getenv('ANTHROPIC_API_KEY'):
    AVAILABLE_MODELS.append(
        ModelInfo(
            id="claude-3-opus",
            name="Claude 3 Opus",
            description="Anthropic Claude 3 Opus model",
            context_length=200000,
            max_tokens=4096
        )
    )

@app.get("/api/v1/models")
async def list_models():
    """List available models"""
    return {
        "success": True,
        "data": {
            "models": [model.dict() for model in AVAILABLE_MODELS],
            "total": len(AVAILABLE_MODELS)
        }
    }

@app.get("/api/v1/models/{model_id}")
async def get_model(model_id: str):
    """Get model information"""
    model = next((m for m in AVAILABLE_MODELS if m.id == model_id), None)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )
    
    return {
        "success": True,
        "data": model.dict()
    }

@app.post("/api/v1/chat/completions")
async def chat_completion(request: ChatCompletionRequest):
    """Generate chat completion"""
    try:
        # Get model config from router
        model_config = model_router.get_model_config(request.model)
        
        if not model_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {request.model} not found"
            )
        
        # Get actual model_id for provider
        actual_model_id = model_config.get("model_id", request.model)
        
        if request.stream:
            # Streaming response
            async def generate_stream() -> AsyncGenerator[str, None]:
                try:
                    # Generate response from inference engine
                    response = await inference_engine.generate(
                        messages=request.messages,
                        model=actual_model_id,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens
                    )
                    
                    # Stream tokens character by character
                    content = response["content"]
                    for char in content:
                        yield f"data: {json.dumps({'choices': [{'delta': {'content': char}}]})}\n\n"
                        await asyncio.sleep(0.01)
                    
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # Non-streaming response
            response = await inference_engine.generate(
                messages=request.messages,
                model=actual_model_id,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            return {
                "success": True,
                "data": {
                    "id": f"chatcmpl-{datetime.utcnow().timestamp()}",
                    "model": request.model,
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": response["content"]
                        },
                        "finish_reason": response["finish_reason"]
                    }],
                    "usage": {
                        "prompt_tokens": sum(len(m.get('content', '')) for m in request.messages),
                        "completion_tokens": response["tokens_generated"],
                        "total_tokens": sum(len(m.get('content', '')) for m in request.messages) + response["tokens_generated"]
                    }
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )

@app.post("/api/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    """Generate embeddings for text"""
    try:
        embeddings = await inference_engine.embed(
            texts=request.input,
            model=request.model
        )
        
        return {
            "success": True,
            "data": {
                "model": request.model,
                "data": [
                    {"embedding": emb, "index": i}
                    for i, emb in enumerate(embeddings)
                ],
                "usage": {
                    "total_tokens": sum(len(text) for text in request.input)
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}"
        )

@app.post("/api/v1/tokens/count")
async def count_tokens(text: str, model: str = "fivoria-base"):
    """Count tokens in text"""
    # Simple token count approximation
    # In production, use actual tokenizer (tiktoken for OpenAI, etc.)
    token_count = len(text.split())
    
    return {
        "success": True,
        "data": {
            "model": model,
            "token_count": token_count,
            "character_count": len(text),
            "note": "Token count is approximate. For production, integrate with actual tokenizer."
        }
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check model router
    models_available = len(model_router.models)
    
    return {
        "status": "healthy",
        "service": "model-gateway",
        "models_available": models_available,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
