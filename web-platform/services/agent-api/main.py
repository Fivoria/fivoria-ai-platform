"""
Fivoria AI Agent API Service
Handles agent-related tasks including chat, task management, and approvals
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
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
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from security.auth import SecurityManager

# Initialize security manager
security_manager = SecurityManager(secret_key="fivoria-secret-key-change-in-production")

async def get_current_user(request):
    """Get current user from JWT token"""
    from fastapi import HTTPException, status
    
    auth_header = request.headers.get("authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    token = auth_header.replace("Bearer ", "")
    payload = security_manager.token_manager.decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("user_id")
    user = security_manager.users.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

app = FastAPI(
    title="Fivoria AI Agent API",
    description="Agent API for Fivoria AI Platform",
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

# Security
security = HTTPBearer()

# Pydantic models
class ChatRequest(BaseModel):
    conversation_id: str
    project_id: Optional[str] = None
    message: str
    model: Optional[str] = "fivoria-base"
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: Optional[List[Dict[str, Any]]] = None

class TaskCreate(BaseModel):
    conversation_id: str
    project_id: Optional[str] = None
    task_type: str
    description: str
    context: Optional[Dict[str, Any]] = None

class ApprovalRequest(BaseModel):
    task_id: str
    approved: bool
    reason: Optional[str] = None

class ApprovalResponse(BaseModel):
    approval_id: str
    approved: bool
    reason: Optional[str] = None

class ToolExecutionRequest(BaseModel):
    tool_name: str
    inputs: Dict[str, Any]

# Dependency: Get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = security_manager.token_manager.decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("user_id")
    user = security_manager.users.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }

# Chat endpoint with streaming (simplified for now)
@app.post("/api/v1/agent/chat")
async def chat(request: ChatRequest, current_user = Depends(get_current_user)):
    """
    Chat with AI agent with streaming response
    """
    async def generate_response() -> AsyncGenerator[str, None]:
        try:
            # Simple mock response for now
            response_text = f"Hello {current_user['username']}! You said: {request.message}"
            
            # Stream the response
            for char in response_text:
                yield char
                await asyncio.sleep(0.01)
            
            # Send final done message
            yield f"data: {json.dumps({'type': 'done', 'conversation_id': request.conversation_id, 'response': {'content': response_text}})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'conversation_id': request.conversation_id, 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# Task endpoints
@app.post("/api/v1/agent/task")
async def create_task(data: TaskCreate, current_user = Depends(get_current_user)):
    """Create new agent task"""
    task_id = f"task-{datetime.utcnow().timestamp()}"
    
    # Create task in orchestrator
    task = agent_orchestrator.create_task(
        task_id=task_id,
        task_type=data.task_type,
        description=data.description,
        user_id=current_user["id"],
        context=data.context or {}
    )
    
    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "conversation_id": data.conversation_id,
            "project_id": data.project_id,
            "user_id": current_user["id"],
            "task_type": data.task_type,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat()
        }
    }

@app.get("/api/v1/agent/task/{task_id}")
async def get_task(task_id: str, current_user = Depends(get_current_user)):
    """Get task status"""
    # Get task from orchestrator
    task = agent_orchestrator.get_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return {
        "success": True,
        "data": {
            "task_id": task.task_id,
            "status": task.status.value,
            "current_step": task.current_step,
            "result": task.result,
            "error": task.error,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
    }

@app.post("/api/v1/agent/task/{task_id}/cancel")
async def cancel_task(task_id: str, current_user = Depends(get_current_user)):
    """Cancel task"""
    success = agent_orchestrator.cancel_task(task_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or cannot be cancelled"
        )
    
    return {
        "success": True,
        "data": None
    }

@app.get("/api/v1/agent/task/{task_id}/events")
async def get_task_events(task_id: str, current_user = Depends(get_current_user)):
    """Stream task events via SSE"""
    async def generate_events() -> AsyncGenerator[str, None]:
        try:
            # Subscribe to task events from orchestrator
            # Get task from orchestrator
            task = agent_orchestrator.get_task(task_id)
            
            if not task:
                yield f"data: {json.dumps({'type': 'error', 'task_id': task_id, 'error': 'Task not found'})}\n\n"
                return
            
            # Stream actual task events from orchestrator
            yield f"data: {json.dumps({'type': 'started', 'task_id': task_id, 'plan': task.plan if hasattr(task, 'plan') else []})}\n\n"
            
            # Monitor task progress
            while task.status.value in ['queued', 'running', 'pending']:
                # Get updated task status
                task = agent_orchestrator.get_task(task_id)
                
                if task.current_step:
                    yield f"data: {json.dumps({'type': 'progress', 'task_id': task_id, 'step': task.current_step, 'status': task.status.value})}\n\n"
                
                await asyncio.sleep(0.5)
            
            # Task completed
            task = agent_orchestrator.get_task(task_id)
            if task.status.value == 'completed':
                yield f"data: {json.dumps({'type': 'completed', 'task_id': task_id, 'result': task.result})}\n\n"
            elif task.status.value == 'failed':
                yield f"data: {json.dumps({'type': 'failed', 'task_id': task_id, 'error': task.error})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'task_id': task_id, 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# Approval endpoints
@app.post("/api/v1/agent/approval")
async def handle_approval(data: ApprovalResponse, current_user = Depends(get_current_user)):
    """Handle approval request"""
    try:
        # Get task from orchestrator that needs approval
        task = agent_orchestrator.get_task(data.task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Process approval
        if data.approved:
            # Resume task execution
            agent_orchestrator.resume_task(data.task_id)
        else:
            # Cancel task
            agent_orchestrator.cancel_task(data.task_id)
        
        return {
            "success": True,
            "data": {
                "approval_id": data.approval_id,
                "status": "approved" if data.approved else "denied",
                "decided_at": datetime.utcnow().isoformat(),
                "reason": data.reason
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle approval: {str(e)}"
        )

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agent-api",
        "timestamp": datetime.utcnow().isoformat()
    }

# WebSocket endpoints
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time event streaming"""
    connection_id = f"{user_id}-{datetime.utcnow().timestamp()}"
    
    await websocket_manager.connect(websocket, user_id, connection_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "subscribe_task":
                task_id = data.get("task_id")
                if task_id:
                    websocket_manager.subscribe_to_task(task_id, user_id)
                    await websocket_manager.send_personal_message(
                        {
                            "type": "subscribed",
                            "task_id": task_id,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        user_id,
                        connection_id
                    )
            
            elif data.get("type") == "unsubscribe_task":
                task_id = data.get("task_id")
                if task_id:
                    websocket_manager.unsubscribe_from_task(task_id, user_id)
                    await websocket_manager.send_personal_message(
                        {
                            "type": "unsubscribed",
                            "task_id": task_id,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        user_id,
                        connection_id
                    )
            
            elif data.get("type") == "ping":
                await websocket_manager.send_personal_message(
                    {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    user_id,
                    connection_id
                )
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id, connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        websocket_manager.disconnect(user_id, connection_id)

@app.get("/ws/connections")
async def get_connections(current_user = Depends(get_current_user)):
    """Get active WebSocket connection count"""
    return {
        "success": True,
        "data": {
            "total_connections": websocket_manager.get_connection_count(),
            "user_connections": websocket_manager.get_connection_count(current_user["id"]),
            "connected_users": len(websocket_manager.get_user_ids())
        }
    }

# Recovery endpoints
@app.post("/api/v1/recovery/task/{task_id}/cancel")
async def cancel_task(task_id: str, reason: Optional[str] = "User cancelled", current_user = Depends(get_current_user)):
    """Request cancellation of a task"""
    success = recovery_manager.request_cancellation(task_id, reason)
    
    if success:
        # Notify via WebSocket
        await websocket_manager.send_task_event(task_id, {
            "type": "cancellation_requested",
            "reason": reason
        })
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "status": "cancellation_requested",
                "reason": reason
            }
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be cancelled (not running or not found)"
        )

@app.post("/api/v1/recovery/task/{task_id}/pause")
async def pause_task(task_id: str, current_user = Depends(get_current_user)):
    """Pause a running task"""
    success = recovery_manager.pause_task(task_id)
    
    if success:
        # Notify via WebSocket
        await websocket_manager.send_task_event(task_id, {
            "type": "paused"
        })
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "status": "paused"
            }
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be paused (not running or not found)"
        )

