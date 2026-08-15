"""
Fivoria AI Project Service
Manages project workspaces, file operations, and Git integration
"""

from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import shutil
import subprocess
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

app = FastAPI(
    title="Fivoria AI Project Service",
    description="Project service for Fivoria AI Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Workspace base directory
WORKSPACE_BASE = "/tmp/fivoria-workspaces"

class TerminalCommand(BaseModel):
    command: str
    working_dir: Optional[str] = None

class GitOperation(BaseModel):
    operation: str  # clone, commit, push, pull, status, diff
    params: Optional[Dict[str, Any]] = None

@app.post("/api/v1/projects/{project_id}/terminal/execute")
async def execute_terminal_command(project_id: str, data: TerminalCommand):
    """Execute terminal command in project workspace"""
    workspace_path = os.path.join(WORKSPACE_BASE, project_id)
    
    if not os.path.exists(workspace_path):
        os.makedirs(workspace_path, exist_ok=True)
    
    working_dir = data.working_dir or workspace_path
    
    try:
        # Execute command with timeout
        result = subprocess.run(
            data.command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "success": True,
            "data": {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "working_dir": working_dir
            }
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Command execution timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Command execution failed: {str(e)}"
        )

@app.post("/api/v1/projects/{project_id}/git")
async def git_operation(project_id: str, data: GitOperation):
    """Execute Git operation"""
    workspace_path = os.path.join(WORKSPACE_BASE, project_id)
    
    if not os.path.exists(workspace_path):
        os.makedirs(workspace_path, exist_ok=True)
    
    try:
        if data.operation == "clone":
            url = data.params.get("url")
            if not url:
                raise HTTPException(status_code=400, detail="Git URL required")
            
            result = subprocess.run(
                ["git", "clone", url, workspace_path],
                capture_output=True,
                text=True
            )
            
        elif data.operation == "status":
            result = subprocess.run(
                ["git", "status"],
                cwd=workspace_path,
                capture_output=True,
                text=True
            )
            
        elif data.operation == "commit":
            message = data.params.get("message", "Update")
            subprocess.run(
                ["git", "add", "."],
                cwd=workspace_path,
                capture_output=True
            )
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=workspace_path,
                capture_output=True,
                text=True
            )
            
        elif data.operation == "diff":
            result = subprocess.run(
                ["git", "diff"],
                cwd=workspace_path,
                capture_output=True,
                text=True
            )
            
        elif data.operation == "push":
            result = subprocess.run(
                ["git", "push"],
                cwd=workspace_path,
                capture_output=True,
                text=True
            )
            
        elif data.operation == "pull":
            result = subprocess.run(
                ["git", "pull"],
                cwd=workspace_path,
                capture_output=True,
                text=True
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {data.operation}")
        
        return {
            "success": True,
            "data": {
                "operation": data.operation,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Git operation failed: {str(e)}"
        )

@app.get("/api/v1/projects/{project_id}/git/history")
async def get_git_history(project_id: str, limit: int = 20):
    """Get Git commit history"""
    workspace_path = os.path.join(WORKSPACE_BASE, project_id)
    
    try:
        result = subprocess.run(
            ["git", "log", f"-{limit}", "--pretty=format:%H|%an|%ae|%s|%ci"],
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        
        commits = []
        for line in result.stdout.split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "message": parts[3],
                        "date": parts[4]
                    })
        
        return {
            "success": True,
            "data": {
                "commits": commits,
                "total": len(commits)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get history: {str(e)}"
        )

@app.get("/api/v1/projects/{project_id}/git/branches")
async def get_git_branches(project_id: str):
    """Get Git branches"""
    workspace_path = os.path.join(WORKSPACE_BASE, project_id)
    
    try:
        result = subprocess.run(
            ["git", "branch", "-a"],
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        
        branches = []
        current_branch = None
        
        for line in result.stdout.split('\n'):
            if line:
                is_current = line.startswith('*')
                branch_name = line.replace('*', '').strip()
                if is_current:
                    current_branch = branch_name
                branches.append({
                    "name": branch_name,
                    "current": is_current
                })
        
        return {
            "success": True,
            "data": {
                "branches": branches,
                "current": current_branch
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get branches: {str(e)}"
        )

@app.post("/api/v1/projects/{project_id}/git/checkout")
async def git_checkout(project_id: str, branch: str):
    """Checkout Git branch"""
    workspace_path = os.path.join(WORKSPACE_BASE, project_id)
    
    try:
        result = subprocess.run(
            ["git", "checkout", branch],
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        
        return {
            "success": True,
            "data": {
                "branch": branch,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Checkout failed: {str(e)}"
        )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "project-service",
        "workspace_base": WORKSPACE_BASE,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
