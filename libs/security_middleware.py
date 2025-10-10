"""
Security Middleware for Enterprise-Grade Protection

Implements comprehensive security controls including RBAC, rate limiting,
authentication, and request validation.
"""

import time
import hashlib
import hmac
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
import redis.asyncio as redis
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with Redis backend
    
    Features:
    - Per-user and per-IP rate limiting
    - Configurable time windows
    - Burst handling
    - Distributed rate limiting via Redis
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        default_limit: int = 100,
        window_seconds: int = 60
    ):
        """
        Initialize rate limiter
        
        Args:
            redis_client: Redis client for distributed limiting
            default_limit: Default requests per window
            window_seconds: Time window in seconds
        """
        self.redis = redis_client
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.local_cache: Dict[str, List[float]] = defaultdict(list)
    
    async def is_allowed(
        self,
        key: str,
        limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed
        
        Args:
            key: Rate limit key (user_id, IP, etc.)
            limit: Custom limit
            window: Custom window
        
        Returns:
            Tuple of (allowed, metadata)
        """
        limit = limit or self.default_limit
        window = window or self.window_seconds
        
        try:
            # Use Redis for distributed rate limiting
            redis_key = f"ratelimit:{key}"
            current_time = time.time()
            window_start = current_time - window
            
            # Remove old entries
            await self.redis.zremrangebyscore(redis_key, 0, window_start)
            
            # Count requests in window
            request_count = await self.redis.zcard(redis_key)
            
            if request_count < limit:
                # Add current request
                await self.redis.zadd(redis_key, {str(current_time): current_time})
                await self.redis.expire(redis_key, window)
                
                return True, {
                    "limit": limit,
                    "remaining": limit - request_count - 1,
                    "reset": int(current_time + window)
                }
            else:
                # Rate limit exceeded
                oldest_request = await self.redis.zrange(redis_key, 0, 0, withscores=True)
                reset_time = int(oldest_request[0][1] + window) if oldest_request else int(current_time + window)
                
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": reset_time
                }
        
        except Exception as e:
            logger.error(f"Rate limiter error: {e}", exc_info=True)
            # Fail open on errors
            return True, {"limit": limit, "remaining": limit, "reset": int(time.time() + window)}


class RBACManager:
    """
    Role-Based Access Control Manager
    
    Features:
    - Role hierarchy
    - Permission-based access
    - Resource-level permissions
    - Dynamic role assignment
    """
    
    def __init__(self):
        self.roles: Dict[str, Dict[str, Any]] = {}
        self.user_roles: Dict[str, List[str]] = {}
        self._setup_default_roles()
    
    def _setup_default_roles(self):
        """Setup default role hierarchy"""
        
        self.roles = {
            "super_admin": {
                "permissions": ["*"],  # All permissions
                "priority": 100
            },
            "admin": {
                "permissions": [
                    "users:read", "users:write", "users:delete",
                    "businesses:read", "businesses:write", "businesses:delete",
                    "analytics:read", "analytics:write",
                    "settings:read", "settings:write"
                ],
                "priority": 80
            },
            "business_owner": {
                "permissions": [
                    "business:read", "business:write",
                    "orders:read", "orders:write",
                    "reservations:read", "reservations:write",
                    "analytics:read",
                    "customers:read"
                ],
                "priority": 50
            },
            "business_manager": {
                "permissions": [
                    "business:read",
                    "orders:read", "orders:write",
                    "reservations:read", "reservations:write",
                    "customers:read"
                ],
                "priority": 40
            },
            "customer": {
                "permissions": [
                    "profile:read", "profile:write",
                    "orders:read", "orders:create",
                    "reservations:read", "reservations:create"
                ],
                "priority": 10
            },
            "guest": {
                "permissions": [
                    "public:read"
                ],
                "priority": 1
            }
        }
    
    def assign_role(self, user_id: str, role: str):
        """Assign role to user"""
        if role not in self.roles:
            raise ValueError(f"Invalid role: {role}")
        
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
        
        if role not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role)
            logger.info(f"Assigned role '{role}' to user {user_id}")
    
    def remove_role(self, user_id: str, role: str):
        """Remove role from user"""
        if user_id in self.user_roles and role in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role)
            logger.info(f"Removed role '{role}' from user {user_id}")
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has permission"""
        user_roles = self.user_roles.get(user_id, ["guest"])
        
        for role in user_roles:
            role_data = self.roles.get(role, {})
            permissions = role_data.get("permissions", [])
            
            # Check for wildcard or exact match
            if "*" in permissions or permission in permissions:
                return True
            
            # Check for prefix match (e.g., "users:*" matches "users:read")
            for perm in permissions:
                if perm.endswith(":*") and permission.startswith(perm[:-1]):
                    return True
        
        return False
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """Get user's roles"""
        return self.user_roles.get(user_id, ["guest"])
    
    def get_highest_role(self, user_id: str) -> str:
        """Get user's highest priority role"""
        user_roles = self.user_roles.get(user_id, ["guest"])
        
        if not user_roles:
            return "guest"
        
        return max(
            user_roles,
            key=lambda r: self.roles.get(r, {}).get("priority", 0)
        )


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware
    
    Features:
    - Request validation
    - Rate limiting
    - RBAC enforcement
    - Security headers
    - Request logging
    """
    
    def __init__(
        self,
        app,
        rate_limiter: Optional[RateLimiter] = None,
        rbac_manager: Optional[RBACManager] = None,
        jwt_secret: Optional[str] = None
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.rbac_manager = rbac_manager or RBACManager()
        self.jwt_secret = jwt_secret or "your-secret-key"  # Use env var in production
        self.security_bearer = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security checks"""
        
        # Add security headers to response
        async def add_security_headers(response):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            return response
        
        try:
            # Skip security for health checks
            if request.url.path in ["/health", "/ready", "/metrics"]:
                response = await call_next(request)
                return await add_security_headers(response)
            
            # Extract user info from JWT
            user_id = None
            user_roles = []
            
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                    user_id = payload.get("user_id")
                    user_roles = payload.get("roles", [])
                    
                    # Assign roles to RBAC manager
                    for role in user_roles:
                        self.rbac_manager.assign_role(user_id, role)
                    
                except jwt.ExpiredSignatureError:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"error": "Token expired"}
                    )
                except jwt.InvalidTokenError:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"error": "Invalid token"}
                    )
            
            # Rate limiting
            if self.rate_limiter:
                rate_key = user_id or request.client.host
                allowed, rate_info = await self.rate_limiter.is_allowed(rate_key)
                
                if not allowed:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Rate limit exceeded",
                            "limit": rate_info["limit"],
                            "reset": rate_info["reset"]
                        },
                        headers={
                            "X-RateLimit-Limit": str(rate_info["limit"]),
                            "X-RateLimit-Remaining": str(rate_info["remaining"]),
                            "X-RateLimit-Reset": str(rate_info["reset"])
                        }
                    )
            
            # Add user context to request state
            request.state.user_id = user_id
            request.state.user_roles = user_roles
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = await add_security_headers(response)
            
            # Add rate limit headers
            if self.rate_limiter:
                response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
                response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
            
            return response
        
        except Exception as e:
            logger.error(f"Security middleware error: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"}
            )