@app.post("/api/v1/recovery/task/{task_id}/resume")
async def resume_task(task_id: str, current_user = Depends(get_current_user)):
    """Resume a paused task"""
    success = recovery_manager.resume_task(task_id)
    
    if success:
        # Notify via WebSocket
        await websocket_manager.send_task_event(task_id, {
            "type": "resumed"
        })
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "status": "running"
            }
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be resumed (not paused or not found)"
        )

@app.get("/api/v1/recovery/task/{task_id}")
async def get_task_state(task_id: str, current_user = Depends(get_current_user)):
    """Get current task state"""
    task_state = recovery_manager.get_task_state(task_id)
    
    if not task_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if cancellation was requested
    is_cancelled, cancel_reason = recovery_manager.is_cancellation_requested(task_id)
    
    return {
        "success": True,
        "data": {
            **task_state,
            "cancellation_requested": is_cancelled,
            "cancellation_reason": cancel_reason
        }
    }

@app.get("/api/v1/recovery/tasks")
async def get_all_tasks(current_user = Depends(get_current_user)):
    """Get all tasks for current user"""
    tasks = recovery_manager.get_all_tasks(current_user["id"])
    return {
        "success": True,
        "data": tasks
    }

@app.post("/api/v1/recovery/cleanup")
async def cleanup_old_tasks(hours: int = 24, current_user = Depends(get_current_user)):
    """Clean up old completed/failed tasks"""
    removed = recovery_manager.cleanup_old_tasks(hours)
    return {
        "success": True,
        "data": {
            "removed_tasks": removed,
            "hours_threshold": hours
        }
    }

@app.get("/api/v1/recovery/statistics")
async def get_recovery_statistics(current_user = Depends(get_current_user)):
    """Get recovery manager statistics"""
    stats = recovery_manager.get_statistics()
    return {
        "success": True,
        "data": stats
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
