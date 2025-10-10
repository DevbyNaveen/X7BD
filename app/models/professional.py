"""
Pydantic models for Professional Services Template
(Law Firm, Accounting Firm, Consulting, Marketing Agency, Real Estate, etc.)
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID


# ============================================================================
# PROJECTS MODELS
# ============================================================================

class ProjectBase(BaseModel):
    client_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_number: Optional[str] = Field(None, max_length=100)
    status: str = Field(default="active", pattern="^(active|on_hold|completed|cancelled)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    hourly_rate: Optional[float] = Field(None, ge=0)
    budget: Optional[float] = Field(None, ge=0)
    assigned_staff: Optional[List[UUID]] = []
    tags: Optional[List[str]] = []
    metadata: Optional[dict] = {}


class ProjectCreate(ProjectBase):
    business_id: UUID


class ProjectUpdate(BaseModel):
    client_id: Optional[UUID] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    project_number: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, pattern="^(active|on_hold|completed|cancelled)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    hourly_rate: Optional[float] = Field(None, ge=0)
    budget: Optional[float] = Field(None, ge=0)
    assigned_staff: Optional[List[UUID]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class ProjectResponse(ProjectBase):
    id: UUID
    business_id: UUID
    actual_hours: float = 0
    total_cost: float = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TIME ENTRIES MODELS
# ============================================================================

class TimeEntryBase(BaseModel):
    project_id: Optional[UUID] = None
    staff_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_hours: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    billable: bool = True
    hourly_rate: Optional[float] = Field(None, ge=0)
    status: str = Field(default="draft", pattern="^(draft|submitted|approved|invoiced)$")
    metadata: Optional[dict] = {}


class TimeEntryCreate(TimeEntryBase):
    business_id: UUID


class TimeEntryUpdate(BaseModel):
    project_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_hours: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    billable: Optional[bool] = None
    hourly_rate: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(draft|submitted|approved|invoiced)$")
    metadata: Optional[dict] = None


class TimeEntryResponse(TimeEntryBase):
    id: UUID
    business_id: UUID
    total_amount: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# INVOICES MODELS
# ============================================================================

class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    amount: float = Field(..., ge=0)


class InvoiceBase(BaseModel):
    client_id: UUID
    project_id: Optional[UUID] = None
    invoice_number: str = Field(..., min_length=1, max_length=100)
    status: str = Field(default="draft", pattern="^(draft|sent|paid|overdue|cancelled)$")
    issue_date: date
    due_date: date
    subtotal: float = Field(..., ge=0)
    tax_amount: float = Field(default=0, ge=0)
    discount_amount: float = Field(default=0, ge=0)
    total_amount: float = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=10)
    line_items: List[InvoiceLineItem]
    notes: Optional[str] = None
    terms: Optional[str] = None
    payment_method: Optional[str] = None
    metadata: Optional[dict] = {}


class InvoiceCreate(InvoiceBase):
    business_id: UUID


class InvoiceUpdate(BaseModel):
    client_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    invoice_number: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = Field(None, pattern="^(draft|sent|paid|overdue|cancelled)$")
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    subtotal: Optional[float] = Field(None, ge=0)
    tax_amount: Optional[float] = Field(None, ge=0)
    discount_amount: Optional[float] = Field(None, ge=0)
    total_amount: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    line_items: Optional[List[InvoiceLineItem]] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    payment_method: Optional[str] = None
    metadata: Optional[dict] = None


class InvoiceResponse(InvoiceBase):
    id: UUID
    business_id: UUID
    amount_paid: float = 0
    amount_due: Optional[float] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# RESOURCES MODELS
# ============================================================================

class ResourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    status: str = Field(default="available", pattern="^(available|in_use|maintenance|unavailable)$")
    location: Optional[str] = Field(None, max_length=255)
    cost_per_hour: Optional[float] = Field(None, ge=0)
    metadata: Optional[dict] = {}


class ResourceCreate(ResourceBase):
    business_id: UUID


class ResourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(available|in_use|maintenance|unavailable)$")
    location: Optional[str] = Field(None, max_length=255)
    cost_per_hour: Optional[float] = Field(None, ge=0)
    metadata: Optional[dict] = None


class ResourceResponse(ResourceBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# RESOURCE ALLOCATIONS MODELS
# ============================================================================

class ResourceAllocationBase(BaseModel):
    resource_id: UUID
    project_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None


class ResourceAllocationCreate(ResourceAllocationBase):
    business_id: UUID


class ResourceAllocationUpdate(BaseModel):
    resource_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None


class ResourceAllocationResponse(ResourceAllocationBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
