"""
API Routes for Professional Services Template
(Law Firm, Accounting Firm, Consulting, Marketing Agency, Real Estate, etc.)

ENTERPRISE STRUCTURE:
- Common endpoints (customers, staff, time-clock) moved to universal routes
- Category-specific endpoints prefixed with /professional
- Billable time entries are professional-specific (different from time-clock)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date

from ..models.professional import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    TimeEntryCreate, TimeEntryUpdate, TimeEntryResponse,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    ResourceCreate, ResourceUpdate, ResourceResponse,
    ResourceAllocationCreate, ResourceAllocationUpdate, ResourceAllocationResponse
)
from ..services.database import get_database_service

router = APIRouter(prefix="/api/v1/professional", tags=["Professional Services Template"])


# ============================================================================
# PROJECTS ENDPOINTS
# ============================================================================

@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate):
    """Create a new project"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("projects").insert({
            "business_id": str(project.business_id),
            "client_id": str(project.client_id),
            "name": project.name,
            "description": project.description,
            "project_number": project.project_number,
            "status": project.status,
            "priority": project.priority,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "end_date": project.end_date.isoformat() if project.end_date else None,
            "estimated_hours": project.estimated_hours,
            "hourly_rate": project.hourly_rate,
            "budget": project.budget,
            "assigned_staff": [str(sid) for sid in project.assigned_staff] if project.assigned_staff else [],
            "tags": project.tags,
            "metadata": project.metadata
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create project")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    business_id: UUID = Query(..., description="Business ID"),
    client_id: Optional[UUID] = Query(None, description="Filter by client"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all projects for a business"""
    db = get_database_service()
    
    try:
        query = db.supabase.table("projects").select("*").eq("business_id", str(business_id))
        
        if client_id:
            query = query.eq("client_id", str(client_id))
        if status:
            query = query.eq("status", status)
        if priority:
            query = query.eq("priority", priority)
        
        query = query.range(offset, offset + limit - 1).order("created_at", desc=True)
        result = await query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID):
    """Get a specific project by ID"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("projects").select("*").eq("id", str(project_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: UUID, project: ProjectUpdate):
    """Update a project"""
    db = get_database_service()
    
    try:
        update_data = {k: v for k, v in project.dict(exclude_unset=True).items() if v is not None}
        
        # Convert UUIDs to strings
        if "client_id" in update_data:
            update_data["client_id"] = str(update_data["client_id"])
        if "assigned_staff" in update_data and update_data["assigned_staff"]:
            update_data["assigned_staff"] = [str(sid) for sid in update_data["assigned_staff"]]
        
        # Convert dates to ISO format
        for field in ["start_date", "end_date"]:
            if field in update_data and update_data[field]:
                update_data[field] = update_data[field].isoformat()
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = await db.supabase.table("projects").update(update_data).eq("id", str(project_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(project_id: UUID):
    """Delete a project"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("projects").delete().eq("id", str(project_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TIME ENTRIES ENDPOINTS
# ============================================================================

@router.post("/time-entries", response_model=TimeEntryResponse, status_code=201)
async def create_time_entry(entry: TimeEntryCreate):
    """Create a new time entry"""
    db = get_database_service()
    
    try:
        # Calculate duration if end_time is provided
        duration_hours = entry.duration_hours
        if entry.end_time and entry.start_time:
            duration = (entry.end_time - entry.start_time).total_seconds() / 3600
            duration_hours = round(duration, 2)
        
        # Calculate total amount
        total_amount = None
        if duration_hours and entry.hourly_rate:
            total_amount = duration_hours * entry.hourly_rate
        
        result = await db.supabase.table("time_entries").insert({
            "business_id": str(entry.business_id),
            "project_id": str(entry.project_id) if entry.project_id else None,
            "staff_id": str(entry.staff_id),
            "start_time": entry.start_time.isoformat(),
            "end_time": entry.end_time.isoformat() if entry.end_time else None,
            "duration_hours": duration_hours,
            "description": entry.description,
            "billable": entry.billable,
            "hourly_rate": entry.hourly_rate,
            "total_amount": total_amount,
            "status": entry.status,
            "metadata": entry.metadata
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create time entry")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/time-entries", response_model=List[TimeEntryResponse])
async def list_time_entries(
    business_id: UUID = Query(..., description="Business ID"),
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    staff_id: Optional[UUID] = Query(None, description="Filter by staff"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    billable: Optional[bool] = Query(None, description="Filter by billable status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all time entries for a business"""
    db = get_database_service()
    
    try:
        query = db.supabase.table("time_entries").select("*").eq("business_id", str(business_id))
        
        if project_id:
            query = query.eq("project_id", str(project_id))
        if staff_id:
            query = query.eq("staff_id", str(staff_id))
        if status:
            query = query.eq("status", status)
        if billable is not None:
            query = query.eq("billable", billable)
        if start_date:
            query = query.gte("start_time", start_date.isoformat())
        if end_date:
            query = query.lte("start_time", end_date.isoformat())
        
        query = query.range(offset, offset + limit - 1).order("start_time", desc=True)
        result = await query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/time-entries/{entry_id}", response_model=TimeEntryResponse)
async def get_time_entry(entry_id: UUID):
    """Get a specific time entry by ID"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("time_entries").select("*").eq("id", str(entry_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Time entry not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/time-entries/{entry_id}", response_model=TimeEntryResponse)
async def update_time_entry(entry_id: UUID, entry: TimeEntryUpdate):
    """Update a time entry"""
    db = get_database_service()
    
    try:
        update_data = {k: v for k, v in entry.dict(exclude_unset=True).items() if v is not None}
        
        # Convert UUIDs to strings
        for field in ["project_id", "staff_id"]:
            if field in update_data and update_data[field]:
                update_data[field] = str(update_data[field])
        
        # Convert datetime to ISO format
        for field in ["start_time", "end_time"]:
            if field in update_data and update_data[field]:
                update_data[field] = update_data[field].isoformat()
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = await db.supabase.table("time_entries").update(update_data).eq("id", str(entry_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Time entry not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/time-entries/{entry_id}", status_code=204)
async def delete_time_entry(entry_id: UUID):
    """Delete a time entry"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("time_entries").delete().eq("id", str(entry_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Time entry not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INVOICES ENDPOINTS
# ============================================================================

@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
async def create_invoice(invoice: InvoiceCreate):
    """Create a new invoice"""
    db = get_database_service()
    
    try:
        # Calculate amount_due
        amount_due = invoice.total_amount
        
        result = await db.supabase.table("invoices").insert({
            "business_id": str(invoice.business_id),
            "client_id": str(invoice.client_id),
            "project_id": str(invoice.project_id) if invoice.project_id else None,
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "issue_date": invoice.issue_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "subtotal": invoice.subtotal,
            "tax_amount": invoice.tax_amount,
            "discount_amount": invoice.discount_amount,
            "total_amount": invoice.total_amount,
            "amount_due": amount_due,
            "currency": invoice.currency,
            "line_items": [item.dict() for item in invoice.line_items],
            "notes": invoice.notes,
            "terms": invoice.terms,
            "payment_method": invoice.payment_method,
            "metadata": invoice.metadata
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create invoice")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    business_id: UUID = Query(..., description="Business ID"),
    client_id: Optional[UUID] = Query(None, description="Filter by client"),
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all invoices for a business"""
    db = get_database_service()
    
    try:
        query = db.supabase.table("invoices").select("*").eq("business_id", str(business_id))
        
        if client_id:
            query = query.eq("client_id", str(client_id))
        if project_id:
            query = query.eq("project_id", str(project_id))
        if status:
            query = query.eq("status", status)
        
        query = query.range(offset, offset + limit - 1).order("issue_date", desc=True)
        result = await query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: UUID):
    """Get a specific invoice by ID"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("invoices").select("*").eq("id", str(invoice_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: UUID, invoice: InvoiceUpdate):
    """Update an invoice"""
    db = get_database_service()
    
    try:
        update_data = {k: v for k, v in invoice.dict(exclude_unset=True).items() if v is not None}
        
        # Convert UUIDs to strings
        for field in ["client_id", "project_id"]:
            if field in update_data and update_data[field]:
                update_data[field] = str(update_data[field])
        
        # Convert dates to ISO format
        for field in ["issue_date", "due_date"]:
            if field in update_data and update_data[field]:
                update_data[field] = update_data[field].isoformat()
        
        # Convert line items
        if "line_items" in update_data and update_data["line_items"]:
            update_data["line_items"] = [item.dict() for item in update_data["line_items"]]
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = await db.supabase.table("invoices").update(update_data).eq("id", str(invoice_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/invoices/{invoice_id}", status_code=204)
async def delete_invoice(invoice_id: UUID):
    """Delete an invoice"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("invoices").delete().eq("id", str(invoice_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoices/{invoice_id}/mark-paid")
async def mark_invoice_paid(
    invoice_id: UUID,
    payment_method: Optional[str] = Query(None, description="Payment method used")
):
    """Mark an invoice as paid"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("invoices").update({
            "status": "paid",
            "amount_paid": db.supabase.table("invoices").select("total_amount").eq("id", str(invoice_id)).execute().data[0]["total_amount"],
            "amount_due": 0,
            "paid_at": datetime.utcnow().isoformat(),
            "payment_method": payment_method,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(invoice_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        return {"success": True, "message": "Invoice marked as paid", "invoice": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RESOURCES ENDPOINTS
# ============================================================================

@router.post("/resources", response_model=ResourceResponse, status_code=201)
async def create_resource(resource: ResourceCreate):
    """Create a new resource"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("resources").insert({
            "business_id": str(resource.business_id),
            "name": resource.name,
            "type": resource.type,
            "description": resource.description,
            "status": resource.status,
            "location": resource.location,
            "cost_per_hour": resource.cost_per_hour,
            "metadata": resource.metadata
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create resource")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources", response_model=List[ResourceResponse])
async def list_resources(
    business_id: UUID = Query(..., description="Business ID"),
    type: Optional[str] = Query(None, description="Filter by resource type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all resources for a business"""
    db = get_database_service()
    
    try:
        query = db.supabase.table("resources").select("*").eq("business_id", str(business_id))
        
        if type:
            query = query.eq("type", type)
        if status:
            query = query.eq("status", status)
        
        query = query.range(offset, offset + limit - 1).order("created_at", desc=True)
        result = await query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(resource_id: UUID):
    """Get a specific resource by ID"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("resources").select("*").eq("id", str(resource_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(resource_id: UUID, resource: ResourceUpdate):
    """Update a resource"""
    db = get_database_service()
    
    try:
        update_data = {k: v for k, v in resource.dict(exclude_unset=True).items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = await db.supabase.table("resources").update(update_data).eq("id", str(resource_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/resources/{resource_id}", status_code=204)
async def delete_resource(resource_id: UUID):
    """Delete a resource"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("resources").delete().eq("id", str(resource_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RESOURCE ALLOCATIONS ENDPOINTS
# ============================================================================

@router.post("/resource-allocations", response_model=ResourceAllocationResponse, status_code=201)
async def create_resource_allocation(allocation: ResourceAllocationCreate):
    """Create a new resource allocation"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("resource_allocations").insert({
            "business_id": str(allocation.business_id),
            "resource_id": str(allocation.resource_id),
            "project_id": str(allocation.project_id) if allocation.project_id else None,
            "staff_id": str(allocation.staff_id) if allocation.staff_id else None,
            "start_time": allocation.start_time.isoformat(),
            "end_time": allocation.end_time.isoformat(),
            "notes": allocation.notes
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create resource allocation")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resource-allocations", response_model=List[ResourceAllocationResponse])
async def list_resource_allocations(
    business_id: UUID = Query(..., description="Business ID"),
    resource_id: Optional[UUID] = Query(None, description="Filter by resource"),
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all resource allocations for a business"""
    db = get_database_service()
    
    try:
        query = db.supabase.table("resource_allocations").select("*").eq("business_id", str(business_id))
        
        if resource_id:
            query = query.eq("resource_id", str(resource_id))
        if project_id:
            query = query.eq("project_id", str(project_id))
        
        query = query.range(offset, offset + limit - 1).order("start_time", desc=True)
        result = await query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/resource-allocations/{allocation_id}", status_code=204)
async def delete_resource_allocation(allocation_id: UUID):
    """Delete a resource allocation"""
    db = get_database_service()
    
    try:
        result = await db.supabase.table("resource_allocations").delete().eq("id", str(allocation_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Resource allocation not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROFESSIONAL SERVICES ANALYTICS ENDPOINTS (Category-Specific)
# ============================================================================

@router.get("/analytics/project-profitability", response_model=dict)
async def get_project_profitability(
    business_id: UUID = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Analyze profitability by project"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "projects": [],
        "total_revenue": 0.0,
        "total_costs": 0.0,
        "overall_margin": 0.0
    }


@router.get("/analytics/billable-vs-non-billable", response_model=dict)
async def get_billable_analysis(
    business_id: UUID = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Analyze billable vs non-billable hours"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "billable_hours": 0.0,
        "non_billable_hours": 0.0,
        "billable_percentage": 0.0,
        "billable_revenue": 0.0
    }


@router.get("/analytics/staff-utilization", response_model=dict)
async def get_staff_utilization_professional(
    business_id: UUID = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Analyze staff utilization and capacity"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "staff_metrics": [],
        "average_utilization": 0.0,
        "capacity_available": 0.0
    }


@router.get("/analytics/project-timeline", response_model=dict)
async def get_project_timeline_analysis(
    business_id: UUID = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Analyze project timeline performance (on-time vs delayed)"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "on_time_projects": 0,
        "delayed_projects": 0,
        "average_delay_days": 0.0,
        "projects": []
    }


@router.get("/analytics/invoice-aging", response_model=dict)
async def get_invoice_aging(
    business_id: UUID = Query(...)
):
    """Analyze invoice aging and outstanding payments"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "current": 0.0,
        "days_30": 0.0,
        "days_60": 0.0,
        "days_90_plus": 0.0,
        "total_outstanding": 0.0
    }


@router.get("/analytics/revenue-by-client", response_model=dict)
async def get_revenue_by_client(
    business_id: UUID = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(10, ge=1, le=50)
):
    """Analyze revenue by client"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "top_clients": [],
        "total_revenue": 0.0
    }


@router.get("/analytics/resource-allocation", response_model=dict)
async def get_resource_allocation_analysis(
    business_id: UUID = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Analyze resource allocation efficiency"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "resources": [],
        "utilization_rate": 0.0,
        "conflicts": []
    }


@router.get("/analytics/budget-variance", response_model=dict)
async def get_budget_variance(
    business_id: UUID = Query(...),
    project_id: Optional[UUID] = Query(None)
):
    """Analyze budget vs actual spending"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "projects": [],
        "total_budget": 0.0,
        "total_actual": 0.0,
        "variance": 0.0,
        "variance_percentage": 0.0
    }
