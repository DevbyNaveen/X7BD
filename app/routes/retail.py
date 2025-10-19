"""
API Routes for Retail Template
(Retail Store, Boutique, Grocery Store, Pharmacy, Electronics Store, etc.)

ENTERPRISE STRUCTURE:
- Common endpoints (customers, staff, time-clock) moved to universal routes
- Category-specific endpoints prefixed with /retail
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..models.retail import (
    ProductCreate, ProductUpdate, ProductResponse,
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerAnalyticsResponse
)
from ..services.database import get_database_service

router = APIRouter(prefix="/api/v1/retail", tags=["Retail Template"])


# ============================================================================
# PRODUCTS ENDPOINTS
# ============================================================================

@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(product: ProductCreate):
    """Create a new product"""
    db = get_database_service()
    
    try:
        result = db.client.table("products").insert({
            "business_id": str(product.business_id),
            "name": product.name,
            "description": product.description,
            "sku": product.sku,
            "barcode": product.barcode,
            "category": product.category,
            "brand": product.brand,
            "price": product.price,
            "cost": product.cost,
            "compare_at_price": product.compare_at_price,
            "tax_rate": product.tax_rate,
            "weight": product.weight,
            "weight_unit": product.weight_unit,
            "dimensions": product.dimensions,
            "image_urls": product.image_urls,
            "is_available": product.is_available,
            "track_inventory": product.track_inventory,
            "inventory_quantity": product.inventory_quantity,
            "low_stock_threshold": product.low_stock_threshold,
            "tags": product.tags,
            "variants": product.variants,
            "metadata": product.metadata
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create product")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    business_id: UUID = Query(..., description="Business ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    low_stock: Optional[bool] = Query(None, description="Show only low stock items"),
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all products for a business"""
    db = get_database_service()
    
    try:
        query = db.client.table("products").select("*").eq("business_id", str(business_id))
        
        if category:
            query = query.eq("category", category)
        if brand:
            query = query.eq("brand", brand)
        if is_available is not None:
            query = query.eq("is_available", is_available)
        
        query = query.range(offset, offset + limit - 1).order("created_at", desc=True)
        result = query.execute()
        
        products = result.data if result.data else []
        
        # Filter low stock items if requested
        if low_stock:
            products = [p for p in products if p.get("inventory_quantity", 0) <= p.get("low_stock_threshold", 10)]
        
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: UUID):
    """Get a specific product by ID"""
    db = get_database_service()
    
    try:
        result = db.client.table("products").select("*").eq("id", str(product_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: UUID, product: ProductUpdate):
    """Update a product"""
    db = get_database_service()
    
    try:
        update_data = {k: v for k, v in product.dict(exclude_unset=True).items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("products").update(update_data).eq("id", str(product_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/products/{product_id}", status_code=204)
async def delete_product(product_id: UUID):
    """Delete a product"""
    db = get_database_service()
    
    try:
        result = db.client.table("products").delete().eq("id", str(product_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/{product_id}/adjust-inventory")
async def adjust_product_inventory(
    product_id: UUID,
    adjustment: int = Query(..., description="Quantity to add (positive) or remove (negative)")
):
    """Adjust product inventory quantity"""
    db = get_database_service()
    
    try:
        # Get current product
        result = db.client.table("products").select("*").eq("id", str(product_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product = result.data[0]
        current_qty = product.get("inventory_quantity", 0)
        new_qty = max(0, current_qty + adjustment)
        
        # Update inventory
        update_result = db.client.table("products").update({
            "inventory_quantity": new_qty,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(product_id)).execute()
        
        return {
            "success": True,
            "product_id": str(product_id),
            "previous_quantity": current_qty,
            "adjustment": adjustment,
            "new_quantity": new_qty
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NOTE: Customer management moved to universal /api/v1/customers
# This eliminates duplication across templates
# Loyalty points endpoint kept here as it's retail-specific
# ============================================================================


# ============================================================================
# PRODUCT CATEGORIES ENDPOINTS
# ============================================================================

@router.post("/categories", response_model=dict, status_code=201)
async def create_product_category(category: dict):
    """Create product category (like menu categories for food)"""
    db = get_database_service()
    
    try:
        result = db.client.table("product_categories").insert({
            "business_id": str(category["business_id"]),
            "name": category["name"],
            "description": category.get("description"),
            "parent_id": str(category.get("parent_id")) if category.get("parent_id") else None,
            "display_order": category.get("display_order", 0),
            "is_active": category.get("is_active", True),
            "image_url": category.get("image_url")
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create category")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories", response_model=list)
async def list_product_categories(
    business_id: UUID = Query(..., description="Business ID"),
    parent_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all product categories"""
    db = get_database_service()
    
    try:
        query = db.client.table("product_categories").select("*").eq("business_id", str(business_id))
        
        if parent_id:
            query = query.eq("parent_id", str(parent_id))
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        query = query.range(offset, offset + limit - 1).order("display_order")
        result = query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/{category_id}", response_model=dict)
async def get_product_category(category_id: UUID):
    """Get product category by ID"""
    db = get_database_service()
    
    try:
        result = db.client.table("product_categories").select("*").eq("id", str(category_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/categories/{category_id}", response_model=dict)
async def update_product_category(category_id: UUID, updates: dict):
    """Update product category"""
    db = get_database_service()
    
    try:
        update_data = {k: v for k, v in updates.items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("product_categories").update(update_data).eq("id", str(category_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/categories/{category_id}", status_code=204)
async def delete_product_category(category_id: UUID):
    """Delete product category"""
    db = get_database_service()
    
    try:
        result = db.client.table("product_categories").delete().eq("id", str(category_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SUPPLIERS ENDPOINTS
# ============================================================================

@router.post("/suppliers", response_model=dict, status_code=201)
async def create_supplier(supplier: dict):
    """Create supplier"""
    db = get_database_service()
    
    try:
        result = db.client.table("suppliers").insert({
            "business_id": str(supplier["business_id"]),
            "name": supplier["name"],
            "contact_name": supplier.get("contact_name"),
            "email": supplier.get("email"),
            "phone": supplier.get("phone"),
            "address": supplier.get("address"),
            "payment_terms": supplier.get("payment_terms"),
            "is_active": supplier.get("is_active", True),
            "notes": supplier.get("notes")
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create supplier")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suppliers", response_model=list)
async def list_suppliers(
    business_id: UUID = Query(..., description="Business ID"),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all suppliers"""
    db = get_database_service()
    
    try:
        query = db.client.table("suppliers").select("*").eq("business_id", str(business_id))
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        query = query.range(offset, offset + limit - 1).order("name")
        result = query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suppliers/{supplier_id}", response_model=dict)
async def get_supplier(supplier_id: UUID):
    """Get supplier by ID"""
    db = get_database_service()
    
    try:
        result = db.client.table("suppliers").select("*").eq("id", str(supplier_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/suppliers/{supplier_id}", response_model=dict)
async def update_supplier(supplier_id: UUID, updates: dict):
    """Update supplier"""
    db = get_database_service()
    
    try:
        update_data = {k: v for k, v in updates.items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("suppliers").update(update_data).eq("id", str(supplier_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/suppliers/{supplier_id}", status_code=204)
async def delete_supplier(supplier_id: UUID):
    """Delete supplier"""
    db = get_database_service()
    
    try:
        result = db.client.table("suppliers").delete().eq("id", str(supplier_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PURCHASE ORDERS ENDPOINTS
# ============================================================================

@router.post("/purchase-orders", response_model=dict, status_code=201)
async def create_purchase_order(po: dict):
    """Create purchase order"""
    db = get_database_service()
    
    try:
        result = db.client.table("purchase_orders").insert({
            "business_id": str(po["business_id"]),
            "supplier_id": str(po["supplier_id"]),
            "order_number": f"PO-{datetime.utcnow().strftime('%Y%m%d')}-{str(po['business_id'])[:8]}",
            "order_date": po.get("order_date", datetime.utcnow().isoformat()),
            "expected_delivery_date": po.get("expected_delivery_date"),
            "status": po.get("status", "pending"),
            "items": po["items"],
            "total_amount": po["total_amount"],
            "notes": po.get("notes")
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create purchase order")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/purchase-orders", response_model=list)
async def list_purchase_orders(
    business_id: UUID = Query(..., description="Business ID"),
    supplier_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all purchase orders"""
    db = get_database_service()
    
    try:
        query = db.client.table("purchase_orders").select("*").eq("business_id", str(business_id))
        
        if supplier_id:
            query = query.eq("supplier_id", str(supplier_id))
        if status:
            query = query.eq("status", status)
        
        query = query.range(offset, offset + limit - 1).order("order_date", desc=True)
        result = query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/purchase-orders/{po_id}", response_model=dict)
async def get_purchase_order(po_id: UUID):
    """Get purchase order by ID"""
    db = get_database_service()
    
    try:
        result = db.client.table("purchase_orders").select("*").eq("id", str(po_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/purchase-orders/{po_id}", response_model=dict)
async def update_purchase_order(po_id: UUID, updates: dict):
    """Update purchase order"""
    db = get_database_service()
    
    try:
        update_data = {k: v for k, v in updates.items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update the purchase order
        result = db.client.table("purchase_orders").update(update_data).eq("id", str(po_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        # Fetch the updated purchase order with supplier information
        updated_po = db.client.table("purchase_orders").select("*, suppliers(name, email, phone)").eq("id", str(po_id)).execute()
        
        if not updated_po.data:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        # Flatten the supplier data for frontend compatibility
        po_data = updated_po.data[0]
        if 'suppliers' in po_data and po_data['suppliers']:
            supplier = po_data['suppliers']
            po_data['supplier_name'] = supplier.get('name')
            po_data['supplier_email'] = supplier.get('email')
            po_data['supplier_phone'] = supplier.get('phone')
        
        return po_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/purchase-orders/{po_id}/receive", response_model=dict)
async def receive_purchase_order(po_id: UUID, received_items: dict):
    """Receive purchase order and update inventory"""
    db = get_database_service()
    
    try:
        # Update PO status
        db.client.table("purchase_orders").update({
            "status": "received",
            "received_date": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(po_id)).execute()
        
        # Update product inventory quantities
        for item in received_items.get("items", []):
            product_id = item["product_id"]
            quantity = item["quantity_received"]
            
            # Get current inventory
            product = db.client.table("products").select("*").eq("id", str(product_id)).execute()
            if product.data:
                current_qty = product.data[0].get("inventory_quantity", 0)
                new_qty = current_qty + quantity
                
                db.client.table("products").update({
                    "inventory_quantity": new_qty,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(product_id)).execute()
        
        return {"success": True, "message": "Purchase order received and inventory updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STOCK ALERTS ENDPOINTS
# ============================================================================

@router.post("/stock-alerts", response_model=dict, status_code=201)
async def create_stock_alert(alert: dict):
    """Create stock alert for low inventory"""
    db = get_database_service()
    
    try:
        # Enterprise-grade: Handle both inventory_item_id and product_id gracefully
        inventory_item_id = alert.get("inventory_item_id") or alert.get("product_id")
        
        insert_data = {
            "business_id": str(alert["business_id"]),
            "alert_type": alert.get("alert_type", "low_stock"),
            "threshold": alert["threshold"],
            "is_active": alert.get("is_active", True)
        }
        
        # Only add inventory_item_id if provided
        if inventory_item_id:
            insert_data["inventory_item_id"] = str(inventory_item_id)
        
        result = db.client.table("stock_alerts").insert(insert_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create alert")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock-alerts", response_model=list)
async def list_stock_alerts(
    business_id: UUID = Query(..., description="Business ID"),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all stock alerts"""
    db = get_database_service()
    
    try:
        query = db.client.table("stock_alerts").select("*").eq("business_id", str(business_id))
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        query = query.range(offset, offset + limit - 1).order("created_at", desc=True)
        result = query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock-alerts/active", response_model=list)
async def get_active_stock_alerts(business_id: UUID = Query(...)):
    """Get currently triggered stock alerts"""
    db = get_database_service()
    
    try:
        # Get all active alerts
        alerts = db.client.table("stock_alerts").select("*").eq("business_id", str(business_id)).eq("is_active", True).execute()
        
        active_alerts = []
        for alert in alerts.data if alerts.data else []:
            product = alert.get("products")
            if product and product.get("inventory_quantity", 0) <= alert["threshold"]:
                active_alerts.append({
                    "alert_id": alert["id"],
                    "product_id": alert["product_id"],
                    "product_name": product.get("name"),
                    "current_quantity": product.get("inventory_quantity", 0),
                    "threshold": alert["threshold"],
                    "alert_type": alert["alert_type"]
                })
        
        return active_alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROMOTIONS ENDPOINTS
# ============================================================================

@router.post("/promotions", response_model=dict, status_code=201)
async def create_promotion(promotion: dict):
    """Create promotion/discount"""
    db = get_database_service()
    
    try:
        result = db.client.table("promotions").insert({
            "business_id": str(promotion["business_id"]),
            "name": promotion["name"],
            "description": promotion.get("description"),
            "promotion_type": promotion["promotion_type"],
            "discount_type": promotion.get("discount_type", "percentage"),
            "discount_value": promotion["discount_value"],
            "start_date": promotion["start_date"],
            "end_date": promotion["end_date"],
            "applicable_products": promotion.get("applicable_products", []),
            "applicable_categories": promotion.get("applicable_categories", []),
            "min_purchase_amount": promotion.get("min_purchase_amount"),
            "max_discount_amount": promotion.get("max_discount_amount"),
            "usage_limit": promotion.get("usage_limit"),
            "is_active": promotion.get("is_active", True)
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create promotion")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/promotions", response_model=list)
async def list_promotions(
    business_id: UUID = Query(..., description="Business ID"),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all promotions"""
    db = get_database_service()
    
    try:
        query = db.client.table("promotions").select("*").eq("business_id", str(business_id))
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        query = query.range(offset, offset + limit - 1).order("start_date", desc=True)
        result = query.execute()
        
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RETAIL ANALYTICS ENDPOINTS (Category-Specific)
# ============================================================================

@router.get("/analytics/product-performance", response_model=dict)
async def get_product_performance(
    business_id: UUID = Query(...),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Analyze product sales performance"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "top_products": [],
        "revenue_by_product": {},
        "units_sold": {}
    }


@router.get("/analytics/inventory-turnover", response_model=dict)
async def get_inventory_turnover(
    business_id: UUID = Query(...),
    period_days: int = Query(30, ge=1, le=365)
):
    """Calculate inventory turnover rate"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "turnover_rate": 0.0,
        "fast_movers": [],
        "slow_movers": []
    }


@router.get("/analytics/category-performance", response_model=dict)
async def get_category_performance(
    business_id: UUID = Query(...),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Analyze sales by product category"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "categories": [],
        "revenue_by_category": {}
    }


@router.get("/analytics/profit-margins", response_model=dict)
async def get_profit_margins(
    business_id: UUID = Query(...)
):
    """Analyze profit margins across products"""
    # TODO: Implement analytics
    return {
        "business_id": str(business_id),
        "overall_margin": 0.0,
        "high_margin_products": [],
        "low_margin_products": []
    }


# ============================================================================
# LOYALTY POINTS ENDPOINT (Retail-Specific)
# ============================================================================

@router.post("/loyalty-points/{customer_id}")
async def adjust_loyalty_points(
    customer_id: UUID,
    points: int = Query(..., description="Points to add (positive) or remove (negative)")
):
    """Adjust customer loyalty points (Retail-specific feature)"""
    db = get_database_service()
    
    try:
        # Get current customer
        result = db.client.table("customers").select("*").eq("id", str(customer_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer = result.data[0]
        current_points = customer.get("loyalty_points", 0)
        new_points = max(0, current_points + points)
        
        # Update loyalty points
        update_result = db.client.table("customers").update({
            "loyalty_points": new_points,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(customer_id)).execute()
        
        return {
            "success": True,
            "customer_id": str(customer_id),
            "previous_points": current_points,
            "adjustment": points,
            "new_points": new_points
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
