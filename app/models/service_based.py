"""
Pydantic models for Service-Based Template
(Salon, Spa, Barbershop, Nail Salon, Massage Therapy, Fitness Gym, etc.)
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID


# ============================================================================
# SERVICES MODELS
# ============================================================================

class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    duration_minutes: int = Field(..., gt=0)
    price: float = Field(..., ge=0)
    category: Optional[str] = None
    is_active: bool = True
    staff_ids: Optional[List[UUID]] = []
    image_url: Optional[str] = None
    metadata: Optional[dict] = {}


class ServiceCreate(ServiceBase):
    business_id: UUID


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    price: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    is_active: Optional[bool] = None
    staff_ids: Optional[List[UUID]] = None
    image_url: Optional[str] = None
    metadata: Optional[dict] = None


class ServiceResponse(ServiceBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# APPOINTMENTS MODELS
# ============================================================================

class AppointmentBase(BaseModel):
    service_id: Optional[UUID] = None
    client_id: UUID
    staff_id: Optional[UUID] = None
    scheduled_time: datetime
    end_time: datetime
    duration_minutes: int = Field(..., gt=0)
    status: str = Field(default="scheduled", pattern="^(scheduled|confirmed|in_progress|completed|cancelled|no_show)$")
    notes: Optional[str] = None
    reminder_sent: bool = False
    metadata: Optional[dict] = {}


class AppointmentCreate(AppointmentBase):
    business_id: UUID


class AppointmentUpdate(BaseModel):
    service_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    scheduled_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    status: Optional[str] = Field(None, pattern="^(scheduled|confirmed|in_progress|completed|cancelled|no_show)$")
    notes: Optional[str] = None
    reminder_sent: Optional[bool] = None
    metadata: Optional[dict] = None


class AppointmentResponse(AppointmentBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CLIENTS MODELS
# ============================================================================

class ClientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    preferences: Optional[dict] = {}
    notes: Optional[str] = None
    tags: Optional[List[str]] = []
    is_active: bool = True


class ClientCreate(ClientBase):
    business_id: UUID


class ClientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    preferences: Optional[dict] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ClientResponse(ClientBase):
    id: UUID
    business_id: UUID
    total_visits: int = 0
    total_spent: float = 0
    last_visit_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CLIENT HISTORY
# ============================================================================

class ClientHistoryResponse(BaseModel):
    client: ClientResponse
    appointments: List[AppointmentResponse]
    total_appointments: int
    total_spent: float
    last_visit: Optional[datetime]
    favorite_services: List[dict]
