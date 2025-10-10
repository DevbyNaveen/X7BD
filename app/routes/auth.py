"""
Authentication Routes for Dashboard Service

Handles business registration (direct Supabase) and login/usage (through backend).
Integrates with auth-service for token validation.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from uuid import UUID
import os
from datetime import datetime

from ..middleware.auth import get_auth_middleware, security, get_supabase_client

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# ============================================================================
# MODELS
# ============================================================================

class BusinessRegistration(BaseModel):
    """Business registration model"""
    # User details
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    phone_number: Optional[str] = None
    
    # Business details
    business_name: str = Field(..., min_length=2)
    business_type: str = Field(..., description="restaurant, salon, retail, etc.")
    business_email: Optional[EmailStr] = None
    business_phone: Optional[str] = None
    business_address: Optional[str] = None
    timezone: str = Field(default="UTC")
    currency: str = Field(default="USD")


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str
    remember_me: bool = False


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class PasswordUpdateRequest(BaseModel):
    """Password update request"""
    new_password: str = Field(..., min_length=8)


# ============================================================================
# BUSINESS REGISTRATION (Direct Supabase)
# ============================================================================

@router.post("/register/business", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def register_business(registration: BusinessRegistration):
    """
    Register a new business with owner account (Direct Supabase)
    
    Creates:
    - User account in Supabase Auth
    - User profile in users table
    - Business profile in businesses table
    - Owner role in user_business_roles table
    - Default business settings
    
    **Flow**: Frontend -> Dashboard Service -> Supabase (Direct)
    """
    try:
        supabase = get_supabase_client(use_service_key=True)
        
        # 1. Create user account in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": registration.email,
            "password": registration.password,
            "options": {
                "data": {
                    "full_name": registration.full_name,
                    "phone_number": registration.phone_number
                }
            }
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
        
        user_id = auth_response.user.id
        
        # 2. Create user profile
        user_profile = {
            "id": user_id,
            "full_name": registration.full_name,
            "phone_number": registration.phone_number,
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("users").insert(user_profile).execute()
        
        # 3. Create business profile
        business_data = {
            "name": registration.business_name,
            "business_type": registration.business_type,
            "owner_id": user_id,
            "email": registration.business_email or registration.email,
            "phone": registration.business_phone or registration.phone_number,
            "address": registration.business_address,
            "timezone": registration.timezone,
            "currency": registration.currency,
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
        business_result = supabase.table("businesses").insert(business_data).execute()
        
        if not business_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create business profile"
            )
        
        business = business_result.data[0]
        business_id = business["id"]
        
        # 4. Create owner role
        role_data = {
            "user_id": user_id,
            "business_id": business_id,
            "role": "owner",
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("user_business_roles").insert(role_data).execute()
        
        # 5. Create default business settings
        settings_data = {
            "business_id": business_id,
            "notifications": {
                "email": True,
                "sms": False,
                "push": True
            },
            "preferences": {
                "locale": "en-US",
                "currency": registration.currency,
                "timezone": registration.timezone,
                "date_format": "MM/DD/YYYY",
                "time_format": "12h"
            },
            "business_hours": [],
            "integrations": {},
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("business_settings").insert(settings_data).execute()
        
        # 6. Return response with tokens
        return {
            "message": "Business registered successfully",
            "user": {
                "id": user_id,
                "email": registration.email,
                "full_name": registration.full_name
            },
            "business": {
                "id": business_id,
                "name": registration.business_name,
                "business_type": registration.business_type,
                "status": "active"
            },
            "session": {
                "access_token": auth_response.session.access_token if auth_response.session else None,
                "refresh_token": auth_response.session.refresh_token if auth_response.session else None,
                "expires_in": auth_response.session.expires_in if auth_response.session else 3600
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


# ============================================================================
# LOGIN & AUTHENTICATION (Through Backend)
# ============================================================================

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """
    Authenticate user and return session tokens (Through Backend)
    
    **Flow**: Frontend -> Dashboard Service -> Supabase Auth -> Backend Validation
    """
    try:
        supabase = get_supabase_client()
        
        # Authenticate with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password
        })
        
        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Get user profile and business roles
        user_id = auth_response.user.id
        
        # Get user profile
        profile_result = supabase.table("users").select("*").eq("id", user_id).execute()
        profile = profile_result.data[0] if profile_result.data else {}
        
        # Get business roles
        roles_result = supabase.table("user_business_roles").select("*, businesses(*)").eq("user_id", user_id).execute()
        business_roles = roles_result.data if roles_result.data else []
        
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "token_type": "bearer",
            "expires_in": auth_response.session.expires_in,
            "user": {
                "id": user_id,
                "email": auth_response.user.email,
                "full_name": profile.get("full_name"),
                "avatar_url": profile.get("avatar_url"),
                "phone_number": auth_response.user.phone,
                "email_confirmed": bool(auth_response.user.email_confirmed_at),
                "businesses": [
                    {
                        "id": role.get("business_id"),
                        "name": role.get("businesses", {}).get("name"),
                        "role": role.get("role"),
                        "business_type": role.get("businesses", {}).get("business_type")
                    }
                    for role in business_roles
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(refresh_data: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    """
    try:
        supabase = get_supabase_client()
        
        # Refresh session with Supabase
        response = supabase.auth.refresh_session(refresh_data.refresh_token)
        
        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
            "expires_in": response.session.expires_in
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get current authenticated user profile
    
    Requires valid JWT token in Authorization header
    """
    auth_middleware = get_auth_middleware()
    user = await auth_middleware.get_current_user(credentials)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout current user and invalidate session
    """
    try:
        supabase = get_supabase_client()
        
        # Sign out from Supabase
        supabase.auth.sign_out()
        
        return None
        
    except Exception as e:
        # Log error but don't fail logout
        print(f"Logout error: {str(e)}")
        return None


# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================

@router.post("/password/reset-request")
async def request_password_reset(email: EmailStr):
    """
    Request password reset email
    """
    try:
        supabase = get_supabase_client()
        
        # Send password reset email
        supabase.auth.reset_password_email(email)
        
        return {
            "message": "If the email exists, a password reset link has been sent"
        }
        
    except Exception as e:
        # Don't reveal if email exists
        return {
            "message": "If the email exists, a password reset link has been sent"
        }


@router.post("/password/update")
async def update_password(
    password_data: PasswordUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update user password (requires authentication)
    """
    try:
        auth_middleware = get_auth_middleware()
        user = await auth_middleware.get_current_user(credentials)
        
        supabase = get_supabase_client(use_service_key=True)
        
        # Update password using admin API
        supabase.auth.admin.update_user_by_id(
            user["id"],
            {"password": password_data.new_password}
        )
        
        return {
            "message": "Password updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password update failed: {str(e)}"
        )
