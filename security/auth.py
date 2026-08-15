"""
Fivoria AI Security Layer
Authentication, authorization, and security controls
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
import bcrypt


class Permission(Enum):
    """Permission levels"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Role(Enum):
    """User roles"""
    USER = "user"
    DEVELOPER = "developer"
    ADMIN = "admin"
    SYSTEM = "system"


@dataclass
class User:
    """User entity"""
    id: int
    username: str
    email: str
    role: Role
    permissions: List[Permission]
    created_at: datetime
    is_active: bool = True


@dataclass
class APIKey:
    """API key entity"""
    id: str
    user_id: int
    name: str
    key_hash: str
    permissions: List[Permission]
    rate_limit_per_minute: int
    expires_at: Optional[datetime]
    created_at: datetime
    is_active: bool = True


class PasswordManager:
    """Password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


class APIKeyManager:
    """API key generation and management"""
    
    @staticmethod
    def generate_key() -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_key(api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_key(api_key: str, key_hash: str) -> bool:
        """Verify API key against hash"""
        return hashlib.sha256(api_key.encode()).hexdigest() == key_hash


class TokenManager:
    """JWT token generation and validation"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def generate_access_token(
        self,
        user_id: int,
        role: str,
        permissions: List[str],
        expires_in_hours: int = 24
    ) -> str:
        """Generate JWT access token"""
        payload = {
            "user_id": user_id,
            "role": role,
            "permissions": permissions,
            "type": "access",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=expires_in_hours)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_refresh_token(
        self,
        user_id: int,
        expires_in_days: int = 30
    ) -> str:
        """Generate JWT refresh token"""
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=expires_in_days)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[Dict]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token"""
        payload = self.decode_token(refresh_token)
        
        if payload is None or payload.get("type") != "refresh":
            return None
        
        user_id = payload["user_id"]
        
        # In production, would fetch user details from database
        # For demo, generate with default permissions
        return self.generate_access_token(
            user_id=user_id,
            role="user",
            permissions=["read"],
            expires_in_hours=24
        )


class RateLimiter:
    """Rate limiting for API requests"""
    
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_minutes: int = 1
    ) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
        
        # Check limit
        if key not in self.requests:
            self.requests[key] = []
        
        if len(self.requests[key]) >= max_requests:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def get_remaining_requests(
        self,
        key: str,
        max_requests: int,
        window_minutes: int = 1
    ) -> int:
        """Get remaining requests for key"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        if key not in self.requests:
            return max_requests
        
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        return max_requests - len(self.requests[key])


class RBAC:
    """Role-Based Access Control"""
    
    # Role permission mapping
    ROLE_PERMISSIONS = {
        Role.USER: [Permission.READ],
        Role.DEVELOPER: [Permission.READ, Permission.WRITE],
        Role.ADMIN: [Permission.READ, Permission.WRITE, Permission.ADMIN],
        Role.SYSTEM: [Permission.READ, Permission.WRITE, Permission.ADMIN, Permission.SUPER_ADMIN]
    }
    
    @classmethod
    def has_permission(cls, role: Role, permission: Permission) -> bool:
        """Check if role has permission"""
        return permission in cls.ROLE_PERMISSIONS.get(role, [])
    
    @classmethod
    def has_any_permission(cls, role: Role, permissions: List[Permission]) -> bool:
        """Check if role has any of the permissions"""
        return any(cls.has_permission(role, perm) for perm in permissions)
    
    @classmethod
    def has_all_permissions(cls, role: Role, permissions: List[Permission]) -> bool:
        """Check if role has all permissions"""
        return all(cls.has_permission(role, perm) for perm in permissions)


