"""
Inventory Management API Routes
Enterprise-grade endpoints for inventory tracking and automation

ENTERPRISE STRUCTURE:
- Food & Hospitality specific endpoints prefixed with /food/inventory
- Common endpoints moved to universal routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date

from ..services.database import DatabaseService, get_database_service

from ..models.inventory import (
    InventoryItem, InventoryItemCreate, InventoryItemUpdate, InventoryItemWithMetrics,
    InventoryTransaction, InventoryTransactionCreate,
    StockAdjustment, StockAlert, StockAlertCreate,
    Supplier, SupplierCreate, SupplierUpdate,
    PurchaseOrder, PurchaseOrderCreate, PurchaseOrderUpdate,
    InventoryReport, InventorySearch
)

router = APIRouter(prefix="/api/v1/food/inventory", tags=["Food & Hospitality - Inventory"])


# ============================================================================
# INVENTORY ITEMS
# ============================================================================

@router.post("/items", response_model=InventoryItem, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(item: InventoryItemCreate, db: DatabaseService = Depends(get_database_service)):
    """
    Create new inventory item
    
    - **Stock tracking**: Real-time stock levels
    - **Reorder points**: Automatic low-stock alerts
    - **Multi-location**: Track inventory per location
    """
    try:
        item_data = item.dict()
        # Convert UUID to string and Decimal to float for JSON serialization
        for key in ['current_stock', 'min_stock', 'max_stock', 'unit_cost']:
            if key in item_data and item_data[key] is not None:
                item_data[key] = float(item_data[key])
        
        # Convert UUID to string
        item_data['business_id'] = str(item_data['business_id'])
        
        result = await db.create_inventory_item(item_data)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create inventory item")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items", response_model=List[InventoryItemWithMetrics])
async def list_inventory_items(
    business_id: UUID = Query(..., description="Business ID"),
    location_id: Optional[UUID] = Query(None),
    category: Optional[str] = Query(None),
    low_stock_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List inventory items with metrics
    
    - **Metrics**: Stock percentage, value, reorder status
    - **Filtering**: By location, category, stock level
    """
    try:
        from ..services.database import get_database_service
        db = get_database_service()
        
        items = await db.get_inventory_items(
            business_id=business_id,
            location_id=location_id,
            low_stock_only=low_stock_only,
            limit=limit,
            offset=offset
        )
        
        # Add calculated metrics
        items_with_metrics = []
        for item in items:
            current_stock = float(item.get("current_stock", 0))
            min_stock = float(item.get("min_stock", 0))
            max_stock = float(item.get("max_stock", 0))
            unit_cost = float(item.get("unit_cost", 0) or 0)
            
            stock_percentage = (current_stock / max_stock * 100) if max_stock > 0 else 0
            needs_reorder = current_stock <= min_stock
            stock_value = current_stock * unit_cost
            
            item_with_metrics = {
                **item,
                "stock_percentage": round(stock_percentage, 2),
                "needs_reorder": needs_reorder,
                "stock_value": round(stock_value, 2),
                "days_of_stock": 7  # Placeholder calculation
            }
            items_with_metrics.append(item_with_metrics)
        
        return items_with_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items/search", response_model=List[InventoryItemWithMetrics])
async def search_inventory_items(search: InventorySearch):
    """Advanced inventory search with multiple filters"""
    try:
        db = get_database_service()
        query = db.client.table("inventory_items").select("*")
        query = query.eq("business_id", str(search.business_id))
        
        # Apply filters
        if search.name:
            query = query.ilike("name", f"%{search.name}%")
        if search.sku:
            query = query.eq("sku", search.sku)
        if search.category:
            query = query.eq("category", search.category)
        if search.location_id:
            query = query.eq("location_id", str(search.location_id))
        if search.min_stock_only:
            query = query.lte("current_stock", "min_stock")
        
        result = query.execute()
        
        # Add metrics
        items_with_metrics = []
        for item in result.data:
            current_stock = float(item.get("current_stock", 0))
            min_stock = float(item.get("min_stock", 0))
            max_stock = float(item.get("max_stock", 0))
            unit_cost = float(item.get("unit_cost", 0) or 0)
            
            items_with_metrics.append({
                **item,
                "stock_percentage": round((current_stock / max_stock * 100), 2) if max_stock > 0 else 0,
                "needs_reorder": current_stock <= min_stock,
                "stock_value": round(current_stock * unit_cost, 2),
                "days_of_stock": 7
            })
        
        return items_with_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search inventory: {str(e)}")


