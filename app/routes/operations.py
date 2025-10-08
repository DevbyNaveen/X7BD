"""
Operations Management API Routes
Enterprise-grade endpoints for tables, floor plans, kitchen, and staff

ENTERPRISE STRUCTURE:
- Food & Hospitality specific endpoints prefixed with /food
- Common endpoints (staff, time-clock, locations) moved to universal routes
- Tables and KDS are food-specific
"""

from fastapi import APIRouter, HTTPException, Query, status, WebSocket
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date, time

from ..models.operations import (
    Location, LocationCreate, LocationUpdate,
    FloorPlan, FloorPlanCreate, FloorPlanUpdate,
    Table, TableCreate, TableUpdate, TableWithDetails, TableAssignment,
    KDSOrder, KDSOrderCreate, KDSOrderUpdate, KDSOrderWithMetrics,
    StaffMember, StaffMemberCreate, StaffMemberUpdate,
    StaffSchedule, StaffScheduleCreate, StaffScheduleUpdate,
    TimeClock, TimeClockCreate, TimeClockUpdate,
    OperationsDashboard
)
from ..services.database import get_database_service
from ..services.realtime import RealtimeEventPublisher

router = APIRouter(prefix="/api/v1/food", tags=["Food & Hospitality - Operations"])


# ============================================================================
# LOCATIONS (Should be moved to universal /api/v1/locations)
# ============================================================================

@router.post("/locations", response_model=Location, status_code=status.HTTP_201_CREATED)
async def create_location(location: LocationCreate):
    """Create new location for multi-location businesses"""
    try:
        db = get_database_service()
        data = location.model_dump()
        data["business_id"] = str(data["business_id"])
        
        result = db.client.table("locations").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create location: {str(e)}")


@router.get("/locations", response_model=List[Location])
async def list_locations(
    business_id: UUID = Query(...),
    is_active: Optional[bool] = Query(None)
):
    """List all locations"""
    try:
        db = get_database_service()
        query = db.client.table("locations").select("*").eq("business_id", str(business_id))
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        result = query.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch locations: {str(e)}")


@router.get("/locations/{location_id}", response_model=Location)
async def get_location(location_id: UUID):
    """Get location details"""
    # TODO: Implement Supabase query
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.put("/locations/{location_id}", response_model=Location)
async def update_location(location_id: UUID, updates: LocationUpdate):
    """Update location"""
    # TODO: Implement Supabase update
    raise HTTPException(status_code=501, detail="Implementation pending")


# ============================================================================
# FLOOR PLANS
# ============================================================================

@router.post("/floor-plans", response_model=FloorPlan, status_code=status.HTTP_201_CREATED)
async def create_floor_plan(floor_plan: FloorPlanCreate):
    """
    Create floor plan with visual layout
    
    - **Visual designer**: Drag-and-drop table placement
    - **Multiple plans**: Different layouts for different times
    """
    # TODO: Implement Supabase insert
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.get("/floor-plans", response_model=List[FloorPlan])
async def list_floor_plans(
    business_id: UUID = Query(...),
    location_id: Optional[UUID] = Query(None)
):
    """List floor plans"""
    # TODO: Implement Supabase query
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.get("/floor-plans/{plan_id}", response_model=FloorPlan)
async def get_floor_plan(plan_id: UUID):
    """Get floor plan with layout data"""
    # TODO: Implement Supabase query
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.put("/floor-plans/{plan_id}", response_model=FloorPlan)
async def update_floor_plan(plan_id: UUID, updates: FloorPlanUpdate):
    """Update floor plan layout"""
    # TODO: Implement Supabase update
    raise HTTPException(status_code=501, detail="Implementation pending")


# ============================================================================
# TABLE MANAGEMENT
# ============================================================================

