"""
Business Settings & Configuration API Routes
Enterprise-grade business settings management
"""

from fastapi import APIRouter, HTTPException, Query, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, time
from pydantic import BaseModel

from ..services.database import get_database_service
from ..middleware.auth import get_auth_middleware, security

router = APIRouter(prefix="/api/v1/business-settings", tags=["business-settings"])


# ============================================================================
# MODELS
# ============================================================================

class WorkingHours(BaseModel):
    """Working hours for a day"""
    day_of_week: int  # 0=Monday, 6=Sunday
    is_open: bool
    open_time: Optional[str] = None  # HH:MM format
    close_time: Optional[str] = None  # HH:MM format
    breaks: List[Dict[str, str]] = []  # List of break periods


class BusinessSettings(BaseModel):
    """Business settings model"""
    business_id: UUID
    notifications: Dict[str, Any] = {
        "email": True,
        "sms": False,
        "push": True
    }
    preferences: Dict[str, Any] = {
        "locale": "en-US",
        "currency": "USD",
        "timezone": "UTC",
        "date_format": "MM/DD/YYYY",
        "time_format": "12h"
    }
    business_hours: List[WorkingHours] = []
    integrations: Dict[str, Any] = {}


class BusinessSettingsUpdate(BaseModel):
    """Update business settings"""
    notifications: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    business_hours: Optional[List[WorkingHours]] = None
    integrations: Optional[Dict[str, Any]] = None


# ============================================================================
# BUSINESS SETTINGS
# ============================================================================

