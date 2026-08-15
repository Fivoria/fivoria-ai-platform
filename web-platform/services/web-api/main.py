"""
Fivoria AI Web API Service
Handles web-specific API endpoints for projects, files, conversations, and documents
"""

import shutil
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import existing Fivoria components
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from security.auth import SecurityManager, Permission, Role
from database.schema import get_db_connection

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
    title="Fivoria AI Web API",
    description="Web API for Fivoria AI Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
security_manager = SecurityManager(secret_key=os.getenv('JWT_SECRET', 'fivoria-secret-key-change-in-production'))

# Pydantic models
class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    git_url: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ConversationCreate(BaseModel):
    project_id: Optional[str] = None
    title: str
    model_version_id: Optional[int] = None

class FileCreate(BaseModel):
    path: str
    content: str

class FileUpdate(BaseModel):
    content: str

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
    
    return user

# Auth endpoints
@app.post("/api/v1/auth/login")
async def login(credentials: UserLogin):
    """Authenticate user and return tokens"""
    user = security_manager.authenticate_user(
        username=credentials.email,
        password=credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    tokens = security_manager.generate_tokens(user.id)
    
    return {
        "success": True,
        "data": {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "permissions": [p.value for p in user.permissions]
            }
        }
    }

@app.post("/api/v1/auth/register")
async def register(data: UserRegister):
    """Register new user"""
    user = security_manager.register_user(
        username=data.username,
        email=data.email,
        password=data.password,
        role=Role.USER
    )
    
    tokens = security_manager.generate_tokens(user.id)
    
    return {
        "success": True,
        "data": {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "permissions": [p.value for p in user.permissions]
            }
        }
    }