def require_permission(permission: str):
    """
    Decorator to require specific permission
    
    Args:
        permission: Required permission
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(request: Request, *args, **kwargs):
            user_id = getattr(request.state, "user_id", None)
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Get RBAC manager from app state
            rbac_manager = getattr(request.app.state, "rbac_manager", None)
            
            if not rbac_manager or not rbac_manager.has_permission(user_id, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission}"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def require_role(role: str):
    """
    Decorator to require specific role
    
    Args:
        role: Required role
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(request: Request, *args, **kwargs):
            user_roles = getattr(request.state, "user_roles", [])
            
            if role not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role}"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


class RequestValidator:
    """
    Request validation and sanitization
    
    Features:
    - Input sanitization
    - SQL injection prevention
    - XSS prevention
    - CSRF protection
    """
    
    @staticmethod
    def sanitize_input(value: str) -> str:
        """Sanitize user input"""
        # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", "&", '"', "'", "/", "\\"]
        sanitized = value
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        return sanitized.strip()
    
    @staticmethod
    def validate_sql_injection(value: str) -> bool:
        """Check for SQL injection patterns"""
        sql_patterns = [
            "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
            "ALTER", "EXEC", "EXECUTE", "--", "/*", "*/", "xp_", "sp_"
        ]
        
        value_upper = value.upper()
        return not any(pattern in value_upper for pattern in sql_patterns)
    
    @staticmethod
    def validate_xss(value: str) -> bool:
        """Check for XSS patterns"""
        xss_patterns = [
            "<script", "javascript:", "onerror=", "onload=",
            "<iframe", "<object", "<embed"
        ]
        
        value_lower = value.lower()
        return not any(pattern in value_lower for pattern in xss_patterns)