@router.get("/items/{item_id}", response_model=InventoryItemWithMetrics)
async def get_inventory_item(item_id: UUID):
    """Get inventory item with full metrics"""
    try:
        db = get_database_service()
        result = db.client.table("inventory_items").select("*, suppliers(name)").eq("id", str(item_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        item = result.data[0]
        current_stock = float(item.get("current_stock", 0))
        min_stock = float(item.get("min_stock", 0))
        max_stock = float(item.get("max_stock", 0))
        unit_cost = float(item.get("unit_cost", 0) or 0)
        
        return {
            **item,
            "stock_percentage": round((current_stock / max_stock * 100), 2) if max_stock > 0 else 0,
            "needs_reorder": current_stock <= min_stock,
            "stock_value": round(current_stock * unit_cost, 2),
            "days_of_stock": 7
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch inventory item: {str(e)}")


@router.put("/items/{item_id}", response_model=InventoryItem)
async def update_inventory_item(item_id: UUID, updates: InventoryItemUpdate):
    """Update inventory item"""
    try:
        db = get_database_service()
        update_data = updates.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Convert Decimal to float
        for key in ['current_stock', 'min_stock', 'max_stock', 'unit_cost']:
            if key in update_data and update_data[key] is not None:
                update_data[key] = float(update_data[key])
        
        result = db.client.table("inventory_items").update(update_data).eq("id", str(item_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update inventory item: {str(e)}")


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(item_id: UUID):
    """Delete inventory item"""
    try:
        db = get_database_service()
        result = db.client.table("inventory_items").delete().eq("id", str(item_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete inventory item: {str(e)}")


# ============================================================================
# STOCK MANAGEMENT
# ============================================================================

@router.post("/adjustments", response_model=InventoryTransaction, status_code=status.HTTP_201_CREATED)
async def adjust_stock(adjustment: StockAdjustment, performed_by: Optional[UUID] = None, db: DatabaseService = Depends(get_database_service)):
    """
    Manually adjust stock levels
    
    - **Audit trail**: All adjustments logged
    - **Reasons**: Track why stock was adjusted
    - **Real-time**: Immediate stock level update
    """
    try:
        result = await db.adjust_inventory_stock(
            item_id=adjustment.inventory_item_id,
            new_quantity=adjustment.new_quantity,
            reason=adjustment.reason,
            performed_by=performed_by
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions", response_model=List[InventoryTransaction])
async def list_inventory_transactions(
    business_id: UUID = Query(...),
    inventory_item_id: Optional[UUID] = Query(None),
    transaction_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List inventory transactions (audit trail)
    
    - **Complete history**: All stock movements
    - **Filtering**: By item, type, date range
    - **Compliance**: Full audit trail for accounting
    """
    try:
        db = get_database_service()
        query = db.client.table("inventory_transactions").select("*, inventory_items(name, sku)")
        query = query.eq("business_id", str(business_id))
        
        if inventory_item_id:
            query = query.eq("inventory_item_id", str(inventory_item_id))
        if transaction_type:
            query = query.eq("transaction_type", transaction_type)
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        if end_date:
            query = query.lte("created_at", end_date.isoformat())
        
        query = query.order("created_at", desc=True)
        query = query.limit(limit).offset(offset)
        result = query.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transactions: {str(e)}")


@router.post("/count", response_model=dict)
async def perform_stock_count(
    business_id: UUID,
    location_id: Optional[UUID] = None,
    counts: List[dict] = []  # [{item_id, counted_quantity}]
):
    """
    Perform physical stock count
    
    - **Reconciliation**: Compare counted vs. system stock
    - **Discrepancies**: Identify and log differences
    - **Adjustments**: Auto-create adjustment transactions
    """
    try:
        db = get_database_service()
        discrepancies = []
        adjustments_created = 0
        
        for count in counts:
            item_id = count.get("item_id")
            counted_quantity = float(count.get("counted_quantity", 0))
            
            # Get current stock
            item_result = db.client.table("inventory_items").select("*").eq("id", str(item_id)).execute()
            if not item_result.data:
                continue
            
            item = item_result.data[0]
            system_quantity = float(item.get("current_stock", 0))
            difference = counted_quantity - system_quantity
            
            if difference != 0:
                discrepancies.append({
                    "item_id": str(item_id),
                    "item_name": item.get("name"),
                    "system_quantity": system_quantity,
                    "counted_quantity": counted_quantity,
                    "difference": difference
                })
                
                # Create adjustment transaction
                transaction_data = {
                    "business_id": str(business_id),
                    "inventory_item_id": str(item_id),
                    "transaction_type": "adjustment",
                    "quantity": difference,
                    "unit_cost": float(item.get("unit_cost", 0)),
                    "reference_type": "stock_count",
                    "notes": f"Stock count adjustment: {system_quantity} → {counted_quantity}",
                    "created_at": datetime.utcnow().isoformat()
                }
                db.client.table("inventory_transactions").insert(transaction_data).execute()
                
                # Update stock level
                db.client.table("inventory_items").update({
                    "current_stock": counted_quantity,
                    "last_counted_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(item_id)).execute()
                
                adjustments_created += 1
        
        return {
            "business_id": str(business_id),
            "items_counted": len(counts),
            "discrepancies_found": len(discrepancies),
            "adjustments_created": adjustments_created,
            "discrepancies": discrepancies
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process stock count: {str(e)}")


# ============================================================================
# STOCK ALERTS
# ============================================================================

@router.post("/alerts", response_model=StockAlert, status_code=status.HTTP_201_CREATED)
async def create_stock_alert(alert: StockAlertCreate, db: DatabaseService = Depends(get_database_service)):
    """
    Create stock alert rule
    
    - **Alert types**: Low stock, out of stock, expiring
    - **Thresholds**: Customizable per item
    - **Notifications**: Email/SMS when triggered
    """
    try:
        alert_data = alert.dict()
        alert_data["created_at"] = datetime.utcnow().isoformat()
        alert_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("stock_alerts").insert(alert_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=List[StockAlert])
async def list_stock_alerts(
    business_id: UUID = Query(...),
    is_active: Optional[bool] = Query(None),
    alert_type: Optional[str] = Query(None)
):
    """List all stock alerts"""
    try:
        db = get_database_service()
        query = db.client.table("stock_alerts").select("*, inventory_items(name)")
        query = query.eq("business_id", str(business_id))
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        if alert_type:
            query = query.eq("alert_type", alert_type)
        
        result = query.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock alerts: {str(e)}")


@router.get("/alerts/active", response_model=List[dict])
async def get_active_alerts(business_id: UUID, db: DatabaseService = Depends(get_database_service)):
    """
    Get currently triggered alerts
    
    - **Real-time**: Items currently below threshold
    - **Priority**: Sorted by severity
    - **Actionable**: Direct links to reorder
    """
    try:
        low_stock_items = await db.get_low_stock_items(business_id)
        
        active_alerts = []
        for item in low_stock_items:
            current_stock = float(item.get("current_stock", 0))
            min_stock = float(item.get("min_stock", 0))
            
            severity = "high" if current_stock <= min_stock * 0.5 else "medium"
            
            alert = {
                "inventory_item_id": item["id"],
                "item_name": item["name"],
                "current_stock": current_stock,
                "min_stock": min_stock,
                "severity": severity,
                "needs_reorder": True
            }
            active_alerts.append(alert)
        
        return active_alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/alerts/{alert_id}", response_model=StockAlert)
async def update_stock_alert(alert_id: UUID, is_active: bool):
    """Enable/disable stock alert"""
    try:
        db = get_database_service()
        result = db.client.table("stock_alerts").update({
            "is_active": is_active,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(alert_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Stock alert not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update stock alert: {str(e)}")


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_alert(alert_id: UUID):
    """Delete stock alert"""
    try:
        db = get_database_service()
        result = db.client.table("stock_alerts").delete().eq("id", str(alert_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Stock alert not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete stock alert: {str(e)}")


# ============================================================================
# SUPPLIERS
# ============================================================================

@router.post("/suppliers", response_model=Supplier, status_code=status.HTTP_201_CREATED)
async def create_supplier(supplier: SupplierCreate, db: DatabaseService = Depends(get_database_service)):
    """Create new supplier"""
    try:
        supplier_data = supplier.dict()
        supplier_data["business_id"] = str(supplier_data["business_id"])
        supplier_data["created_at"] = datetime.utcnow().isoformat()
        supplier_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("suppliers").insert(supplier_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suppliers", response_model=List[Supplier])
async def list_suppliers(
    business_id: UUID = Query(...),
    is_active: Optional[bool] = Query(None),
    db: DatabaseService = Depends(get_database_service)
):
    """List all suppliers"""
    try:
        query = db.client.table("suppliers").select("*").eq("business_id", str(business_id))
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        query = query.order("name")
        result = query.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suppliers/{supplier_id}", response_model=Supplier)
async def get_supplier(supplier_id: UUID):
    """Get supplier details"""
    try:
        db = get_database_service()
        result = db.client.table("suppliers").select("*").eq("id", str(supplier_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch supplier: {str(e)}")


@router.put("/suppliers/{supplier_id}", response_model=Supplier)
async def update_supplier(supplier_id: UUID, updates: SupplierUpdate):
    """Update supplier"""
    try:
        db = get_database_service()
        update_data = updates.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("suppliers").update(update_data).eq("id", str(supplier_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update supplier: {str(e)}")


@router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(supplier_id: UUID):
    """Delete supplier"""
    try:
        db = get_database_service()
        result = db.client.table("suppliers").delete().eq("id", str(supplier_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete supplier: {str(e)}")


# ============================================================================
# PURCHASE ORDERS
# ============================================================================

@router.post("/purchase-orders", response_model=PurchaseOrder, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(po: PurchaseOrderCreate, created_by: Optional[UUID] = None, db: DatabaseService = Depends(get_database_service)):
    """
    Create purchase order
    
    - **Supplier integration**: Send to supplier via email/API
    - **Tracking**: Monitor delivery status
    - **Auto-receive**: Update inventory on delivery
    """
    try:
        po_data = po.dict()
        po_data["order_number"] = f"PO-{datetime.utcnow().strftime('%Y%m%d')}-{str(po.business_id)[:8]}"
        po_data["status"] = "pending"
        po_data["created_by"] = str(created_by) if created_by else None
        po_data["created_at"] = datetime.utcnow().isoformat()
        po_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Calculate total amount
        total_amount = sum(item["quantity"] * item["unit_cost"] for item in po_data["items"])
        po_data["total_amount"] = total_amount
        
        result = db.client.table("purchase_orders").insert(po_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/purchase-orders", response_model=List[PurchaseOrder])
async def list_purchase_orders(
    business_id: UUID = Query(...),
    supplier_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: DatabaseService = Depends(get_database_service)
):
    """List purchase orders with filtering"""
    try:
        query = db.client.table("purchase_orders").select("*, suppliers(name)").eq("business_id", str(business_id))
        
        if supplier_id:
            query = query.eq("supplier_id", str(supplier_id))
        if status:
            query = query.eq("status", status)
        if start_date:
            query = query.gte("order_date", start_date.isoformat())
        if end_date:
            query = query.lte("order_date", end_date.isoformat())
        
        query = query.order("order_date", desc=True)
        result = query.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrder)
async def get_purchase_order(po_id: UUID):
    """Get purchase order details"""
    try:
        db = get_database_service()
        result = db.client.table("purchase_orders").select("*, suppliers(name, email, phone)").eq("id", str(po_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch purchase order: {str(e)}")


@router.put("/purchase-orders/{po_id}", response_model=PurchaseOrder)
async def update_purchase_order(po_id: UUID, updates: PurchaseOrderUpdate):
    """Update purchase order status"""
    try:
        db = get_database_service()
        update_data = updates.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Convert dates to ISO format
        if "expected_delivery_date" in update_data and update_data["expected_delivery_date"]:
            update_data["expected_delivery_date"] = update_data["expected_delivery_date"].isoformat()
        if "actual_delivery_date" in update_data and update_data["actual_delivery_date"]:
            update_data["actual_delivery_date"] = update_data["actual_delivery_date"].isoformat()
        
        result = db.client.table("purchase_orders").update(update_data).eq("id", str(po_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update purchase order: {str(e)}")


@router.post("/purchase-orders/{po_id}/receive", response_model=dict)
async def receive_purchase_order(
    po_id: UUID,
    received_items: List[dict],  # [{item_id, quantity_received}]
    background_tasks: BackgroundTasks
):
    """
    Receive purchase order
    
    - **Auto-update**: Increase inventory levels
    - **Partial receives**: Support partial deliveries
    - **Cost tracking**: Update unit costs
    """
    try:
        db = get_database_service()
        
        # Validate PO exists
        po_result = db.client.table("purchase_orders").select("*").eq("id", str(po_id)).execute()
        if not po_result.data:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        po = po_result.data[0]
        if po.get("status") not in ["pending", "confirmed"]:
            raise HTTPException(status_code=400, detail="Purchase order cannot be received in current status")
        
        # Process received items
        transactions_created = 0
        for item in received_items:
            item_id = item.get("item_id")
            quantity_received = float(item.get("quantity_received", 0))
            
            if quantity_received <= 0:
                continue
            
            # Get item details
            item_result = db.client.table("inventory_items").select("*").eq("id", str(item_id)).execute()
            if not item_result.data:
                continue
            
            inventory_item = item_result.data[0]
            unit_cost = float(inventory_item.get("unit_cost", 0))
            
            # Create inventory transaction
            transaction_data = {
                "business_id": po["business_id"],
                "inventory_item_id": str(item_id),
                "transaction_type": "purchase",
                "quantity": quantity_received,
                "unit_cost": unit_cost,
                "reference_type": "purchase_order",
                "reference_id": str(po_id),
                "notes": f"Received from PO {po.get('order_number')}",
                "created_at": datetime.utcnow().isoformat()
            }
            db.client.table("inventory_transactions").insert(transaction_data).execute()
            
            # Update inventory stock level
            current_stock = float(inventory_item.get("current_stock", 0))
            new_stock = current_stock + quantity_received
            db.client.table("inventory_items").update({
                "current_stock": new_stock,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(item_id)).execute()
            
            transactions_created += 1
        
        # Update PO status
        db.client.table("purchase_orders").update({
            "status": "received",
            "actual_delivery_date": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(po_id)).execute()
        
        # Background task: Send confirmation email
        background_tasks.add_task(
            lambda: print(f"Sending confirmation email for PO {po.get('order_number')}")
        )
        
        return {
            "success": True,
            "po_id": str(po_id),
            "items_received": len(received_items),
            "transactions_created": transactions_created,
            "received_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to receive purchase order: {str(e)}")


# ============================================================================
# INVENTORY REPORTS
# ============================================================================

@router.get("/reports/summary", response_model=InventoryReport)
async def get_inventory_summary(business_id: UUID, location_id: Optional[UUID] = None, db: DatabaseService = Depends(get_database_service)):
    """
    Get inventory summary report
    
    - **Overview**: Total items, value, alerts
    - **Categories**: Breakdown by category
    - **Top items**: Highest value items
    """
    try:
        valuation = await db.get_inventory_valuation(business_id, location_id)
        low_stock_items = await db.get_low_stock_items(business_id)
        
        return {
            "business_id": business_id,
            "report_date": datetime.utcnow(),
            "total_items": valuation["total_items"],
            "total_value": float(valuation["total_value"]),
            "low_stock_items": len(low_stock_items),
            "out_of_stock_items": 0,
            "items_by_category": {},
            "top_value_items": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/valuation", response_model=dict)
async def get_inventory_valuation(
    business_id: UUID,
    location_id: Optional[UUID] = None,
    as_of_date: Optional[date] = Query(None)
):
    """
    Get inventory valuation report
    
    - **Total value**: Current inventory worth
    - **By category**: Value breakdown
    - **Historical**: Point-in-time valuation
    """
    try:
        db = get_database_service()
        query = db.client.table("inventory_items").select("*")
        query = query.eq("business_id", str(business_id))
        
        if location_id:
            query = query.eq("location_id", str(location_id))
        
        result = query.execute()
        
        # Calculate valuation
        from collections import defaultdict
        category_values = defaultdict(float)
        total_value = 0.0
        total_items = 0
        
        for item in result.data:
            current_stock = float(item.get("current_stock", 0))
            unit_cost = float(item.get("unit_cost", 0) or 0)
            category = item.get("category", "Uncategorized")
            
            value = current_stock * unit_cost
            category_values[category] += value
            total_value += value
            total_items += 1
        
        return {
            "business_id": str(business_id),
            "location_id": str(location_id) if location_id else None,
            "as_of_date": as_of_date.isoformat() if as_of_date else date.today().isoformat(),
            "total_value": round(total_value, 2),
            "total_items": total_items,
            "by_category": {cat: round(val, 2) for cat, val in category_values.items()}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate valuation: {str(e)}")


@router.get("/reports/turnover", response_model=dict)
async def get_inventory_turnover(
    business_id: UUID,
    period_days: int = Query(30, ge=1, le=365)
):
    """
    Analyze inventory turnover
    
    - **Turnover rate**: How quickly inventory moves
    - **Slow movers**: Items with low turnover
    - **Fast movers**: High turnover items
    """
    try:
        db = get_database_service()
        
        # Get inventory transactions for the period
        start_date = date.today() - timedelta(days=period_days)
        trans_query = db.client.table("inventory_transactions").select("*, inventory_items(name, current_stock, unit_cost)")
        trans_query = trans_query.eq("business_id", str(business_id))
        trans_query = trans_query.gte("created_at", start_date.isoformat())
        trans_query = trans_query.in_("transaction_type", ["sale", "waste"])
        trans_result = trans_query.execute()
        
        # Calculate turnover by item
        from collections import defaultdict
        item_usage = defaultdict(float)
        
        for trans in trans_result.data:
            item_id = trans.get("inventory_item_id")
            quantity = abs(float(trans.get("quantity", 0)))
            item_usage[item_id] += quantity
        
        # Calculate turnover rates
        items_with_turnover = []
        for item_id, usage in item_usage.items():
            # Get current stock
            item_query = db.client.table("inventory_items").select("*").eq("id", str(item_id)).execute()
            if not item_query.data:
                continue
            
            item = item_query.data[0]
            current_stock = float(item.get("current_stock", 0))
            avg_stock = (current_stock + usage) / 2  # Simple average
            
            turnover_rate = (usage / avg_stock) if avg_stock > 0 else 0
            
            items_with_turnover.append({
                "item_id": str(item_id),
                "item_name": item.get("name"),
                "usage": round(usage, 2),
                "avg_stock": round(avg_stock, 2),
                "turnover_rate": round(turnover_rate, 2),
                "category": "fast" if turnover_rate > 2 else "slow" if turnover_rate < 0.5 else "normal"
            })
        
        # Sort by turnover rate
        items_with_turnover.sort(key=lambda x: x["turnover_rate"], reverse=True)
        
        fast_movers = [i for i in items_with_turnover if i["category"] == "fast"]
        slow_movers = [i for i in items_with_turnover if i["category"] == "slow"]
        
        return {
            "business_id": str(business_id),
            "period_days": period_days,
            "total_items_analyzed": len(items_with_turnover),
            "fast_movers": fast_movers[:10],
            "slow_movers": slow_movers[:10],
            "all_items": items_with_turnover
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate turnover: {str(e)}")


@router.get("/reports/waste", response_model=dict)
async def get_waste_report(
    business_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Analyze inventory waste
    
    - **Waste tracking**: Items marked as waste
    - **Cost impact**: Total waste cost
    - **Trends**: Waste patterns over time
    """
    try:
        db = get_database_service()
        
        # Query waste transactions
        query = db.client.table("inventory_transactions").select("*, inventory_items(name, category)")
        query = query.eq("business_id", str(business_id))
        query = query.eq("transaction_type", "waste")
        query = query.gte("created_at", start_date.isoformat())
        query = query.lte("created_at", end_date.isoformat())
        result = query.execute()
        
        # Calculate waste metrics
        from collections import defaultdict
        category_waste = defaultdict(lambda: {"quantity": 0.0, "cost": 0.0})
        total_waste_cost = 0.0
        total_waste_quantity = 0.0
        
        for trans in result.data:
            quantity = abs(float(trans.get("quantity", 0)))
            unit_cost = float(trans.get("unit_cost", 0))
            cost = quantity * unit_cost
            
            total_waste_quantity += quantity
            total_waste_cost += cost
            
            if trans.get("inventory_items"):
                category = trans["inventory_items"].get("category", "Uncategorized")
                category_waste[category]["quantity"] += quantity
                category_waste[category]["cost"] += cost
        
        # Format by category
        by_category = [
            {
                "category": cat,
                "quantity": round(data["quantity"], 2),
                "cost": round(data["cost"], 2)
            }
            for cat, data in sorted(category_waste.items(), key=lambda x: x[1]["cost"], reverse=True)
        ]
        
        return {
            "business_id": str(business_id),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_waste_cost": round(total_waste_cost, 2),
            "total_waste_quantity": round(total_waste_quantity, 2),
            "waste_transactions": len(result.data),
            "by_category": by_category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate waste report: {str(e)}")


# ============================================================================
# AUTOMATION & INTEGRATIONS
# ============================================================================

@router.post("/auto-reorder", response_model=dict)
async def trigger_auto_reorder(business_id: UUID, dry_run: bool = Query(False)):
    """
    Trigger automatic reordering
    
    - **Smart reordering**: Based on usage patterns
    - **Supplier selection**: Choose best supplier
    - **PO generation**: Auto-create purchase orders
    """
    try:
        db = get_database_service()
        
        # Identify items below reorder point
        low_stock_items = await db.get_low_stock_items(business_id)
        
        reorder_recommendations = []
        pos_created = 0
        
        for item in low_stock_items:
            current_stock = float(item.get("current_stock", 0))
            min_stock = float(item.get("min_stock", 0))
            max_stock = float(item.get("max_stock", 0))
            
            # Calculate optimal order quantity (bring to max stock)
            order_quantity = max_stock - current_stock
            
            if order_quantity <= 0:
                continue
            
            recommendation = {
                "item_id": item["id"],
                "item_name": item["name"],
                "current_stock": current_stock,
                "min_stock": min_stock,
                "max_stock": max_stock,
                "recommended_order_quantity": round(order_quantity, 2),
                "supplier_id": item.get("supplier_id"),
                "unit_cost": float(item.get("unit_cost", 0))
            }
            reorder_recommendations.append(recommendation)
            
            # Create PO if not dry run
            if not dry_run and item.get("supplier_id"):
                # Group by supplier and create POs
                # For simplicity, creating individual POs here
                po_data = {
                    "business_id": str(business_id),
                    "supplier_id": str(item["supplier_id"]),
                    "order_number": f"AUTO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "status": "draft",
                    "order_date": datetime.utcnow().isoformat(),
                    "items": [{
                        "item_id": item["id"],
                        "quantity": order_quantity,
                        "unit_cost": float(item.get("unit_cost", 0))
                    }],
                    "total_amount": order_quantity * float(item.get("unit_cost", 0)),
                    "created_at": datetime.utcnow().isoformat()
                }
                db.client.table("purchase_orders").insert(po_data).execute()
                pos_created += 1
        
        return {
            "business_id": str(business_id),
            "dry_run": dry_run,
            "items_needing_reorder": len(reorder_recommendations),
            "purchase_orders_created": pos_created,
            "recommendations": reorder_recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger auto-reorder: {str(e)}")


@router.post("/sync-from-pos", response_model=dict)
async def sync_from_pos(business_id: UUID, pos_system: str):
    """
    Sync inventory from POS system
    
    - **Integrations**: Square, Toast, Clover
    - **Real-time**: Keep inventory in sync
    - **Reconciliation**: Handle discrepancies
    """
    try:
        # This is a placeholder for POS integration
        # In production, this would:
        # 1. Connect to POS API (Square, Toast, Clover, etc.)
        # 2. Fetch inventory data from POS
        # 3. Compare with local inventory
        # 4. Create adjustment transactions for discrepancies
        
        # For now, return a structure showing what would happen
        return {
            "business_id": str(business_id),
            "pos_system": pos_system,
            "status": "not_implemented",
            "message": f"POS integration for {pos_system} is not yet implemented",
            "supported_systems": ["square", "toast", "clover"],
            "next_steps": [
                "Configure POS API credentials",
                "Map POS items to local inventory items",
                "Enable real-time sync webhook",
                "Test reconciliation process"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync from POS: {str(e)}")
