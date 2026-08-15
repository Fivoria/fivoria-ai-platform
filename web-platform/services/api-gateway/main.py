"""
Fivoria AI API Gateway
Central gateway for routing requests to backend services
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from httpx import AsyncClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fivoria AI API Gateway",
    description="Central API Gateway for Fivoria AI Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
SERVICES = {
    "web-api": "http://web-api:8001",
    "agent-api": "http://agent-api:8002",
    "project-service": "http://project-service:8003",
    "model-gateway": "http://model-gateway:8004",
    "preview-service": "http://preview-service:8005",
}

http_client = AsyncClient()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "services": list(SERVICES.keys())
    }

@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(path: str, request: Request):
    """Proxy request to appropriate service"""
    
    # Determine target service based on path
    if path.startswith("auth/"):
        target_service = "web-api"
    elif path.startswith("user/"):
        target_service = "web-api"
    elif path.startswith("projects/"):
        target_service = "web-api"
    elif path.startswith("conversations/"):
        target_service = "web-api"
    elif path.startswith("documents/"):
        target_service = "web-api"
    elif path.startswith("knowledge/"):
        target_service = "web-api"
    elif path.startswith("agent/"):
        target_service = "agent-api"
    elif path.startswith("tools/"):
        target_service = "agent-api"
    elif path.startswith("chat/"):
        target_service = "agent-api"
    elif path.startswith("models/"):
        target_service = "model-gateway"
    elif path.startswith("embeddings/"):
        target_service = "model-gateway"
    elif path.startswith("tokens/"):
        target_service = "model-gateway"
    elif path.startswith("preview/"):
        target_service = "preview-service"
    else:
        target_service = "web-api"  # Default
    
    target_url = SERVICES.get(target_service)
    if not target_url:
        return JSONResponse(
            {"success": False, "error": "Service not found"},
            status_code=503
        )
    
    # Build target URL
    url = f"{target_url}/api/v1/{path}"
    
    # Get request body
    body = await request.body()
    
    # Forward request
    try:
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            content=body,
            timeout=30.0
        )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        return JSONResponse(
            {"success": False, "error": f"Proxy error: {str(e)}"},
            status_code=502
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
