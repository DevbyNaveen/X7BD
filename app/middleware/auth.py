"""
Authentication Middleware for Dashboard Service

Validates JWT tokens from auth-service and extracts user context.
Supports both direct Supabase auth and backend token validation.
"""

import logging
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

security = HTTPBearer(auto_error=False)


def get_supabase_client(use_service_key: bool = False) -> Client:
    """Get Supabase client instance"""
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL not configured")
    
    key = SUPABASE_SERVICE_KEY if use_service_key else SUPABASE_ANON_KEY
    if not key:
        raise ValueError("Supabase key not configured")
    
    return create_client(SUPABASE_URL, key)


class AuthMiddleware:
    """Authentication middleware for validating tokens"""
    
    def __init__(self):
        self.supabase = get_supabase_client(use_service_key=True)
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token with Supabase
        
        Args:
            token: JWT access token
            
        Returns:
            User data from token
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Verify token with Supabase
            user_response = self.supabase.auth.get_user(token)
            
            if not user_response or not user_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            user = user_response.user
            
            # Get additional user profile data
            profile_result = self.supabase.table("users").select("*").eq("id", user.id).execute()
            profile = profile_result.data[0] if profile_result.data else {}
            
            # Get user's business roles
            roles_result = self.supabase.table("user_business_roles").select("*").eq("user_id", user.id).execute()
            business_roles = roles_result.data if roles_result.data else []
            
            return {
                "id": user.id,
                "email": user.email,
                "full_name": profile.get("full_name"),
                "avatar_url": profile.get("avatar_url"),
                "phone_number": user.phone,
                "email_confirmed": bool(user.email_confirmed_at),
                "business_roles": business_roles,
                "created_at": str(user.created_at),
                "last_sign_in_at": str(user.last_sign_in_at) if user.last_sign_in_at else None
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    async def get_current_user(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = None
    ) -> Dict[str, Any]:
        """
        Get current authenticated user from request
        
        Args:
            credentials: HTTP authorization credentials
            
        Returns:
            Current user data
            
        Raises:
            HTTPException: If authentication fails
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return await self.verify_token(credentials.credentials)
    
    async def require_business_access(
        self,
        user: Dict[str, Any],
        business_id: str,
        required_roles: Optional[list] = None
    ) -> bool:
        """
        Check if user has access to a specific business
        
        Args:
            user: User data from token
            business_id: Business ID to check access for
            required_roles: Optional list of required roles (owner, admin, staff)
            
        Returns:
            True if user has access
            
        Raises:
            HTTPException: If user doesn't have access
        """
        business_roles = user.get("business_roles", [])
        
        # Check if user has any role in this business
        user_role = None
        for role in business_roles:
            if role.get("business_id") == business_id:
                user_role = role.get("role")
                break
        
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this business"
            )
        
        # Check if user has required role
        if required_roles and user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {', '.join(required_roles)}"
            )
        
        return True


# Singleton instance
_auth_middleware: Optional[AuthMiddleware] = None


def get_auth_middleware() -> AuthMiddleware:
    """Get auth middleware singleton"""
    global _auth_middleware
    if _auth_middleware is None:
        _auth_middleware = AuthMiddleware()
    return _auth_middleware
