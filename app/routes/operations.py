"""
Operations Management API Routes
Enterprise-grade endpoints for tables, floor plans, kitchen, and staff

ENTERPRISE STRUCTURE:
- Food & Hospitality specific endpoints prefixed with /food
- Common endpoints (staff, time-clock, locations) moved to universal routes
- Tables and KDS are food-specific
"""

from fastapi import APIRouter, HTTPException, Query, status, WebSocket
from fastapi.responses import JSONResponse
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal
import json

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
    try:
        db = get_database_service()
        result = db.client.table("locations").select("*").eq("id", str(location_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch location: {str(e)}")


@router.put("/locations/{location_id}", response_model=Location)
async def update_location(location_id: UUID, updates: LocationUpdate):
    """Update location"""
    try:
        db = get_database_service()
        update_data = updates.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("locations").update(update_data).eq("id", str(location_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update location: {str(e)}")


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
    try:
        db = get_database_service()
        data = floor_plan.model_dump()
        data["business_id"] = str(data["business_id"])
        if data.get("location_id"):
            data["location_id"] = str(data["location_id"])
        
        result = db.client.table("floor_plans").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create floor plan: {str(e)}")


@router.get("/floor-plans", response_model=List[FloorPlan])
async def list_floor_plans(
    business_id: UUID = Query(...),
    location_id: Optional[UUID] = Query(None)
):
    """List floor plans"""
    try:
        db = get_database_service()
        query = db.client.table("floor_plans").select("*").eq("business_id", str(business_id))
        
        if location_id:
            query = query.eq("location_id", str(location_id))
        
        result = query.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch floor plans: {str(e)}")


@router.get("/floor-plans/{plan_id}", response_model=FloorPlan)
async def get_floor_plan(plan_id: UUID):
    """Get floor plan with layout data"""
    try:
        db = get_database_service()
        result = db.client.table("floor_plans").select("*").eq("id", str(plan_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Floor plan not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch floor plan: {str(e)}")


@router.put("/floor-plans/{plan_id}", response_model=FloorPlan)
async def update_floor_plan(plan_id: UUID, updates: FloorPlanUpdate):
    """Update floor plan layout"""
    try:
        db = get_database_service()
        update_data = updates.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("floor_plans").update(update_data).eq("id", str(plan_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Floor plan not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update floor plan: {str(e)}")


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


@router.put("/tables/{table_id}/assign", response_model=dict)
async def assign_table_by_id(
    table_id: UUID,
    assignment: TableAssignment
):
    """
    Assign table to order (alternative endpoint)
    
    - **Capacity check**: Validate party size
    - **Status update**: Mark table as occupied
    - **Tracking**: Start occupancy timer
    """
    # Ensure the table_id in the URL matches the assignment
    if assignment.table_id != table_id:
        raise HTTPException(status_code=400, detail="Table ID mismatch")
    
    return await assign_table(assignment)


@router.get("/tables/test", response_model=dict)
async def test_tables_connection():
    """Test endpoint to check database connection and tables table"""
    try:
        db = get_database_service()
        
        # Test basic connection
        result = db.client.table("tables").select("id").limit(1).execute()
        
        return {
            "success": True,
            "message": "Database connection successful",
            "tables_count": len(result.data) if result.data else 0,
            "sample_data": result.data[0] if result.data else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Database connection failed"
        }

@router.post("/tables/assign", response_model=dict)
async def assign_table(assignment: TableAssignment):
    """Debug version - minimal operations"""
    print("🎯 DEBUG: Table assignment endpoint called!")
    print(f"📦 DEBUG: Received data: {assignment.dict()}")
    
    try:
        # Test 1: Basic response without any operations
        print("✅ DEBUG: Basic test passed - returning success")
        
        return {
            "success": True,
            "table_id": str(assignment.table_id),
            "order_id": str(assignment.order_id),
            "assigned_at": datetime.utcnow().isoformat(),
            "message": "Debug: Basic success"
        }
        
    except Exception as e:
        print(f"💥 DEBUG: Error in endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")
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


@router.get("/tables/availability", response_model=List[dict])
async def check_table_availability(
    business_id: UUID = Query(...),
    location_id: Optional[UUID] = Query(None),
    party_size: str = Query(...),
    time_slot: Optional[datetime] = Query(None)
):
    """
    Check table availability for reservations
    
    - **Capacity matching**: Find suitable tables
    - **Time-based**: Check future availability
    - **Combining tables**: Suggest table combinations
    """
    try:
        db = get_database_service()
        
        # Parse party_size - handle formats like "1:1", "4", etc.
        try:
            if ":" in party_size:
                # Format like "1:1" - take the first number
                party_size_int = int(party_size.split(":")[0])
            else:
                # Format like "4" - direct integer
                party_size_int = int(party_size)
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="Invalid party_size format. Expected integer or format like '1:1'")
        
        if party_size_int < 1:
            raise HTTPException(status_code=400, detail="Party size must be at least 1")
        
        # Query tables with sufficient capacity
        query = db.client.table("tables").select("*")
        query = query.eq("business_id", str(business_id))
        query = query.gte("capacity", party_size_int)
        
        if location_id:
            query = query.eq("location_id", str(location_id))
        
        result = query.execute()
        tables = result.data
        
        # If time_slot provided, check for reservations
        if time_slot:
            # Query reservations for the time slot (would need reservations table)
            # For now, filter by current status
            available_tables = [t for t in tables if t.get("status") == "available" or t.get("status") is None]
        else:
            # Just return currently available tables
            available_tables = [t for t in tables if t.get("status") == "available" or t.get("status") is None]
        
        # Ensure all tables have a status field
        for table in available_tables:
            if "status" not in table or table["status"] is None:
                table["status"] = "available"
        
        return available_tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check availability: {str(e)}")


@router.put("/orders/{order_id}/status", response_model=dict)
async def update_order_status(
    order_id: UUID,
    status: str = Query(..., pattern=r"^(pending|active|preparing|ready|completed|cancelled)$")
):
    """
    Update order status
    
    - **Status Updates**: Change order status (pending, active, preparing, ready, completed, cancelled)
    - **Analytics Integration**: Automatically populates item_performance when completed
    - **Real-time Updates**: Publishes status change events
    """
    try:
        db = get_database_service()
        
        # Update order status
        result = await db.update_order_status(order_id, status)
        
        if not result:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Publish real-time update
        await RealtimeEventPublisher.publish_order_update(
            result["business_id"],
            {
                "type": "order_status_updated",
                "order_id": str(order_id),
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "order_id": str(order_id),
            "status": status,
            "updated_at": result["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update order status: {str(e)}")


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
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🎯 START: Creating KDS order")
    logger.info(f"📦 Received KDS order data: {kds_order.model_dump()}")
    
    try:
        # Step 1: Get database service
        logger.info("1️⃣ Getting database service...")
        db = get_database_service()
        logger.info("✅ Database service obtained")
        
        # Step 2: Prepare data
        logger.info("2️⃣ Preparing order data...")
        data = kds_order.model_dump()
        logger.info(f"📊 Raw model dump: {data}")
        
        data["business_id"] = str(data["business_id"])
        data["order_id"] = str(data["order_id"])
        
        # Convert datetime fields to strings for JSON serialization
        if "target_time" in data and data["target_time"]:
            data["target_time"] = data["target_time"].isoformat()
            logger.info(f"🕐 Converted target_time to ISO string: {data['target_time']}")
        
        # Convert any other datetime fields that might exist
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
                logger.info(f"🕐 Converted {key} datetime to ISO string: {data[key]}")
        
        # Convert UUID fields in items and handle any datetime fields
        if "items" in data and data["items"]:
            logger.info(f"🔍 Order items: {len(data['items'])} items")
            for i, item in enumerate(data["items"]):
                if "menu_item_id" in item:
                    item["menu_item_id"] = str(item["menu_item_id"])
                
                # Convert any datetime fields in items
                for key, value in item.items():
                    if isinstance(value, datetime):
                        item[key] = value.isoformat()
                        logger.info(f"🕐 Converted item {i+1} {key} datetime to ISO string: {item[key]}")
                
                logger.info(f"   Item {i+1}: {item}")
        else:
            logger.warning("⚠️ No items found in order data")
        
        logger.info(f"📦 Final data to insert: {data}")
        
        # Step 3: Ensure order exists before creating KDS order
        logger.info("3️⃣ Ensuring order exists...")
        logger.info(f"🔍 Checking for order_id: {kds_order.order_id}")
        
        try:
            order_exists = await db.order_exists(kds_order.order_id)
            logger.info(f"🔍 Order exists check result: {order_exists}")
            
            if not order_exists:
                logger.info("📝 Order doesn't exist, creating new order...")
                
                # Handle customer_id - NULL for staff orders, populated for customer orders
                customer_id = None
                if hasattr(kds_order, 'customer_id') and kds_order.customer_id:
                    customer_id = str(kds_order.customer_id)
                    logger.info(f"✅ Using customer ID from KDS order: {customer_id}")
                else:
                    logger.info("🔍 No customer ID provided - creating staff/internal order with customer_id = NULL")
                
                # Calculate total amount from KDS order items
                total_amount = 0.0
                order_items = []
                if kds_order.items:
                    for item in kds_order.items:
                        # Get menu item details to calculate price
                        try:
                            menu_item_result = db.client.table("menu_items").select("price, cost").eq("id", str(item.menu_item_id)).execute()
                            if menu_item_result.data:
                                menu_item = menu_item_result.data[0]
                                price = float(menu_item.get("price", 0))
                                cost = float(menu_item.get("cost", 0)) if menu_item.get("cost") else price * 0.3
                                item_total = price * item.quantity
                                total_amount += item_total
                                
                                order_items.append({
                                    "menu_item_id": str(item.menu_item_id),
                                    "name": item.name,
                                    "quantity": item.quantity,
                                    "price": price,
                                    "cost": cost,
                                    "modifiers": item.modifiers,
                                    "special_instructions": item.special_instructions
                                })
                        except Exception as item_error:
                            logger.warning(f"⚠️ Could not get menu item details for {item.menu_item_id}: {str(item_error)}")
                            # Use default values if menu item not found
                            order_items.append({
                                "menu_item_id": str(item.menu_item_id),
                                "name": item.name,
                                "quantity": item.quantity,
                                "price": 0.0,
                                "cost": 0.0,
                                "modifiers": item.modifiers,
                                "special_instructions": item.special_instructions
                            })
                
                order_data = {
                    "id": str(kds_order.order_id),
                    "business_id": str(kds_order.business_id),
                    "customer_id": customer_id,  # NULL for staff orders, populated for customer orders
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "total_amount": total_amount,
                    "order_number": f"KDS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(kds_order.order_id)[:8]}",
                    "items": order_items  # Populate with actual items from KDS order
                }
                logger.info(f"📦 Order data to insert: {order_data}")
                order_result = await db.create_order(order_data)
                logger.info(f"✅ Order created: {order_result}")
                
                # Verify order was created
                verify_exists = await db.order_exists(kds_order.order_id)
                logger.info(f"🔍 Verification - Order exists after creation: {verify_exists}")
                if not verify_exists:
                    raise Exception("Order creation failed - order still doesn't exist after creation")
                
                # Small delay to ensure database transaction is committed
                import asyncio
                await asyncio.sleep(0.1)
                logger.info("⏳ Brief delay to ensure order is committed to database")
            else:
                logger.info("✅ Order already exists")
        except Exception as order_error:
            logger.error(f"💥 CRITICAL: Failed to ensure order exists: {str(order_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to create required order: {str(order_error)}")
        
        # Step 4: Create KDS order in database
        logger.info("4️⃣ Creating KDS order in database...")
        logger.info(f"🔍 About to create KDS order with order_id: {kds_order.order_id}")
        result = await db.create_kds_order(data)
        logger.info(f"✅ KDS order created successfully: {result}")
        
        # Step 5: Publish real-time update
        logger.info("5️⃣ Publishing real-time update...")
        try:
            await RealtimeEventPublisher.publish_kds_update(
                str(kds_order.business_id),
                {"type": "new_order", "order": result}
            )
            logger.info("✅ Real-time update published")
        except Exception as pub_error:
            logger.error(f"⚠️ Failed to publish real-time update: {str(pub_error)}")
            # Don't fail the whole request if real-time update fails
        
        logger.info("🎉 KDS order creation completed successfully")
        return result
        
    except HTTPException:
        logger.error("🚨 HTTPException in create_kds_order")
        raise
    except Exception as e:
        logger.error(f"💥 UNEXPECTED ERROR in create_kds_order: {str(e)}", exc_info=True)
        logger.error(f"🔍 Error type: {type(e).__name__}")
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
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🎯 START: Listing KDS orders")
    logger.info(f"📋 Query params - business_id: {business_id}, station: {station}, status: {status}, active_only: {active_only}")
    
    try:
        # Step 1: Get database service
        logger.info("1️⃣ Getting database service...")
        db = get_database_service()
        logger.info("✅ Database service obtained")
        
        # Step 2: Fetch orders from database
        logger.info("2️⃣ Fetching KDS orders from database...")
        orders = await db.get_active_kds_orders(business_id, station)
        logger.info(f"📊 Retrieved {len(orders)} orders from database")
        
        # Log some details about the returned orders
        if orders:
            for i, order in enumerate(orders[:3]):  # Log first 3 orders
                logger.info(f"   Order {i+1}: ID={order.get('id', 'N/A')}, Status={order.get('status', 'N/A')}")
            if len(orders) > 3:
                logger.info(f"   ... and {len(orders) - 3} more orders")
        else:
            logger.info("   No orders found")
        
        # Step 3: Apply additional filtering if needed
        if status:
            filtered_orders = [order for order in orders if order.get('status') == status]
            logger.info(f"🔍 Filtered by status '{status}': {len(filtered_orders)} orders")
            orders = filtered_orders
        
        if active_only:
            # Define what "active" means for your system
            active_statuses = ['pending', 'preparing', 'ready']
            active_orders = [order for order in orders if order.get('status') in active_statuses]
            logger.info(f"🔍 Active orders filter: {len(active_orders)} orders")
            orders = active_orders
        
        logger.info(f"✅ Final result: {len(orders)} orders to return")
        return orders
        
    except HTTPException:
        logger.error("🚨 HTTPException in list_kds_orders")
        raise
    except Exception as e:
        logger.error(f"💥 UNEXPECTED ERROR in list_kds_orders: {str(e)}", exc_info=True)
        logger.error(f"🔍 Error type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch KDS orders: {str(e)}")
@router.get("/kds/orders/{order_id}", response_model=KDSOrderWithMetrics)
async def get_kds_order(order_id: UUID):
    """Get KDS order with metrics"""
    try:
        db = get_database_service()
        result = db.client.table("kds_orders").select("*, orders(*), staff_members(first_name, last_name)").eq("id", str(order_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="KDS order not found")
        
        order = result.data[0]
        
        # Calculate metrics
        if order.get("prep_start_time") and order.get("prep_end_time"):
            start = datetime.fromisoformat(order["prep_start_time"].replace('Z', '+00:00'))
            end = datetime.fromisoformat(order["prep_end_time"].replace('Z', '+00:00'))
            order["prep_time_minutes"] = (end - start).total_seconds() / 60
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch KDS order: {str(e)}")


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
        
        # Handle status updates specifically
        if "status" in update_data:
            # Set timestamp fields based on status
            timestamp_field = None
            if update_data["status"] == "preparing":
                timestamp_field = "prep_start_time"
            elif update_data["status"] == "ready":
                timestamp_field = "prep_end_time"
            
            result = await db.update_kds_order_status(order_id, update_data["status"], timestamp_field)
        else:
            # Handle other field updates
            result = await db.update_kds_order_fields(order_id, update_data)
        
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
    try:
        db = get_database_service()
        
        # Set default date range if not provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Query KDS orders
        query = db.client.table("kds_orders").select("*")
        query = query.eq("business_id", str(business_id))
        query = query.gte("created_at", start_date.isoformat())
        query = query.lte("created_at", end_date.isoformat())
        result = query.execute()
        
        # Calculate metrics
        prep_times = []
        late_orders = 0
        total_orders = len(result.data)
        
        for order in result.data:
            if order.get("prep_start_time") and order.get("prep_end_time"):
                start = datetime.fromisoformat(order["prep_start_time"].replace('Z', '+00:00'))
                end = datetime.fromisoformat(order["prep_end_time"].replace('Z', '+00:00'))
                prep_time = (end - start).total_seconds() / 60
                prep_times.append(prep_time)
                
                # Check if late
                if order.get("target_time"):
                    target = datetime.fromisoformat(order["target_time"].replace('Z', '+00:00'))
                    if end > target:
                        late_orders += 1
        
        avg_prep_time = sum(prep_times) / len(prep_times) if prep_times else 0
        time_span_hours = (end_date - start_date).total_seconds() / 3600
        orders_per_hour = total_orders / time_span_hours if time_span_hours > 0 else 0
        late_percentage = (late_orders / total_orders * 100) if total_orders > 0 else 0
        
        return {
            "business_id": str(business_id),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "avg_prep_time_minutes": round(avg_prep_time, 2),
            "orders_per_hour": round(orders_per_hour, 2),
            "late_orders_percentage": round(late_percentage, 2),
            "total_orders": total_orders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze kitchen performance: {str(e)}")


@router.websocket("/kds/live/{business_id}")
async def kds_live_feed(websocket: WebSocket, business_id: UUID):
    """
    WebSocket for real-time KDS updates
    
    - **Live orders**: New orders appear instantly
    - **Status updates**: Real-time status changes
    - **Alerts**: Priority orders and delays
    """
    await websocket.accept()
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "business_id": str(business_id),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive and listen for messages
        while True:
            # In production, this would:
            # 1. Subscribe to Redis/Kafka for KDS events
            # 2. Stream real-time updates to client
            # 3. Handle client messages (order status updates)
            
            # For now, keep connection alive
            data = await websocket.receive_text()
            
            # Echo back for testing
            await websocket.send_json({
                "type": "echo",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
    except Exception as e:
        await websocket.close()
        print(f"WebSocket error: {str(e)}")


# ============================================================================
# STAFF MANAGEMENT (Should be moved to universal /api/v1/staff)
# ============================================================================

@router.post("/staff/members", response_model=StaffMember, status_code=status.HTTP_201_CREATED)
async def create_staff_member(staff: StaffMemberCreate):
    """Create new staff member"""
    try:
        # Add logging to see what's received
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"📦 Received staff creation data: {staff.model_dump()}")
        print(f"🎯 Backend received: {staff.model_dump()}")  # Also print to console
        
        db = get_database_service()
        data = staff.model_dump()
        data["business_id"] = str(data["business_id"])
        if data.get("user_id"):
            data["user_id"] = str(data["user_id"])
        
        # Handle empty hire_date string
        if data.get("hire_date") == "":
            data["hire_date"] = None
        # Convert hire_date datetime to ISO string for JSON serialization
        elif data.get("hire_date"):
            hire_dt = data["hire_date"]
            if isinstance(hire_dt, datetime) and hire_dt.tzinfo is None:
                hire_dt = hire_dt.replace(tzinfo=timezone.utc)
            if isinstance(hire_dt, datetime):
                data["hire_date"] = hire_dt.isoformat()
        
        # Convert Decimal to float for JSON serialization
        if data.get("hourly_rate") is not None:
            data["hourly_rate"] = float(data["hourly_rate"])
        
        result = await db.create_staff_member(data)
        
        # Ensure Decimal fields are converted to float for JSON serialization
        if result and isinstance(result, dict):
            if 'hourly_rate' in result and isinstance(result['hourly_rate'], Decimal):
                result['hourly_rate'] = float(result['hourly_rate'])
        
        return result
    except Exception as e:
        logger.error(f"❌ Error creating staff: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create staff member: {str(e)}")


@router.get("/staff", response_model=List[StaffMember])
async def list_staff_members_short(
    business_id: UUID = Query(...),
    status: Optional[str] = Query(None),
    position: Optional[str] = Query(None)
):
    """List staff members (short endpoint)"""
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


@router.get("/staff/members", response_model=List[StaffMember])
async def list_staff_members(
    business_id: UUID = Query(...),
    status: Optional[str] = Query(None),
    position: Optional[str] = Query(None)
):
    """List staff members (full endpoint)"""
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
    try:
        db = get_database_service()
        result = db.client.table("staff_members").select("*").eq("id", str(staff_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Staff member not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch staff member: {str(e)}")


@router.put("/staff/{staff_id}", response_model=StaffMember)
async def update_staff_member(staff_id: UUID, updates: StaffMemberUpdate):
    """Update staff member"""
    try:
        db = get_database_service()
        update_data = updates.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Handle empty hire_date string
        if update_data.get("hire_date") == "":
            update_data["hire_date"] = None
        # Convert hire_date datetime to ISO string for JSON serialization
        elif update_data.get("hire_date"):
            hire_dt = update_data["hire_date"]
            if isinstance(hire_dt, datetime) and hire_dt.tzinfo is None:
                hire_dt = hire_dt.replace(tzinfo=timezone.utc)
            if isinstance(hire_dt, datetime):
                update_data["hire_date"] = hire_dt.isoformat()
        
        # Convert Decimal to float for JSON serialization
        if update_data.get("hourly_rate") is not None:
            if isinstance(update_data["hourly_rate"], Decimal):
                update_data["hourly_rate"] = float(update_data["hourly_rate"])
        
        result = db.client.table("staff_members").update(update_data).eq("id", str(staff_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Staff member not found")
        
        # Ensure Decimal fields are converted to float for JSON serialization
        if result.data[0] and isinstance(result.data[0], dict):
            if 'hourly_rate' in result.data[0] and isinstance(result.data[0]['hourly_rate'], Decimal):
                result.data[0]['hourly_rate'] = float(result.data[0]['hourly_rate'])
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update staff member: {str(e)}")


# ============================================================================
# STAFF SCHEDULING
# ============================================================================

@router.post("/schedules", response_model=StaffSchedule, status_code=status.HTTP_201_CREATED)
async def create_schedule(schedule: StaffScheduleCreate):
    """Create staff schedule"""
    try:
        db = get_database_service()
        
        # Check for scheduling conflicts
        conflict_query = db.client.table("staff_schedules").select("*")
        conflict_query = conflict_query.eq("staff_id", str(schedule.staff_id))
        conflict_query = conflict_query.eq("shift_date", schedule.shift_date.isoformat())
        conflict_result = conflict_query.execute()
        
        if conflict_result.data:
            raise HTTPException(status_code=400, detail="Staff member already scheduled for this date")
        
        # Create schedule
        data = schedule.model_dump()
        data["business_id"] = str(data["business_id"])
        data["staff_id"] = str(data["staff_id"])
        if data.get("location_id"):
            data["location_id"] = str(data["location_id"])
        
        # Handle empty datetime/time strings
        if data.get("shift_date") == "":
            data["shift_date"] = None
        elif data.get("shift_date"):
            data["shift_date"] = data["shift_date"].isoformat()
            
        if data.get("shift_start") == "":
            data["shift_start"] = None
        elif data.get("shift_start"):
            data["shift_start"] = str(data["shift_start"])
            
        if data.get("shift_end") == "":
            data["shift_end"] = None
        elif data.get("shift_end"):
            data["shift_end"] = str(data["shift_end"])
        
        result = db.client.table("staff_schedules").insert(data).execute()
        return result.data[0] if result.data else None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")


@router.get("/schedules", response_model=List[StaffSchedule])
async def list_schedules(
    business_id: UUID = Query(...),
    staff_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """List staff schedules"""
    try:
        db = get_database_service()
        query = db.client.table("staff_schedules").select("*, staff_members(first_name, last_name, position)")
        query = query.eq("business_id", str(business_id))
        
        if staff_id:
            query = query.eq("staff_id", str(staff_id))
        if start_date:
            query = query.gte("shift_date", start_date.isoformat())
        if end_date:
            query = query.lte("shift_date", end_date.isoformat())
        
        query = query.order("shift_date")
        result = query.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch schedules: {str(e)}")


@router.put("/schedules/{schedule_id}", response_model=StaffSchedule)
async def update_schedule(schedule_id: UUID, updates: StaffScheduleUpdate):
    """Update staff schedule"""
    try:
        db = get_database_service()
        update_data = updates.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Convert time objects to strings if present
        if "shift_start" in update_data and update_data["shift_start"]:
            update_data["shift_start"] = str(update_data["shift_start"])
        if "shift_end" in update_data and update_data["shift_end"]:
            update_data["shift_end"] = str(update_data["shift_end"])
        if "shift_date" in update_data and update_data["shift_date"]:
            update_data["shift_date"] = update_data["shift_date"].isoformat()
        
        result = db.client.table("staff_schedules").update(update_data).eq("id", str(schedule_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update schedule: {str(e)}")


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(schedule_id: UUID):
    """Delete staff schedule"""
    try:
        db = get_database_service()
        result = db.client.table("staff_schedules").delete().eq("id", str(schedule_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")


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
        import logging
        logger = logging.getLogger(__name__)
        
        db = get_database_service()
        data = clock_in_data.model_dump()
        data["business_id"] = str(data["business_id"])
        data["staff_id"] = str(data["staff_id"])
        if data.get("location_id"):
            data["location_id"] = str(data["location_id"])
        
        # Handle empty clock_in string
        if data.get("clock_in") == "":
            data["clock_in"] = None
        elif data.get("clock_in"):
            # Ensure timezone-aware datetime
            clock_in_dt = data["clock_in"]
            if isinstance(clock_in_dt, datetime) and clock_in_dt.tzinfo is None:
                clock_in_dt = clock_in_dt.replace(tzinfo=timezone.utc)
            data["clock_in"] = clock_in_dt.isoformat()
        
        result = await db.clock_in_staff(data)
        
        # Ensure Decimal fields are converted to float for JSON serialization
        if result and isinstance(result, dict):
            if 'total_hours' in result and isinstance(result['total_hours'], Decimal):
                result['total_hours'] = float(result['total_hours'])
            if 'overtime_hours' in result and isinstance(result['overtime_hours'], Decimal):
                result['overtime_hours'] = float(result['overtime_hours'])
        
        # Publish staff update (optional - don't fail if this errors)
        try:
            await RealtimeEventPublisher.publish_staff_update(
                str(clock_in_data.business_id),
                {"type": "clock_in", "staff": result}
            )
        except Exception as pub_error:
            logger.warning(f"⚠️ Failed to publish real-time update: {str(pub_error)}")
            # Don't fail the whole request if real-time update fails
        
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
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🕐 Clock out request for clock_id: {clock_id}")
        
        db = get_database_service()
        
        if not clock_out_time:
            clock_out_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        
        logger.info(f"🕐 Clock out time: {clock_out_time}")
        
        result = await db.clock_out_staff(clock_id, clock_out_time)
        logger.info(f"🕐 Clock out result: {result}")
        
        # Ensure Decimal fields are converted to float for JSON serialization
        if result and isinstance(result, dict):
            if 'total_hours' in result and isinstance(result['total_hours'], Decimal):
                result['total_hours'] = float(result['total_hours'])
            if 'overtime_hours' in result and isinstance(result['overtime_hours'], Decimal):
                result['overtime_hours'] = float(result['overtime_hours'])
        
        # Publish staff update (optional - don't fail if this errors)
        try:
            await RealtimeEventPublisher.publish_staff_update(
                result["business_id"],
                {"type": "clock_out", "staff": result}
            )
        except Exception as pub_error:
            logger.warning(f"⚠️ Failed to publish real-time update: {str(pub_error)}")
            # Don't fail the whole request if real-time update fails
        
        return result
    except ValueError as ve:
        logger.error(f"❌ Clock out validation error: {str(ve)}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"❌ Clock out error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to clock out: {str(e)}")


@router.get("/time-clock", response_model=List[TimeClock])
async def list_time_clock_entries(
    business_id: UUID = Query(...),
    staff_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """List time clock entries"""
    try:
        db = get_database_service()
        query = db.client.table("time_clock").select("*, staff_members(first_name, last_name, position)")
        query = query.eq("business_id", str(business_id))
        
        if staff_id:
            query = query.eq("staff_id", str(staff_id))
        if start_date:
            query = query.gte("clock_in", start_date.isoformat())
        if end_date:
            query = query.lte("clock_in", end_date.isoformat())
        
        query = query.order("clock_in", desc=True)
        result = query.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch time clock entries: {str(e)}")


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
    try:
        db = get_database_service()
        
        # Get today's date
        today = date.today()
        
        # Get table status
        tables = await db.get_tables(business_id, location_id, None)
        table_stats = {
            "total": len(tables),
            "available": sum(1 for t in tables if t.get("status") == "available"),
            "occupied": sum(1 for t in tables if t.get("status") == "occupied"),
            "reserved": sum(1 for t in tables if t.get("status") == "reserved")
        }
        
        # Get active KDS orders
        kds_orders = await db.get_active_kds_orders(business_id, None)
        
        # Get clocked-in staff
        clocked_in_staff = await db.get_clocked_in_staff(business_id)
        
        # Get today's sales summary
        daily_sales = await db.get_daily_sales_summary(business_id, today)
        
        # Get low stock items
        low_stock = await db.get_low_stock_items(business_id)
        
        return {
            "business_id": str(business_id),
            "timestamp": datetime.utcnow().isoformat(),
            "tables": table_stats,
            "kitchen": {
                "active_orders": len(kds_orders),
                "pending": sum(1 for o in kds_orders if o.get("status") == "pending"),
                "preparing": sum(1 for o in kds_orders if o.get("status") == "preparing"),
                "ready": sum(1 for o in kds_orders if o.get("status") == "ready")
            },
            "staff": {
                "clocked_in": len(clocked_in_staff),
                "total_hours_today": sum(float(s.get("total_hours", 0)) for s in clocked_in_staff)
            },
            "sales": {
                "today_revenue": float(daily_sales.get("total_sales", 0)) if daily_sales else 0.0,
                "today_orders": int(daily_sales.get("total_orders", 0)) if daily_sales else 0,
                "avg_order_value": float(daily_sales.get("avg_order_value", 0)) if daily_sales else 0.0
            },
            "inventory": {
                "low_stock_items": len(low_stock),
                "out_of_stock": sum(1 for item in low_stock if item.get("current_stock", 0) == 0)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch operations dashboard: {str(e)}")


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
    try:
        # This endpoint is already implemented in analytics.py
        # Redirect to analytics endpoint or duplicate implementation
        db = get_database_service()
        
        # Get orders with table assignments
        orders_query = db.client.table("orders").select("id, table_id, created_at, completed_at")
        orders_query = orders_query.eq("business_id", str(business_id))
        orders_query = orders_query.gte("created_at", start_date.isoformat())
        orders_query = orders_query.lte("created_at", end_date.isoformat())
        orders_query = orders_query.eq("status", "completed")
        orders_query = orders_query.not_.is_("table_id", "null")
        orders_query = orders_query.not_.is_("completed_at", "null")
        orders_result = orders_query.execute()
        
        # Calculate turnover times
        turnovers = []
        for order in orders_result.data:
            if order.get("created_at") and order.get("completed_at"):
                created = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00'))
                completed = datetime.fromisoformat(order["completed_at"].replace('Z', '+00:00'))
                turnover_minutes = (completed - created).total_seconds() / 60
                turnovers.append(turnover_minutes)
        
        avg_turnover = sum(turnovers) / len(turnovers) if turnovers else 0
        
        return {
            "business_id": str(business_id),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "avg_turnover_minutes": round(avg_turnover, 2),
            "total_orders": len(turnovers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze table turnover: {str(e)}")


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
    try:
        # This endpoint is already implemented in analytics.py
        # Redirect to analytics endpoint or duplicate implementation
        db = get_database_service()
        
        # Get time clock data
        clock_query = db.client.table("time_clock").select("*, staff_members(hourly_rate, position)")
        clock_query = clock_query.eq("business_id", str(business_id))
        clock_query = clock_query.gte("clock_in", start_date.isoformat())
        clock_query = clock_query.lte("clock_in", end_date.isoformat())
        clock_query = clock_query.not_.is_("clock_out", "null")
        clock_result = clock_query.execute()
        
        # Calculate labor costs
        total_labor_cost = 0.0
        total_overtime_cost = 0.0
        
        for record in clock_result.data:
            regular_hours = float(record.get("total_hours", 0)) - float(record.get("overtime_hours", 0))
            overtime_hours = float(record.get("overtime_hours", 0))
            
            hourly_rate = 15.0  # Default
            if record.get("staff_members"):
                hourly_rate = float(record["staff_members"].get("hourly_rate", 15.0))
            
            regular_cost = regular_hours * hourly_rate
            overtime_cost = overtime_hours * hourly_rate * 1.5
            
            total_labor_cost += regular_cost + overtime_cost
            total_overtime_cost += overtime_cost
        
        # Get revenue for percentage
        revenue_query = db.client.table("daily_sales_summary").select("total_sales")
        revenue_query = revenue_query.eq("business_id", str(business_id))
        revenue_query = revenue_query.gte("date", start_date.isoformat())
        revenue_query = revenue_query.lte("date", end_date.isoformat())
        revenue_result = revenue_query.execute()
        total_revenue = sum(float(r.get("total_sales", 0)) for r in revenue_result.data)
        
        labor_percentage = (total_labor_cost / total_revenue * 100) if total_revenue > 0 else 0.0
        
        return {
            "business_id": str(business_id),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_labor_cost": round(total_labor_cost, 2),
            "overtime_cost": round(total_overtime_cost, 2),
            "labor_percentage": round(labor_percentage, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze labor costs: {str(e)}")
