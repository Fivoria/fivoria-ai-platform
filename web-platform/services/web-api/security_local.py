"""
Security middleware for Web API Service
Handles user isolation, permission checking, and security controls
"""

from fastapi import HTTPException, status, Request
from functools import wraps
from typing import Callable
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from security.auth import SecurityManager, Permission, Role

security_manager = SecurityManager(secret_key="fivoria-secret-key-change-in-production")

async def get_current_user(request: Request):
    """Get current user from JWT token"""
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

def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs (should be injected by get_current_user)
            user = kwargs.get('current_user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not security_manager.authorize(user.id, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role: Role):
    """Decorator to require specific role"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if user.role != role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def check_project_access(user_id: int, project_id: str, required_permission: Permission = Permission.READ):
    """Check if user has access to project"""
    # TODO: Implement project access checking from database
    # For now, allow all access
    return True

async def check_file_access(user_id: int, project_id: str, file_path: str, required_permission: Permission = Permission.READ):
    """Check if user has access to file"""
    # TODO: Implement file access checking
    # For now, allow all access
    return True
