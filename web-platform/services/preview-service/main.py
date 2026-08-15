"""
Fivoria AI Preview Service
Manages isolated preview containers for live website previews
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
import docker
import asyncio
import uuid

app = FastAPI(
    title="Fivoria AI Preview Service",
    description="Preview service for Fivoria AI Platform",
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

# Docker client
docker_client = docker.from_env()

# Pydantic models
class PreviewCreate(BaseModel):
    project_id: str
    workspace_path: str
    port: Optional[int] = None
    command: Optional[str] = None
    environment: Optional[Dict[str, str]] = None

class PreviewUpdate(BaseModel):
    command: Optional[str] = None

# Store active previews
active_previews: Dict[str, Dict] = {}

@app.post("/api/v1/preview/start")
async def start_preview(data: PreviewCreate):
    """Start preview container for project"""
    preview_id = str(uuid.uuid4())
    
    try:
        # Determine port
        port = data.port or 3000 + len(active_previews)
        
        # Create container
        container_name = f"preview-{data.project_id}-{preview_id[:8]}"
        
        # Build docker run command
        container_config = {
            "image": "node:18-alpine",
            "name": container_name,
            "volumes": {
                data.workspace_path: {"bind": "/app", "mode": "rw"}
            },
            "ports": {
                f"{port}/tcp": port
            },
            "working_dir": "/app",
            "detach": True,
            "environment": data.environment or {}
        }
        
        # Start container
        container = docker_client.containers.run(**container_config)
        
        # Start dev server if command provided
        if data.command:
            container.exec_run(data.command)
        
        # Store preview info
        active_previews[preview_id] = {
            "preview_id": preview_id,
            "project_id": data.project_id,
            "container_id": container.id,
            "container_name": container_name,
            "port": port,
            "url": f"http://localhost:{port}",
            "status": "running",
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "data": active_previews[preview_id]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start preview: {str(e)}"
        )

@app.get("/api/v1/preview/{preview_id}")
async def get_preview(preview_id: str):
    """Get preview status"""
    if preview_id not in active_previews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview not found"
        )
    
    preview = active_previews[preview_id]
    
    # Check container status
    try:
        container = docker_client.containers.get(preview["container_id"])
        preview["container_status"] = container.status
        preview["container_running"] = container.status == "running"
    except:
        preview["container_status"] = "not found"
        preview["container_running"] = False
    
    return {
        "success": True,
        "data": preview
    }

@app.post("/api/v1/preview/{preview_id}/restart")
async def restart_preview(preview_id: str):
    """Restart preview container"""
    if preview_id not in active_previews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview not found"
        )
    
    try:
        container = docker_client.containers.get(active_previews[preview_id]["container_id"])
        container.restart()
        
        active_previews[preview_id]["status"] = "running"
        active_previews[preview_id]["restarted_at"] = datetime.utcnow().isoformat()
        
        return {
            "success": True,
            "data": active_previews[preview_id]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart preview: {str(e)}"
        )

@app.delete("/api/v1/preview/{preview_id}")
async def stop_preview(preview_id: str):
    """Stop and remove preview container"""
    if preview_id not in active_previews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview not found"
        )
    
    try:
        container = docker_client.containers.get(active_previews[preview_id]["container_id"])
        container.stop()
        container.remove()
        
        del active_previews[preview_id]
        
        return {
            "success": True,
            "data": None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop preview: {str(e)}"
        )

@app.get("/api/v1/preview/{preview_id}/logs")
async def get_preview_logs(preview_id: str, lines: int = 100):
    """Get preview container logs"""
    if preview_id not in active_previews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview not found"
        )
    
    try:
        container = docker_client.containers.get(active_previews[preview_id]["container_id"])
        logs = container.logs(tail=lines).decode('utf-8')
        
        return {
            "success": True,
            "data": {
                "logs": logs,
                "preview_id": preview_id
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}"
        )

@app.get("/api/v1/preview")
async def list_previews(project_id: Optional[str] = None):
    """List all active previews"""
    previews = list(active_previews.values())
    
    if project_id:
        previews = [p for p in previews if p["project_id"] == project_id]
    
    return {
        "success": True,
        "data": previews
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Docker connection
        docker_client.ping()
        docker_status = "connected"
    except:
        docker_status = "disconnected"
    
    return {
        "status": "healthy" if docker_status == "connected" else "degraded",
        "service": "preview-service",
        "docker": docker_status,
        "active_previews": len(active_previews),
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