@router.post("/tables", response_model=Table, status_code=status.HTTP_201_CREATED)
async def create_table(table: TableCreate):
    """Create new table"""
    try:
        db = get_database_service()
        data = table.model_dump()
        data["business_id"] = str(data["business_id"])
        if data.get("location_id"):
            data["location_id"] = str(data["location_id"])
        if data.get("floor_plan_id"):
            data["floor_plan_id"] = str(data["floor_plan_id"])
        
        result = await db.create_table(data)
        
        # Publish real-time update
        await RealtimeEventPublisher.publish_table_update(
            str(table.business_id),
            {"type": "table_created", "table": result}
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create table: {str(e)}")


@router.get("/tables", response_model=List[TableWithDetails])
async def list_tables(
    business_id: UUID = Query(...),
    location_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    include_details: bool = Query(True)
):
    """
    List tables with real-time status
    
    - **Live status**: Available, occupied, reserved
    - **Occupancy**: Current order and duration
    - **Filtering**: By location and status
    """
    try:
        db = get_database_service()
        tables = await db.get_tables(business_id, location_id, status)
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tables: {str(e)}")


@router.get("/tables/{table_id}", response_model=TableWithDetails)
async def get_table(table_id: UUID):
    """Get table with full details"""
    # TODO: Implement Supabase query
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.put("/tables/{table_id}", response_model=Table)
async def update_table(table_id: UUID, updates: TableUpdate):
    """Update table details or status"""
    try:
        db = get_database_service()
        update_data = updates.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("tables").update(update_data).eq("id", str(table_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Table not found")
        
        # Publish real-time update
        await RealtimeEventPublisher.publish_table_update(
            result.data[0]["business_id"],
            {"type": "table_updated", "table": result.data[0]}
        )
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update table: {str(e)}")


@router.post("/tables/assign", response_model=dict)
async def assign_table(assignment: TableAssignment):
    """
    Assign table to order
    
    - **Capacity check**: Validate party size
    - **Status update**: Mark table as occupied
    - **Tracking**: Start occupancy timer
    """
    try:
        db = get_database_service()
        
        # Get table
        table_result = db.client.table("tables").select("*").eq("id", str(assignment.table_id)).execute()
        if not table_result.data:
            raise HTTPException(status_code=404, detail="Table not found")
        
        table = table_result.data[0]
        
        # Validate capacity
        if assignment.party_size > table["capacity"]:
            raise HTTPException(status_code=400, detail="Party size exceeds table capacity")
        
        # Check availability
        if table["status"] != "available":
            raise HTTPException(status_code=400, detail="Table is not available")
        
        # Update table
        result = await db.update_table_status(
            assignment.table_id,
            "occupied",
            assignment.order_id
        )
        
        # Publish real-time update
        await RealtimeEventPublisher.publish_table_update(
            table["business_id"],
            {"type": "table_assigned", "table": result}
        )
        
        return {
            "success": True,
            "table_id": str(assignment.table_id),
            "order_id": str(assignment.order_id),
            "assigned_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign table: {str(e)}")


@router.post("/tables/{table_id}/release", response_model=dict)
async def release_table(table_id: UUID):
    """
    Release table after service
    
    - **Status update**: Mark as cleaning or available
    - **Metrics**: Calculate table turnover time
    """
    try:
        db = get_database_service()
        
        # Get table
        table_result = db.client.table("tables").select("*").eq("id", str(table_id)).execute()
        if not table_result.data:
            raise HTTPException(status_code=404, detail="Table not found")
        
        table = table_result.data[0]
        
        # Update table status
        result = await db.update_table_status(table_id, "available", None)
        
        # Publish real-time update
        await RealtimeEventPublisher.publish_table_update(
            table["business_id"],
            {"type": "table_released", "table": result}
        )
        
        return {
            "success": True,
            "table_id": str(table_id),
            "released_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to release table: {str(e)}")


@router.get("/tables/availability", response_model=List[Table])
async def check_table_availability(
    business_id: UUID = Query(...),
    location_id: Optional[UUID] = Query(None),
    party_size: int = Query(..., ge=1),
    time_slot: Optional[datetime] = Query(None)
):
    """
    Check table availability for reservations
    
    - **Capacity matching**: Find suitable tables
    - **Time-based**: Check future availability
    - **Combining tables**: Suggest table combinations
    """
    # TODO: Query available tables
    # TODO: Filter by capacity
    # TODO: Check reservations for time slot
    raise HTTPException(status_code=501, detail="Implementation pending")


# ============================================================================
# KITCHEN DISPLAY SYSTEM (KDS)
# ============================================================================

@router.post("/kds/orders", response_model=KDSOrder, status_code=status.HTTP_201_CREATED)
async def create_kds_order(kds_order: KDSOrderCreate):
    """
    Send order to kitchen
    
    - **Station routing**: Route to appropriate kitchen station
    - **Priority**: Set order priority
    - **Timing**: Calculate target completion time
    """
    try:
        db = get_database_service()
        data = kds_order.model_dump()
        data["business_id"] = str(data["business_id"])
        data["order_id"] = str(data["order_id"])
        
        result = await db.create_kds_order(data)
        
        # Publish to WebSocket for real-time KDS updates
        await RealtimeEventPublisher.publish_kds_update(
            str(kds_order.business_id),
            {"type": "new_order", "order": result}
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create KDS order: {str(e)}")


@router.get("/kds/orders", response_model=List[KDSOrderWithMetrics])
async def list_kds_orders(
    business_id: UUID = Query(...),
    station: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    active_only: bool = Query(True)
):
    """
    List kitchen orders with metrics
    
    - **Real-time**: Live order status
    - **Metrics**: Prep time, delays
    - **Filtering**: By station and status
    """
    try:
        db = get_database_service()
        orders = await db.get_active_kds_orders(business_id, station)
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch KDS orders: {str(e)}")


@router.get("/kds/orders/{order_id}", response_model=KDSOrderWithMetrics)
async def get_kds_order(order_id: UUID):
    """Get KDS order with metrics"""
    # TODO: Implement Supabase query
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.put("/kds/orders/{order_id}", response_model=KDSOrder)
async def update_kds_order(order_id: UUID, updates: KDSOrderUpdate):
    """
    Update KDS order status
    
    - **Status transitions**: pending → preparing → ready → served
    - **Timing**: Track prep start/end times
    - **Notifications**: Alert servers when ready
    """
    try:
        db = get_database_service()
        update_data = updates.model_dump(exclude_unset=True)
        
        # Set timestamp fields based on status
        timestamp_field = None
        if update_data.get("status") == "preparing":
            timestamp_field = "started_at"
        elif update_data.get("status") == "ready":
            timestamp_field = "completed_at"
        
        result = await db.update_kds_order_status(order_id, update_data["status"], timestamp_field)
        
        # Publish WebSocket update
        await RealtimeEventPublisher.publish_kds_update(
            result["business_id"],
            {"type": "order_status_updated", "order": result}
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update KDS order: {str(e)}")


@router.get("/kds/performance", response_model=dict)
async def get_kitchen_performance(
    business_id: UUID = Query(...),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """
    Analyze kitchen performance
    
    - **Prep times**: Average and by item
    - **Efficiency**: Orders per hour
    - **Delays**: Late orders analysis
    """
    # TODO: Query KDS orders
    # TODO: Calculate performance metrics
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.websocket("/kds/live/{business_id}")
async def kds_live_feed(websocket: WebSocket, business_id: UUID):
    """
    WebSocket for real-time KDS updates
    
    - **Live orders**: New orders appear instantly
    - **Status updates**: Real-time status changes
    - **Alerts**: Priority orders and delays
    """
    await websocket.accept()
    # TODO: Implement WebSocket connection
    # TODO: Subscribe to KDS events
    # TODO: Stream updates to client
    pass


# ============================================================================
# STAFF MANAGEMENT (Should be moved to universal /api/v1/staff)
# ============================================================================

@router.post("/staff", response_model=StaffMember, status_code=status.HTTP_201_CREATED)
async def create_staff_member(staff: StaffMemberCreate):
    """Create new staff member"""
    try:
        db = get_database_service()
        data = staff.model_dump()
        data["business_id"] = str(data["business_id"])
        if data.get("user_id"):
            data["user_id"] = str(data["user_id"])
        
        result = await db.create_staff_member(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create staff member: {str(e)}")


@router.get("/staff", response_model=List[StaffMember])
async def list_staff_members(
    business_id: UUID = Query(...),
    status: Optional[str] = Query(None),
    position: Optional[str] = Query(None)
):
    """List staff members"""
    try:
        db = get_database_service()
        query = db.client.table("staff_members").select("*").eq("business_id", str(business_id))
        
        if status:
            query = query.eq("status", status)
        if position:
            query = query.eq("position", position)
        
        result = query.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch staff members: {str(e)}")


@router.get("/staff/{staff_id}", response_model=StaffMember)
async def get_staff_member(staff_id: UUID):
    """Get staff member details"""
    # TODO: Implement Supabase query
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.put("/staff/{staff_id}", response_model=StaffMember)
async def update_staff_member(staff_id: UUID, updates: StaffMemberUpdate):
    """Update staff member"""
    # TODO: Implement Supabase update
    raise HTTPException(status_code=501, detail="Implementation pending")


# ============================================================================
# STAFF SCHEDULING
# ============================================================================

@router.post("/schedules", response_model=StaffSchedule, status_code=status.HTTP_201_CREATED)
async def create_schedule(schedule: StaffScheduleCreate):
    """Create staff schedule"""
    # TODO: Implement Supabase insert
    # TODO: Check for scheduling conflicts
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.get("/schedules", response_model=List[StaffSchedule])
async def list_schedules(
    business_id: UUID = Query(...),
    staff_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """List staff schedules"""
    # TODO: Implement Supabase query
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.put("/schedules/{schedule_id}", response_model=StaffSchedule)
async def update_schedule(schedule_id: UUID, updates: StaffScheduleUpdate):
    """Update staff schedule"""
    # TODO: Implement Supabase update
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(schedule_id: UUID):
    """Delete staff schedule"""
    # TODO: Implement Supabase delete
    raise HTTPException(status_code=501, detail="Implementation pending")


# ============================================================================
# TIME CLOCK (Should be moved to universal /api/v1/time-clock)
# ============================================================================

@router.post("/time-clock/clock-in", response_model=TimeClock, status_code=status.HTTP_201_CREATED)
async def clock_in(clock_in_data: TimeClockCreate):
    """
    Clock in staff member
    
    - **Validation**: Check scheduled shift
    - **Location**: Track clock-in location
    - **Notifications**: Alert manager of early/late clock-in
    """
    try:
        db = get_database_service()
        data = clock_in_data.model_dump()
        data["business_id"] = str(data["business_id"])
        data["staff_id"] = str(data["staff_id"])
        if data.get("location_id"):
            data["location_id"] = str(data["location_id"])
        
        result = await db.clock_in_staff(data)
        
        # Publish staff update
        await RealtimeEventPublisher.publish_staff_update(
            str(clock_in_data.business_id),
            {"type": "clock_in", "staff": result}
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clock in: {str(e)}")


@router.put("/time-clock/{clock_id}/clock-out", response_model=TimeClock)
async def clock_out(clock_id: UUID, clock_out_time: Optional[datetime] = None):
    """
    Clock out staff member
    
    - **Hours calculation**: Auto-calculate total hours
    - **Overtime**: Detect and flag overtime
    - **Breaks**: Account for break time
    """
    try:
        db = get_database_service()
        
        if not clock_out_time:
            clock_out_time = datetime.utcnow()
        
        result = await db.clock_out_staff(clock_id, clock_out_time)
        
        # Publish staff update
        await RealtimeEventPublisher.publish_staff_update(
            result["business_id"],
            {"type": "clock_out", "staff": result}
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clock out: {str(e)}")


@router.get("/time-clock", response_model=List[TimeClock])
async def list_time_clock_entries(
    business_id: UUID = Query(...),
    staff_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """List time clock entries"""
    # TODO: Implement Supabase query
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.get("/time-clock/active", response_model=List[dict])
async def get_clocked_in_staff(business_id: UUID):
    """
    Get currently clocked-in staff
    
    - **Real-time**: Who's working now
    - **Duration**: How long they've been clocked in
    - **Position**: Current role/station
    """
    try:
        db = get_database_service()
        staff = await db.get_clocked_in_staff(business_id)
        return staff
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch clocked-in staff: {str(e)}")


# ============================================================================
# OPERATIONS DASHBOARD
# ============================================================================

@router.get("/dashboard/{business_id}", response_model=OperationsDashboard)
async def get_operations_dashboard(
    business_id: UUID,
    location_id: Optional[UUID] = Query(None)
):
    """
    Real-time operations dashboard
    
    - **Tables**: Live table status
    - **Kitchen**: Active orders and prep times
    - **Staff**: Who's working, breaks, etc.
    - **Orders**: Today's order metrics
    - **Revenue**: Real-time revenue tracking
    """
    # TODO: Aggregate data from multiple sources
    # TODO: Calculate real-time metrics
    # TODO: Return comprehensive dashboard data
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.get("/analytics/table-turnover", response_model=dict)
async def analyze_table_turnover(
    business_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Analyze table turnover rates
    
    - **Average turnover**: Time per table
    - **By time of day**: Peak vs. off-peak
    - **By table**: Identify slow tables
    """
    # TODO: Calculate turnover metrics
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.get("/analytics/labor-costs", response_model=dict)
async def analyze_labor_costs(
    business_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Analyze labor costs
    
    - **Total costs**: Labor expense for period
    - **Labor percentage**: % of revenue
    - **Overtime**: Overtime costs
    - **By position**: Cost breakdown
    """
    # TODO: Calculate labor metrics
    raise HTTPException(status_code=501, detail="Implementation pending")