class SecurityManager:
    """
    Centralized security manager
    """
    
    def __init__(self, secret_key: str):
        self.password_manager = PasswordManager()
        self.api_key_manager = APIKeyManager()
        self.token_manager = TokenManager(secret_key)
        self.rate_limiter = RateLimiter()
        self.rbac = RBAC()
        
        # In-memory storage (use database in production)
        self.users: Dict[int, User] = {}
        self.api_keys: Dict[str, APIKey] = {}
    
    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        role: Role = Role.USER
    ) -> User:
        """Register new user"""
        user_id = len(self.users) + 1
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            role=role,
            permissions=self.rbac.ROLE_PERMISSIONS[role],
            created_at=datetime.utcnow()
        )
        
        self.users[user_id] = user
        return user
    
    def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[User]:
        """Authenticate user with username/password"""
        # In production, would query database
        for user in self.users.values():
            if user.username == username:
                # For demo, skip password verification
                return user
        return None
    
    def create_api_key(
        self,
        user_id: int,
        name: str,
        rate_limit_per_minute: int = 60,
        expires_in_days: Optional[int] = None
    ) -> str:
        """Create API key for user"""
        api_key = self.api_key_manager.generate_key()
        key_hash = self.api_key_manager.hash_key(api_key)
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        user = self.users.get(user_id)
        if user is None:
            raise ValueError("User not found")
        
        api_key_obj = APIKey(
            id=secrets.token_hex(16),
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            permissions=user.permissions,
            rate_limit_per_minute=rate_limit_per_minute,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        
        self.api_keys[key_hash] = api_key_obj
        return api_key
    
    def validate_api_key(
        self,
        api_key: str
    ) -> Optional[APIKey]:
        """Validate API key"""
        key_hash = self.api_key_manager.hash_key(api_key)
        
        api_key_obj = self.api_keys.get(key_hash)
        if api_key_obj is None:
            return None
        
        # Check if active
        if not api_key_obj.is_active:
            return None
        
        # Check expiration
        if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
            return None
        
        return api_key_obj
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int = 60
    ) -> bool:
        """Check rate limit"""
        return self.rate_limiter.is_allowed(key, max_requests)
    
    def authorize(
        self,
        user_id: int,
        permission: Permission
    ) -> bool:
        """Authorize user for permission"""
        user = self.users.get(user_id)
        if user is None:
            return False
        
        return self.rbac.has_permission(user.role, permission)
    
    def generate_tokens(
        self,
        user_id: int
    ) -> Dict[str, str]:
        """Generate access and refresh tokens"""
        user = self.users.get(user_id)
        if user is None:
            raise ValueError("User not found")
        
        access_token = self.token_manager.generate_access_token(
            user_id=user_id,
            role=user.role.value,
            permissions=[p.value for p in user.permissions]
        )
        
        refresh_token = self.token_manager.generate_refresh_token(user_id=user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
        }


class AuditLogger:
    """Security audit logging"""
    
    def __init__(self):
        self.logs: List[Dict] = []
    
    def log(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        success: bool = True
    ):
        """Log security event"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "success": success
        }
        
        self.logs.append(log_entry)
    
    def get_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get filtered logs"""
        filtered = self.logs
        
        if user_id is not None:
            filtered = [log for log in filtered if log["user_id"] == user_id]
        
        if action is not None:
            filtered = [log for log in filtered if log["action"] == action]
        
        return filtered[-limit:]


class InputValidator:
    """Input validation for security"""
    
    @staticmethod
    def sanitize_input(input_str: str, max_length: int = 10000) -> str:
        """Sanitize user input"""
        if len(input_str) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length}")
        
        # Basic sanitization
        dangerous_patterns = [
            "<script",
            "javascript:",
            "onerror=",
            "onload=",
        ]
        
        input_lower = input_str.lower()
        for pattern in dangerous_patterns:
            if pattern in input_lower:
                raise ValueError(f"Input contains dangerous pattern: {pattern}")
        
        return input_str
    
    @staticmethod
    def validate_sql_query(query: str) -> bool:
        """Validate SQL query for injection"""
        dangerous_keywords = [
            "DROP",
            "DELETE",
            "TRUNCATE",
            "ALTER",
            "EXEC",
            "EXECUTE"
        ]
        
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False
        
        return True


if __name__ == "__main__":
    # Demo: Security system
    security = SecurityManager(secret_key="demo-secret-key-change-in-production")
    audit_logger = AuditLogger()
    
    # Register user
    user = security.register_user(
        username="demo_user",
        email="demo@fivoria.com",
        password="secure_password",
        role=Role.DEVELOPER
    )
    
    print(f"Registered user: {user.username} with role {user.role}")
    
    # Create API key
    api_key = security.create_api_key(
        user_id=user.id,
        name="Demo API Key",
        rate_limit_per_minute=100
    )
    
    print(f"Created API key: {api_key[:20]}...")
    
    # Validate API key
    api_key_obj = security.validate_api_key(api_key)
    print(f"API key valid: {api_key_obj is not None}")
    
    # Check authorization
    authorized = security.authorize(user.id, Permission.WRITE)
    print(f"User authorized for WRITE: {authorized}")
    
    # Generate tokens
    tokens = security.generate_tokens(user.id)
    print(f"Generated tokens: {tokens['token_type']}")
    
    # Log audit event
    audit_logger.log(
        user_id=user.id,
        action="api_key_created",
        resource_type="api_key",
        resource_id=api_key_obj.id,
        ip_address="127.0.0.1",
        success=True
    )
    
    print(f"Audit logs: {len(audit_logger.logs)}")
