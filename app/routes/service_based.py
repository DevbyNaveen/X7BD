"""
API Routes for Service-Based Template
(Salon, Spa, Barbershop, Nail Salon, Massage Therapy, Fitness Gym, etc.)

ENTERPRISE STRUCTURE:
- Common endpoints (customers, staff, time-clock) moved to universal routes
- Category-specific endpoints prefixed with /services
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..models.service_based import (
    ServiceCreate, ServiceUpdate, ServiceResponse,
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    ClientCreate, ClientUpdate, ClientResponse, ClientHistoryResponse
)
from ..services.database import get_database_service

router = APIRouter(prefix="/api/v1/service-based", tags=["Service-Based Template"])


# ============================================================================
# SERVICES ENDPOINTS
# ============================================================================

@router.post("/services", response_model=dict, status_code=201)
async def create_service_simple(service: dict):
    """Create a new service offering (simplified)"""
    db = get_database_service()
    
    try:
        result = db.client.table("services").insert({
            "business_id": str(service["business_id"]),
            "name": service["name"],
            "description": service.get("description"),
            "category": service.get("category"),
            "price": service["price"],
            "duration_minutes": service.get("duration", 60),
            "is_active": service.get("is_available", True)
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create service")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/offerings", response_model=ServiceResponse, status_code=201)
async def create_service(service: ServiceCreate):
    """Create a new service offering"""
    db = get_database_service()
    
    try:
        result = db.client.table("services").insert({
            "business_id": str(service.business_id),
            "name": service.name,
            "description": service.description,
            "duration_minutes": service.duration_minutes,
            "price": service.price,
            "category": service.category,
            "is_active": service.is_active,
            "staff_ids": [str(sid) for sid in service.staff_ids] if service.staff_ids else [],
            "image_url": service.image_url,
            "metadata": service.metadata
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create service")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services", response_model=list)
async def list_services_simple(business_id: UUID = Query(...)):
    """List all services for a business (simplified)"""
    db = get_database_service()
    
    try:
        result = db.client.table("services").select("*").eq("business_id", str(business_id)).execute()
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/service-categories", response_model=dict, status_code=201)
async def create_service_category_simple(category: dict):
    """Create service category (simplified)"""
    db = get_database_service()
    
    try:
        result = db.client.table("service_categories").insert({
            "business_id": str(category["business_id"]),
            "name": category["name"],
            "description": category.get("description"),
            "display_order": category.get("display_order", 0),
            "is_active": True
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create category")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/offerings", response_model=List[ServiceResponse])
async def list_services(
    business_id: UUID = Query(..., description="Business ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all service offerings for a business"""
    db = get_database_service()
    
    try:
        query = db.client.table("services").select("*").eq("business_id", str(business_id))
        
        if category:
            query = query.eq("category", category)
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        query = query.range(offset, offset + limit - 1).order("created_at", desc=True)
        result = query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/offerings/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: UUID):
    """Get a specific service offering by ID"""
    db = get_database_service()
    
    try:
        result = db.client.table("services").select("*").eq("id", str(service_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Service not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/offerings/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: UUID, service: ServiceUpdate):
    """Update a service offering"""
    db = get_database_service()
    
    try:
        # Build update data
        update_data = {k: v for k, v in service.dict(exclude_unset=True).items() if v is not None}
        
        if "staff_ids" in update_data and update_data["staff_ids"]:
            update_data["staff_ids"] = [str(sid) for sid in update_data["staff_ids"]]
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("services").update(update_data).eq("id", str(service_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Service not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/offerings/{service_id}", status_code=204)
async def delete_service(service_id: UUID):
    """Delete a service offering"""
    db = get_database_service()
    
    try:
        result = db.client.table("services").delete().eq("id", str(service_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Service not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# APPOINTMENTS ENDPOINTS
# ============================================================================

@router.post("/appointments", response_model=dict, status_code=201)
async def create_appointment_flexible(appointment: dict):
    """Create appointment (enterprise-grade flexible endpoint)"""
    db = get_database_service()
    
    try:
        # Enterprise-grade: Handle various input formats
        scheduled_time = appointment.get("scheduled_time") or appointment.get("appointment_date")
        client_id = appointment.get("client_id") or appointment.get("customer_id")
        
        # Calculate duration if not provided
        duration = appointment.get("duration_minutes") or appointment.get("duration") or 60
        
        # Handle end_time - if it's just a time string, combine with scheduled_time date
        end_time = appointment.get("end_time")
        if end_time and isinstance(end_time, str) and len(end_time) <= 8:  # Time only like "14:45:00"
            # Combine date from scheduled_time with the time
            from datetime import datetime
            if scheduled_time:
                date_part = scheduled_time.split('T')[0] if 'T' in scheduled_time else scheduled_time.split(' ')[0]
                end_time = f"{date_part}T{end_time}" if 'T' not in end_time else f"{date_part} {end_time}"
        
        insert_data = {
            "business_id": str(appointment["business_id"]),
            "service_id": str(appointment["service_id"]) if appointment.get("service_id") else None,
            "client_id": str(client_id) if client_id else None,
            "staff_id": str(appointment["staff_id"]) if appointment.get("staff_id") else None,
            "scheduled_time": scheduled_time,
            "end_time": end_time or scheduled_time,
            "duration_minutes": duration,
            "status": appointment.get("status", "pending"),
            "notes": appointment.get("notes"),
            "reminder_sent": appointment.get("reminder_sent", False)
        }
        
        result = db.client.table("appointments").insert(insert_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create appointment")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/appointments/strict", response_model=AppointmentResponse, status_code=201)
async def create_appointment(appointment: AppointmentCreate):
    """Create a new appointment (strict validation)"""
    db = get_database_service()
    
    try:
        result = db.client.table("appointments").insert({
            "business_id": str(appointment.business_id),
            "service_id": str(appointment.service_id) if appointment.service_id else None,
            "client_id": str(appointment.client_id),
            "staff_id": str(appointment.staff_id) if appointment.staff_id else None,
            "scheduled_time": appointment.scheduled_time.isoformat(),
            "end_time": appointment.end_time.isoformat(),
            "duration_minutes": appointment.duration_minutes,
            "status": appointment.status,
            "notes": appointment.notes,
            "reminder_sent": appointment.reminder_sent,
            "metadata": appointment.metadata
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create appointment")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/appointments", response_model=list)
async def list_appointments(
    business_id: UUID = Query(..., description="Business ID"),
    client_id: Optional[UUID] = Query(None, description="Filter by client"),
    staff_id: Optional[UUID] = Query(None, description="Filter by staff"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all appointments for a business"""
    db = get_database_service()
    
    try:
        query = db.client.table("appointments").select("*").eq("business_id", str(business_id))
        
        if client_id:
            query = query.eq("client_id", str(client_id))
        if staff_id:
            query = query.eq("staff_id", str(staff_id))
        if status:
            query = query.eq("status", status)
        if start_date:
            query = query.gte("scheduled_time", start_date.isoformat())
        if end_date:
            query = query.lte("scheduled_time", end_date.isoformat())
        
        query = query.range(offset, offset + limit - 1).order("scheduled_time", desc=True)
        result = query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(appointment_id: UUID):
    """Get a specific appointment by ID"""
    db = get_database_service()
    
    try:
        result = db.client.table("appointments").select("*").eq("id", str(appointment_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(appointment_id: UUID, appointment: AppointmentUpdate):
    """Update an appointment"""
    db = get_database_service()
    
    try:
        update_data = {k: v for k, v in appointment.dict(exclude_unset=True).items() if v is not None}
        
        # Convert UUIDs to strings
        for field in ["service_id", "client_id", "staff_id"]:
            if field in update_data and update_data[field]:
                update_data[field] = str(update_data[field])
        
        # Convert datetime to ISO format
        for field in ["scheduled_time", "end_time"]:
            if field in update_data and update_data[field]:
                update_data[field] = update_data[field].isoformat()
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("appointments").update(update_data).eq("id", str(appointment_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/appointments/{appointment_id}", status_code=204)
async def delete_appointment(appointment_id: UUID):
    """Cancel/Delete an appointment"""
    db = get_database_service()
    
    try:
        result = db.client.table("appointments").delete().eq("id", str(appointment_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NOTE: Client/Customer management moved to universal /api/v1/customers
# This eliminates duplication across templates
# ============================================================================


# ============================================================================
# SERVICE PACKAGES ENDPOINTS
# ============================================================================

@router.post("/packages", response_model=dict, status_code=201)
async def create_service_package(package: dict):
    """
    Create a service package (bundle multiple services)
    
    Example: "Spa Day Package" includes massage + facial + manicure
    """
    db = get_database_service()
    
    try:
        result = db.client.table("service_packages").insert({
            "business_id": str(package["business_id"]),
            "name": package["name"],
            "description": package.get("description"),
            "service_ids": [str(sid) for sid in package.get("service_ids", [])],
            "package_price": package["package_price"],
            "savings_amount": package.get("savings_amount", 0),
            "duration_minutes": package.get("duration_minutes"),
            "is_active": package.get("is_active", True),
            "valid_days": package.get("valid_days", 365),
            "metadata": package.get("metadata", {})
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create package")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packages", response_model=list)
async def list_service_packages(
    business_id: UUID = Query(..., description="Business ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all service packages"""
    db = get_database_service()
    
    try:
        query = db.client.table("service_packages").select("*").eq("business_id", str(business_id))
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        query = query.range(offset, offset + limit - 1).order("created_at", desc=True)
        result = await query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packages/{package_id}", response_model=dict)
async def get_service_package(package_id: UUID):
    """Get service package by ID"""
    db = get_database_service()
    
    try:
        result = db.client.table("service_packages").select("*").eq("id", str(package_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Package not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/packages/{package_id}", response_model=dict)
async def update_service_package(package_id: UUID, updates: dict):
    """Update service package"""
    db = get_database_service()
    
    try:
        update_data = {k: v for k, v in updates.items() if v is not None}
        
        if "service_ids" in update_data:
            update_data["service_ids"] = [str(sid) for sid in update_data["service_ids"]]
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("service_packages").update(update_data).eq("id", str(package_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Package not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/packages/{package_id}", status_code=204)
async def delete_service_package(package_id: UUID):
    """Delete service package"""
    db = get_database_service()
    
    try:
        result = db.client.table("service_packages").delete().eq("id", str(package_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Package not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MEMBERSHIP PLANS ENDPOINTS
# ============================================================================

@router.post("/memberships", response_model=dict, status_code=201)
async def create_membership_plan(membership: dict):
    """
    Create membership plan (monthly gym membership, salon VIP, etc.)
    """
    db = get_database_service()
    
    try:
        result = db.client.table("membership_plans").insert({
            "business_id": str(membership["business_id"]),
            "name": membership["name"],
            "description": membership.get("description"),
            "price": membership["price"],
            "billing_cycle": membership.get("billing_cycle", "monthly"),
            "duration_months": membership.get("duration_months"),
            "included_services": membership.get("included_services", []),
            "service_credits": membership.get("service_credits", 0),
            "discount_percentage": membership.get("discount_percentage", 0),
            "is_active": membership.get("is_active", True),
            "benefits": membership.get("benefits", []),
            "metadata": membership.get("metadata", {})
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create membership")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memberships", response_model=list)
async def list_membership_plans(
    business_id: UUID = Query(..., description="Business ID"),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all membership plans"""
    db = get_database_service()
    
    try:
        query = db.client.table("membership_plans").select("*").eq("business_id", str(business_id))
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        query = query.range(offset, offset + limit - 1).order("price")
        result = await query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memberships/{membership_id}", response_model=dict)
async def get_membership_plan(membership_id: UUID):
    """Get membership plan by ID"""
    db = get_database_service()
    
    try:
        result = db.client.table("membership_plans").select("*").eq("id", str(membership_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Membership not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/memberships/{membership_id}", response_model=dict)
async def update_membership_plan(membership_id: UUID, updates: dict):
    """Update membership plan"""
    db = get_database_service()
    
    try:
        update_data = {k: v for k, v in updates.items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("membership_plans").update(update_data).eq("id", str(membership_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Membership not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memberships/{membership_id}", status_code=204)
async def delete_membership_plan(membership_id: UUID):
    """Delete membership plan"""
    db = get_database_service()
    
    try:
        result = db.client.table("membership_plans").delete().eq("id", str(membership_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Membership not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CLASS/SESSION MANAGEMENT ENDPOINTS (for gyms, yoga studios)
# ============================================================================

@router.post("/classes", response_model=dict, status_code=201)
async def create_class_session(class_data: dict):
    """
    Create class/group session (yoga class, spin class, group training)
    """
    db = get_database_service()
    
    try:
        result = db.client.table("class_sessions").insert({
            "business_id": str(class_data["business_id"]),
            "name": class_data["name"],
            "description": class_data.get("description"),
            "instructor_id": str(class_data.get("instructor_id")) if class_data.get("instructor_id") else None,
            "max_capacity": class_data["max_capacity"],
            "duration_minutes": class_data["duration_minutes"],
            "price": class_data.get("price", 0),
            "recurring_schedule": class_data.get("recurring_schedule"),
            "start_time": class_data["start_time"],
            "end_time": class_data["end_time"],
            "room_id": str(class_data.get("room_id")) if class_data.get("room_id") else None,
            "is_active": class_data.get("is_active", True),
            "metadata": class_data.get("metadata", {})
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create class")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classes", response_model=list)
async def list_class_sessions(
    business_id: UUID = Query(..., description="Business ID"),
    instructor_id: Optional[UUID] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all class sessions"""
    db = get_database_service()
    
    try:
        query = db.client.table("class_sessions").select("*").eq("business_id", str(business_id))
        
        if instructor_id:
            query = query.eq("instructor_id", str(instructor_id))
        if start_date:
            query = query.gte("start_time", start_date.isoformat())
        if end_date:
            query = query.lte("start_time", end_date.isoformat())
        
        query = query.range(offset, offset + limit - 1).order("start_time")
        result = await query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classes/{class_id}/book", response_model=dict, status_code=201)
async def book_class_session(class_id: UUID, booking: dict):
    """Book a spot in a class session"""
    db = get_database_service()
    
    try:
        # Check capacity
        class_result = db.client.table("class_sessions").select("*").eq("id", str(class_id)).execute()
        
        if not class_result.data:
            raise HTTPException(status_code=404, detail="Class not found")
        
        class_data = class_result.data[0]
        
        # Check current bookings
        bookings_result = db.client.table("class_bookings").select("*").eq("class_id", str(class_id)).execute()
        current_bookings = len(bookings_result.data) if bookings_result.data else 0
        
        if current_bookings >= class_data["max_capacity"]:
            raise HTTPException(status_code=400, detail="Class is full")
        
        # Create booking
        result = db.client.table("class_bookings").insert({
            "class_id": str(class_id),
            "customer_id": str(booking["customer_id"]),
            "business_id": str(booking["business_id"]),
            "status": "confirmed",
            "booked_at": datetime.utcnow().isoformat()
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to book class")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WAITLIST MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/waitlist", response_model=dict, status_code=201)
async def add_to_waitlist(waitlist_entry: dict):
    """Add customer to waitlist when appointments are full"""
    db = get_database_service()
    
    try:
        result = db.client.table("waitlist").insert({
            "business_id": str(waitlist_entry["business_id"]),
            "customer_id": str(waitlist_entry["customer_id"]),
            "service_id": str(waitlist_entry.get("service_id")) if waitlist_entry.get("service_id") else None,
            "preferred_date": waitlist_entry.get("preferred_date"),
            "preferred_time": waitlist_entry.get("preferred_time"),
            "notes": waitlist_entry.get("notes"),
            "status": "waiting",
            "priority": waitlist_entry.get("priority", 0),
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to add to waitlist")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/waitlist", response_model=list)
async def list_waitlist(
    business_id: UUID = Query(..., description="Business ID"),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List waitlist entries"""
    db = get_database_service()
    
    try:
        query = db.client.table("waitlist").select("*").eq("business_id", str(business_id))
        
        if status:
            query = query.eq("status", status)
        
        query = query.range(offset, offset + limit - 1).order("priority", desc=True).order("created_at")
        result = await query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/waitlist/{entry_id}/convert", response_model=dict)
async def convert_waitlist_to_appointment(entry_id: UUID, appointment_data: dict):
    """Convert waitlist entry to actual appointment"""
    db = get_database_service()
    
    try:
        # Update waitlist status
        db.client.table("waitlist").update({
            "status": "converted",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(entry_id)).execute()
        
        # Create appointment (reuse existing appointment creation logic)
        # This would call the create_appointment function
        
        return {"success": True, "message": "Waitlist entry converted to appointment"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SERVICE ANALYTICS ENDPOINTS (Category-Specific)
# ============================================================================

@router.get("/analytics/appointment-trends", response_model=dict)
async def get_appointment_trends(
    business_id: UUID = Query(...),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Analyze appointment booking trends"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "trends": [],
        "peak_hours": [],
        "busiest_days": []
    }


@router.get("/analytics/service-performance", response_model=dict)
async def get_service_performance(
    business_id: UUID = Query(...),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Analyze which services are most popular"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "top_services": [],
        "revenue_by_service": {},
        "bookings_by_service": {}
    }


@router.get("/analytics/no-show-rate", response_model=dict)
async def get_no_show_rate(
    business_id: UUID = Query(...),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Calculate no-show and cancellation rates"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "no_show_rate": 0.0,
        "cancellation_rate": 0.0,
        "total_appointments": 0
    }


@router.get("/analytics/staff-utilization", response_model=dict)
async def get_staff_utilization(
    business_id: UUID = Query(...),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Analyze staff booking utilization"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "staff_metrics": [],
        "average_utilization": 0.0
    }