@app.post("/api/v1/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    new_token = security_manager.token_manager.refresh_access_token(refresh_token)
    
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    return {
        "success": True,
        "data": {
            "access_token": new_token
        }
    }

# User endpoints
@app.get("/api/v1/user/profile")
async def get_profile(current_user = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "success": True,
        "data": current_user
    }

@app.put("/api/v1/user/profile")
async def update_profile(data: dict, current_user = Depends(get_current_user)):
    """Update user profile"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Update user profile in database
        update_fields = []
        update_values = []
        
        if 'email' in data:
            update_fields.append("email = %s")
            update_values.append(data['email'])
        
        if 'username' in data:
            update_fields.append("username = %s")
            update_values.append(data['username'])
        
        if update_fields:
            update_values.append(current_user["id"])
            cursor.execute(f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """, update_values)
            
            conn.commit()
            
            # Fetch updated user
            cursor.execute("SELECT * FROM users WHERE id = %s", (current_user["id"],))
            updated_user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "data": updated_user
            }
        else:
            cursor.close()
            conn.close()
            return {
                "success": True,
                "data": current_user
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

# Project endpoints
@app.get("/api/v1/projects")
async def get_projects(current_user = Depends(get_current_user)):
    """Get all projects for current user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM projects 
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (current_user["id"],))
        
        projects = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "data": projects
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects: {str(e)}"
        )

@app.post("/api/v1/projects")
async def create_project(data: ProjectCreate, current_user = Depends(get_current_user)):
    """Create new project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        project_id = f"proj-{datetime.utcnow().timestamp()}"
        workspace_path = os.path.join(
            os.getenv('WORKSPACE_BASE', '/tmp/fivoria-workspaces'),
            f"user_{current_user["id"]}",
            project_id
        )
        
        # Create workspace directory
        os.makedirs(workspace_path, exist_ok=True)
        
        cursor.execute("""
            INSERT INTO projects 
            (project_id, user_id, name, description, workspace_path, git_url, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            project_id,
            current_user["id"],
            data.name,
            data.description,
            workspace_path,
            data.git_url,
            "active",
            datetime.utcnow(),
            datetime.utcnow()
        ))
        
        conn.commit()
        
        cursor.execute("""
            SELECT * FROM projects WHERE project_id = %s
        """, (project_id,))
        
        project = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "data": project
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str, current_user = Depends(get_current_user)):
    """Get project by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM projects 
            WHERE project_id = %s AND user_id = %s
        """, (project_id, current_user["id"]))
        
        project = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return {
            "success": True,
            "data": project
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch project: {str(e)}"
        )

@app.put("/api/v1/projects/{project_id}")
async def update_project(project_id: str, data: ProjectUpdate, current_user = Depends(get_current_user)):
    """Update project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        if data.name is not None:
            update_fields.append("name = %s")
            update_values.append(data.name)
        
        if data.description is not None:
            update_fields.append("description = %s")
            update_values.append(data.description)
        
        if data.status is not None:
            update_fields.append("status = %s")
            update_values.append(data.status)
        
        if update_fields:
            update_fields.append("updated_at = %s")
            update_values.append(datetime.utcnow())
            update_values.extend([project_id, current_user["id"]])
            
            query = f"""
                UPDATE projects 
                SET {', '.join(update_fields)}
                WHERE project_id = %s AND user_id = %s
            """
            
            cursor.execute(query, update_values)
            conn.commit()
        
        cursor.execute("""
            SELECT * FROM projects 
            WHERE project_id = %s AND user_id = %s
        """, (project_id, current_user["id"]))
        
        project = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "data": project
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )

@app.delete("/api/v1/projects/{project_id}")
async def delete_project(project_id: str, current_user = Depends(get_current_user)):
    """Delete project and its workspace"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify project exists and user has access
        cursor.execute("SELECT * FROM projects WHERE id = %s AND user_id = %s", (project_id, current_user["id"]))
        project = cursor.fetchone()
        
        if not project:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Delete project workspace
        workspace_base = os.getenv('WORKSPACE_BASE_PATH', '/tmp/fivoria-workspaces')
        project_workspace = os.path.join(workspace_base, project_id)
        
        if os.path.exists(project_workspace):
            import shutil
            shutil.rmtree(project_workspace)
        
        # Delete project from database
        cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "deleted_at": datetime.utcnow().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )

# File endpoints
@app.get("/api/v1/projects/{project_id}/files")
async def get_files(project_id: str, path: Optional[str] = None, current_user = Depends(get_current_user)):
    """Get files in project workspace"""
    try:
        # Get workspace path for project
        workspace_base = os.getenv('WORKSPACE_BASE_PATH', '/tmp/fivoria-workspaces')
        project_workspace = os.path.join(workspace_base, project_id)
        
        # Verify project exists and user has access
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM projects WHERE id = %s AND user_id = %s", (project_id, current_user["id"]))
        project = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Get target directory
        target_dir = os.path.join(project_workspace, path) if path else project_workspace
        
        # Ensure directory exists
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        # List files
        files = []
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            relative_path = os.path.relpath(item_path, project_workspace)
            
            files.append({
                "name": item,
                "path": relative_path.replace('\\', '/'),
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size_bytes": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                "modified_at": datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
            })
        
        return {
            "success": True,
            "data": {
                "files": files,
                "total": len(files),
                "path": path or "/"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )

@app.post("/api/v1/projects/{project_id}/files")
async def create_file(project_id: str, data: FileCreate, current_user = Depends(get_current_user)):
    """Create file in project workspace"""
    try:
        # Get workspace path for project
        workspace_base = os.getenv('WORKSPACE_BASE_PATH', '/tmp/fivoria-workspaces')
        project_workspace = os.path.join(workspace_base, project_id)
        
        # Verify project exists and user has access
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM projects WHERE id = %s AND user_id = %s", (project_id, current_user["id"]))
        project = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Ensure project workspace exists
        if not os.path.exists(project_workspace):
            os.makedirs(project_workspace, exist_ok=True)
        
        # Get full file path
        file_path = os.path.join(project_workspace, data.path)
        
        # Ensure directory exists
        file_dir = os.path.dirname(file_path)
        if file_dir and not os.path.exists(file_dir):
            os.makedirs(file_dir, exist_ok=True)
        
        # Write file content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data.content)
        
        file_info = {
            "file_id": f"file-{datetime.utcnow().timestamp()}",
            "project_id": project_id,
            "path": data.path,
            "size_bytes": len(data.content.encode('utf-8')),
            "file_type": data.path.split('.')[-1] if '.' in data.path else 'unknown',
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "data": file_info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create file: {str(e)}"
        )

@app.get("/api/v1/projects/{project_id}/files/{file_path:path}")
async def get_file(project_id: str, file_path: str, current_user = Depends(get_current_user)):
    """Get file content from workspace"""
    try:
        # Get workspace path for project
        workspace_base = os.getenv('WORKSPACE_BASE_PATH', '/tmp/fivoria-workspaces')
        project_workspace = os.path.join(workspace_base, project_id)
        
        # Verify project exists and user has access
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM projects WHERE id = %s AND user_id = %s", (project_id, current_user["id"]))
        project = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Get full file path
        full_path = os.path.join(project_workspace, file_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if it's a file (not directory)
        if os.path.isdir(full_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path is a directory, not a file"
            )
        
        # Read file content
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "data": {
                "path": file_path,
                "content": content,
                "size_bytes": len(content.encode('utf-8')),
                "modified_at": datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}"
        )

@app.put("/api/v1/projects/{project_id}/files/{file_path:path}")
async def update_file(project_id: str, file_path: str, data: FileUpdate, current_user = Depends(get_current_user)):
    """Update file content in workspace"""
    try:
        # Get workspace path for project
        workspace_base = os.getenv('WORKSPACE_BASE_PATH', '/tmp/fivoria-workspaces')
        project_workspace = os.path.join(workspace_base, project_id)
        
        # Verify project exists and user has access
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM projects WHERE id = %s AND user_id = %s", (project_id, current_user["id"]))
        project = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Get full file path
        full_path = os.path.join(project_workspace, file_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Write updated content
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(data.content)
        
        return {
            "success": True,
            "data": {
                "path": file_path,
                "size_bytes": len(data.content.encode('utf-8')),
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update file: {str(e)}"
        )

@app.delete("/api/v1/projects/{project_id}/files/{file_path:path}")
async def delete_file(project_id: str, file_path: str, current_user = Depends(get_current_user)):
    """Delete file from workspace"""
    try:
        # Get workspace path for project
        workspace_base = os.getenv('WORKSPACE_BASE_PATH', '/tmp/fivoria-workspaces')
        project_workspace = os.path.join(workspace_base, project_id)
        
        # Verify project exists and user has access
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM projects WHERE id = %s AND user_id = %s", (project_id, current_user["id"]))
        project = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Get full file path
        full_path = os.path.join(project_workspace, file_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Delete file or directory
        if os.path.isdir(full_path):
            import shutil
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        
        return {
            "success": True,
            "data": {
                "path": file_path,
                "deleted_at": datetime.utcnow().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

# Conversation endpoints
@app.get("/api/v1/conversations")
async def get_conversations(current_user = Depends(get_current_user)):
    """Get all conversations"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM conversations 
            WHERE user_id = %s
            ORDER BY updated_at DESC
        """, (current_user["id"],))
        
        conversations = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "data": conversations
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversations: {str(e)}"
        )

@app.post("/api/v1/conversations")
async def create_conversation(data: ConversationCreate, current_user = Depends(get_current_user)):
    """Create new conversation"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            INSERT INTO conversations (user_id, project_id, title, model_version_id)
            VALUES (%s, %s, %s, %s)
        """, (current_user["id"], data.project_id, data.title, data.model_version_id))
        
        conversation_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM conversations WHERE id = %s", (conversation_id,))
        conversation = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "data": conversation
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )

@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, current_user = Depends(get_current_user)):
    """Get conversation by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM conversations 
            WHERE id = %s AND user_id = %s
        """, (conversation_id, current_user["id"]))
        
        conversation = cursor.fetchone()
        
        # Get messages for this conversation
        if conversation:
            cursor.execute("""
                SELECT * FROM messages 
                WHERE conversation_id = %s 
                ORDER BY created_at ASC
            """, (conversation_id,))
            
            messages = cursor.fetchall()
            conversation['messages'] = messages
        
        cursor.close()
        conn.close()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {
            "success": True,
            "data": conversation
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversation: {str(e)}"
        )

@app.delete("/api/v1/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user = Depends(get_current_user)):
    """Delete conversation"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify conversation exists and user has access
        cursor.execute("""
            SELECT * FROM conversations 
            WHERE id = %s AND user_id = %s
        """, (conversation_id, current_user["id"]))
        
        conversation = cursor.fetchone()
        
        if not conversation:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Delete messages first
        cursor.execute("DELETE FROM messages WHERE conversation_id = %s", (conversation_id,))
        
        # Delete conversation
        cursor.execute("DELETE FROM conversations WHERE id = %s", (conversation_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "data": None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )

# Document endpoints
@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile, project_id: Optional[str] = None, current_user = Depends(get_current_user)):
    """Upload document for RAG processing"""
    try:
        # Read file content
        content = await file.read()
        
        # Store document in database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            INSERT INTO documents (user_id, project_id, filename, content_type, size_bytes, content)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (current_user["id"], project_id, file.filename, file.content_type, len(content), content))
        
        document_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM documents WHERE id = %s", (document_id,))
        document = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "data": document
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

# Knowledge endpoints
@app.get("/api/v1/knowledge/search")
async def search_knowledge(query: str, project_id: Optional[str] = None, current_user = Depends(get_current_user)):
    """Search knowledge base using RAG system"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
        
        from web_platform.services.agent_api.rag_adapter import RAGAdapter
        
        rag_adapter = RAGAdapter()
        results = await rag_adapter.retrieve(query, top_k=10, project_id=project_id)
        
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search knowledge base: {str(e)}"
        )

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "web-api",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