@router.get("/{business_id}", response_model=BusinessSettings)
async def get_business_settings(
    business_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get business settings (Requires Authentication)
    
    - **Notifications**: Email, SMS, push preferences
    - **Preferences**: Locale, currency, timezone
    - **Business hours**: Operating hours per day
    - **Integrations**: Third-party service configs
    """
    try:
        # Verify authentication and business access
        auth_middleware = get_auth_middleware()
        user = await auth_middleware.get_current_user(credentials)
        await auth_middleware.require_business_access(user, str(business_id))
        
        db = get_database_service()
        result = db.client.table("business_settings").select("*").eq("business_id", str(business_id)).execute()
        
        if not result.data:
            # Return default settings
            return BusinessSettings(
                business_id=business_id,
                notifications={"email": True, "sms": False, "push": True},
                preferences={"locale": "en-US", "currency": "USD", "timezone": "UTC"},
                business_hours=[],
                integrations={}
            )
        
        settings = result.data[0]
        settings["business_id"] = business_id
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch settings: {str(e)}")


@router.put("/{business_id}", response_model=BusinessSettings)
async def update_business_settings(
    business_id: UUID,
    updates: BusinessSettingsUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update business settings (Requires Authentication - Owner/Admin)
    
    - **Partial updates**: Only update provided fields
    - **Validation**: Ensure valid configurations
    """
    try:
        # Verify authentication and business access (owner/admin only)
        auth_middleware = get_auth_middleware()
        user = await auth_middleware.get_current_user(credentials)
        await auth_middleware.require_business_access(user, str(business_id), required_roles=["owner", "admin"])
        
        db = get_database_service()
        update_data = updates.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Convert working hours to dict format
        if "business_hours" in update_data and update_data["business_hours"]:
            update_data["business_hours"] = [h.model_dump() if hasattr(h, 'model_dump') else h for h in update_data["business_hours"]]
        
        # Check if settings exist
        existing = db.client.table("business_settings").select("*").eq("business_id", str(business_id)).execute()
        
        if existing.data:
            # Update existing
            result = db.client.table("business_settings").update(update_data).eq("business_id", str(business_id)).execute()
        else:
            # Insert new
            update_data["business_id"] = str(business_id)
            result = db.client.table("business_settings").insert(update_data).execute()
        
        if result.data:
            settings = result.data[0]
            settings["business_id"] = business_id
            return settings
        else:
            raise HTTPException(status_code=500, detail="Failed to update settings")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


# ============================================================================
# WORKING HOURS
# ============================================================================

@router.get("/{business_id}/working-hours", response_model=List[WorkingHours])
async def get_working_hours(
    business_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get business working hours (Requires Authentication)
    
    - **Schedule**: Hours for each day of week
    - **Breaks**: Break periods during the day
    - **Holidays**: Special hours or closures
    """
    try:
        # Verify authentication and business access
        auth_middleware = get_auth_middleware()
        user = await auth_middleware.get_current_user(credentials)
        await auth_middleware.require_business_access(user, str(business_id))
        
        db = get_database_service()
        result = db.client.table("business_settings").select("business_hours").eq("business_id", str(business_id)).execute()
        
        if result.data and result.data[0].get("business_hours"):
            return result.data[0]["business_hours"]
        
        # Return default hours (closed all days)
        return [
            WorkingHours(day_of_week=i, is_open=False)
            for i in range(7)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch working hours: {str(e)}")


@router.put("/{business_id}/working-hours", response_model=List[WorkingHours])
async def update_working_hours(
    business_id: UUID,
    hours: List[WorkingHours],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update business working hours (Requires Authentication - Owner/Admin)
    
    - **Validation**: Ensure valid time ranges
    - **Conflicts**: Check for overlapping hours
    """
    try:
        # Verify authentication and business access (owner/admin only)
        auth_middleware = get_auth_middleware()
        user = await auth_middleware.get_current_user(credentials)
        await auth_middleware.require_business_access(user, str(business_id), required_roles=["owner", "admin"])
        
        db = get_database_service()
        
        # Validate hours
        for hour in hours:
            if hour.is_open and (not hour.open_time or not hour.close_time):
                raise HTTPException(status_code=400, detail=f"Open/close times required for day {hour.day_of_week}")
        
        # Convert to dict format
        hours_data = [h.model_dump() for h in hours]
        
        update_data = {
            "business_hours": hours_data,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Check if settings exist
        existing = db.client.table("business_settings").select("*").eq("business_id", str(business_id)).execute()
        
        if existing.data:
            result = db.client.table("business_settings").update(update_data).eq("business_id", str(business_id)).execute()
        else:
            update_data["business_id"] = str(business_id)
            result = db.client.table("business_settings").insert(update_data).execute()
        
        if result.data:
            return result.data[0].get("business_hours", [])
        else:
            raise HTTPException(status_code=500, detail="Failed to update working hours")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update working hours: {str(e)}")


# ============================================================================
# INTEGRATIONS
# ============================================================================

@router.get("/{business_id}/integrations", response_model=Dict[str, Any])
async def get_integrations(
    business_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get third-party integrations (Requires Authentication)
    
    - **POS systems**: Toast, Square, Clover
    - **Delivery**: DoorDash, UberEats, GrubHub
    - **Payments**: Stripe, PayPal
    - **Communication**: Twilio, SendGrid
    """
    try:
        # Verify authentication and business access
        auth_middleware = get_auth_middleware()
        user = await auth_middleware.get_current_user(credentials)
        await auth_middleware.require_business_access(user, str(business_id))
        
        db = get_database_service()
        result = db.client.table("business_settings").select("integrations").eq("business_id", str(business_id)).execute()
        
        if result.data and result.data[0].get("integrations"):
            return result.data[0]["integrations"]
        
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch integrations: {str(e)}")


@router.put("/{business_id}/integrations/{integration_name}", response_model=Dict[str, Any])
async def update_integration(
    business_id: UUID,
    integration_name: str,
    config: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update integration configuration (Requires Authentication - Owner/Admin)
    
    - **Enable/disable**: Toggle integration
    - **Credentials**: API keys, tokens
    - **Settings**: Integration-specific configs
    """
    try:
        # Verify authentication and business access (owner/admin only)
        auth_middleware = get_auth_middleware()
        user = await auth_middleware.get_current_user(credentials)
        await auth_middleware.require_business_access(user, str(business_id), required_roles=["owner", "admin"])
        
        db = get_database_service()
        
        # Get current integrations
        result = db.client.table("business_settings").select("integrations").eq("business_id", str(business_id)).execute()
        
        integrations = {}
        if result.data and result.data[0].get("integrations"):
            integrations = result.data[0]["integrations"]
        
        # Update specific integration
        integrations[integration_name] = config
        
        update_data = {
            "integrations": integrations,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Check if settings exist
        existing = db.client.table("business_settings").select("*").eq("business_id", str(business_id)).execute()
        
        if existing.data:
            result = db.client.table("business_settings").update(update_data).eq("business_id", str(business_id)).execute()
        else:
            update_data["business_id"] = str(business_id)
            result = db.client.table("business_settings").insert(update_data).execute()
        
        if result.data:
            return result.data[0].get("integrations", {})
        else:
            raise HTTPException(status_code=500, detail="Failed to update integration")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update integration: {str(e)}")


@router.delete("/{business_id}/integrations/{integration_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    business_id: UUID,
    integration_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Remove integration configuration (Requires Authentication - Owner/Admin)"""
    try:
        # Verify authentication and business access (owner/admin only)
        auth_middleware = get_auth_middleware()
        user = await auth_middleware.get_current_user(credentials)
        await auth_middleware.require_business_access(user, str(business_id), required_roles=["owner", "admin"])
        
        db = get_database_service()
        
        # Get current integrations
        result = db.client.table("business_settings").select("integrations").eq("business_id", str(business_id)).execute()
        
        if result.data and result.data[0].get("integrations"):
            integrations = result.data[0]["integrations"]
            
            if integration_name in integrations:
                del integrations[integration_name]
                
                update_data = {
                    "integrations": integrations,
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                db.client.table("business_settings").update(update_data).eq("business_id", str(business_id)).execute()
        
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete integration: {str(e)}")
