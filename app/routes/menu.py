"""
Menu Management API Routes
Enterprise-grade endpoints for menu CRUD operations
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from ..models.menu import (
    MenuCategory, MenuCategoryCreate, MenuCategoryUpdate,
    MenuItem, MenuItemCreate, MenuItemUpdate, MenuItemWithDetails,
    ItemModifier, ItemModifierCreate, ItemModifierUpdate,
    BulkMenuItemUpdate, MenuItemSearch, MenuImport
)
from ..services.database import get_database_service
from ..services.realtime import RealtimeEventPublisher

router = APIRouter(prefix="/api/v1/menu", tags=["menu"])


# ============================================================================
# MENU CATEGORIES
# ============================================================================

@router.post("/categories", response_model=MenuCategory, status_code=status.HTTP_201_CREATED)
async def create_menu_category(category: MenuCategoryCreate):
    """
    Create a new menu category
    
    - **Hierarchical support**: Can have parent categories
    - **Display order**: Control category ordering
    - **Icons**: Optional icon URLs for visual representation
    """
    try:
        db = get_database_service()
        data = category.model_dump()
        data["business_id"] = str(data["business_id"])
        if data.get("parent_id"):
            data["parent_id"] = str(data["parent_id"])
        
        result = await db.create_menu_category(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create category: {str(e)}")


@router.get("/categories", response_model=List[MenuCategory])
async def list_menu_categories(
    business_id: UUID = Query(..., description="Business ID"),
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """
    List all menu categories for a business
    
    - **Hierarchical**: Returns categories with parent-child relationships
    - **Filtering**: Filter by parent or active status
    """
    try:
        db = get_database_service()
        categories = await db.get_menu_categories(business_id, parent_id, is_active)
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch categories: {str(e)}")


@router.get("/categories/{category_id}", response_model=MenuCategory)
async def get_menu_category(category_id: UUID):
    """Get menu category by ID"""
    try:
        db = get_database_service()
        result = db.client.table("menu_categories").select("*").eq("id", str(category_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Category not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch category: {str(e)}")


@router.put("/categories/{category_id}", response_model=MenuCategory)
async def update_menu_category(category_id: UUID, updates: MenuCategoryUpdate):
    """Update menu category"""
    try:
        db = get_database_service()
        update_data = updates.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("menu_categories").update(update_data).eq("id", str(category_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Category not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update category: {str(e)}")


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_category(category_id: UUID):
    """
    Delete menu category
    
    - **Cascade handling**: Items in category will have category_id set to NULL
    - **Soft delete option**: Can be implemented for data retention
    """
    try:
        db = get_database_service()
        result = db.client.table("menu_categories").delete().eq("id", str(category_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Category not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete category: {str(e)}")


# ============================================================================
# MENU ITEMS
# ============================================================================

@router.post("/items", response_model=MenuItem, status_code=status.HTTP_201_CREATED)
async def create_menu_item(item: MenuItemCreate):
    """
    Create a new menu item
    
    - **Full customization**: Price, cost, variants, modifiers
    - **Availability**: Time-based and location-based availability
    - **Rich metadata**: Images, allergens, nutrition info
    """
    try:
        db = get_database_service()
        data = item.model_dump()
        data["business_id"] = str(data["business_id"])
        if data.get("category_id"):
            data["category_id"] = str(data["category_id"])
        
        # Convert decimal to float for JSON
        data["price"] = float(data["price"])
        if data.get("cost"):
            data["cost"] = float(data["cost"])
        
        # Convert UUIDs in lists
        data["modifiers"] = [str(m) for m in data.get("modifiers", [])]
        data["locations"] = [str(l) for l in data.get("locations", [])]
        
        result = await db.create_menu_item(data)
        
        # Publish real-time update
        await RealtimeEventPublisher.publish_order_update(
            str(item.business_id),
            {"type": "menu_item_created", "item": result}
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create menu item: {str(e)}")


@router.get("/items", response_model=List[MenuItem])
async def list_menu_items(
    business_id: UUID = Query(..., description="Business ID"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List menu items with filtering and pagination
    
    - **Search**: Full-text search on name and description
    - **Filtering**: By category, availability, tags
    - **Pagination**: Efficient for large menus
    """
    try:
        db = get_database_service()
        query = db.client.table("menu_items").select("*").eq("business_id", str(business_id))
        
        if category_id:
            query = query.eq("category_id", str(category_id))
        if is_available is not None:
            query = query.eq("is_available", is_available)
        if search:
            query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")
        
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch menu items: {str(e)}")


@router.post("/items/search", response_model=List[MenuItem])
async def search_menu_items(search: MenuItemSearch):
    """
    Advanced menu item search
    
    - **Multi-criteria**: Search by multiple fields
    - **Price range**: Filter by min/max price
    - **Tags**: Filter by tags
    """
    # TODO: Implement advanced search
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.get("/items/{item_id}", response_model=MenuItemWithDetails)
async def get_menu_item(item_id: UUID, include_modifiers: bool = Query(True)):
    """
    Get menu item with full details
    
    - **Complete data**: Includes category and modifier details
    - **Profit margin**: Automatically calculated
    """
    try:
        db = get_database_service()
        item = await db.get_menu_item_with_details(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch menu item: {str(e)}")


@router.put("/items/{item_id}", response_model=MenuItem)
async def update_menu_item(item_id: UUID, updates: MenuItemUpdate):
    """
    Update menu item
    
    - **Partial updates**: Only update provided fields
    - **Validation**: Price, cost, and inventory checks
    """
    try:
        db = get_database_service()
        update_data = updates.model_dump(exclude_unset=True)
        
        # Convert decimals to float
        if "price" in update_data:
            update_data["price"] = float(update_data["price"])
        if "cost" in update_data and update_data["cost"]:
            update_data["cost"] = float(update_data["cost"])
        
        result = await db.update_menu_item(item_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Menu item not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update menu item: {str(e)}")


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(item_id: UUID, soft_delete: bool = Query(True)):
    """
    Delete menu item
    
    - **Soft delete**: Set is_available to false (default)
    - **Hard delete**: Permanently remove from database
    """
    try:
        db = get_database_service()
        success = await db.delete_menu_item(item_id, soft_delete)
        if not success:
            raise HTTPException(status_code=404, detail="Menu item not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete menu item: {str(e)}")


@router.post("/items/bulk-update", response_model=dict)
async def bulk_update_menu_items(bulk_update: BulkMenuItemUpdate):
    """
    Bulk update multiple menu items
    
    - **Efficiency**: Update many items at once
    - **Use cases**: Price changes, availability updates, category reassignment
    """
    try:
        db = get_database_service()
        update_data = bulk_update.updates.model_dump(exclude_unset=True)
        
        # Convert decimals to float
        if "price" in update_data:
            update_data["price"] = float(update_data["price"])
        if "cost" in update_data and update_data["cost"]:
            update_data["cost"] = float(update_data["cost"])
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        item_ids = [str(item_id) for item_id in bulk_update.item_ids]
        result = db.client.table("menu_items").update(update_data).in_("id", item_ids).execute()
        
        return {
            "updated_count": len(result.data),
            "item_ids": item_ids,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk update: {str(e)}")


@router.post("/items/{item_id}/duplicate", response_model=MenuItem, status_code=status.HTTP_201_CREATED)
async def duplicate_menu_item(item_id: UUID, new_name: Optional[str] = None):
    """
    Duplicate an existing menu item
    
    - **Quick creation**: Copy all properties
    - **Customization**: Optionally provide new name
    """
    try:
        db = get_database_service()
        # Get original item
        original = db.client.table("menu_items").select("*").eq("id", str(item_id)).execute()
        if not original.data:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        # Create duplicate
        duplicate_data = original.data[0].copy()
        duplicate_data.pop("id", None)
        duplicate_data.pop("created_at", None)
        duplicate_data.pop("updated_at", None)
        
        if new_name:
            duplicate_data["name"] = new_name
        else:
            duplicate_data["name"] = f"{duplicate_data['name']} (Copy)"
        
        result = await db.create_menu_item(duplicate_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to duplicate item: {str(e)}")


# ============================================================================
# ITEM MODIFIERS
# ============================================================================

@router.post("/modifiers", response_model=ItemModifier, status_code=status.HTTP_201_CREATED)
async def create_item_modifier(modifier: ItemModifierCreate):
    """
    Create item modifier (toppings, sizes, customizations)
    
    - **Types**: Single or multiple selection
    - **Pricing**: Each option can have price adjustment
    - **Validation**: Min/max selection rules
    """
    try:
        db = get_database_service()
        data = modifier.model_dump()
        data["business_id"] = str(data["business_id"])
        
        # Convert options to proper format
        data["options"] = [{
            "name": opt.name,
            "price": float(opt.price),
            "is_default": opt.is_default
        } for opt in modifier.options]
        
        result = db.client.table("item_modifiers").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create modifier: {str(e)}")


@router.get("/modifiers", response_model=List[ItemModifier])
async def list_item_modifiers(
    business_id: UUID = Query(..., description="Business ID"),
    modifier_type: Optional[str] = Query(None, description="Filter by type")
):
    """List all item modifiers for a business"""
    try:
        db = get_database_service()
        query = db.client.table("item_modifiers").select("*").eq("business_id", str(business_id))
        
        if modifier_type:
            query = query.eq("type", modifier_type)
        
        result = query.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch modifiers: {str(e)}")


@router.get("/modifiers/{modifier_id}", response_model=ItemModifier)
async def get_item_modifier(modifier_id: UUID):
    """Get item modifier by ID"""
    try:
        db = get_database_service()
        result = db.client.table("item_modifiers").select("*").eq("id", str(modifier_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Modifier not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch modifier: {str(e)}")


@router.put("/modifiers/{modifier_id}", response_model=ItemModifier)
async def update_item_modifier(modifier_id: UUID, updates: ItemModifierUpdate):
    """Update item modifier"""
    try:
        db = get_database_service()
        update_data = updates.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        if "options" in update_data and update_data["options"]:
            update_data["options"] = [{
                "name": opt.name,
                "price": float(opt.price),
                "is_default": opt.is_default
            } for opt in updates.options]
        
        result = db.client.table("item_modifiers").update(update_data).eq("id", str(modifier_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Modifier not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update modifier: {str(e)}")


@router.delete("/modifiers/{modifier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item_modifier(modifier_id: UUID):
    """Delete item modifier"""
    try:
        db = get_database_service()
        result = db.client.table("item_modifiers").delete().eq("id", str(modifier_id)).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Modifier not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete modifier: {str(e)}")


@router.post("/items/{item_id}/modifiers/{modifier_id}", status_code=status.HTTP_201_CREATED)
async def assign_modifier_to_item(
    item_id: UUID,
    modifier_id: UUID,
    display_order: int = Query(0, ge=0)
):
    """
    Assign modifier to menu item
    
    - **Flexible**: Same modifier can be used for multiple items
    - **Ordering**: Control display order of modifiers
    """
    # TODO: Implement modifier assignment
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.delete("/items/{item_id}/modifiers/{modifier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_modifier_from_item(item_id: UUID, modifier_id: UUID):
    """Remove modifier from menu item"""
    # TODO: Implement modifier removal
    raise HTTPException(status_code=501, detail="Implementation pending")


# ============================================================================
# MENU IMPORT/EXPORT
# ============================================================================

@router.post("/import", response_model=dict)
async def import_menu(menu_import: MenuImport):
    """
    Import menu from external sources
    
    - **Sources**: PDF, CSV, JSON, Toast, DoorDash
    - **Auto-categorization**: AI-powered category creation
    - **Conflict handling**: Overwrite or skip existing items
    """
    # TODO: Implement import logic
    # TODO: Handle different source formats
    # TODO: Use AI for categorization
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.get("/export/{business_id}", response_model=dict)
async def export_menu(
    business_id: UUID,
    format: str = Query("json", pattern=r"^(json|csv|pdf)$"),
    include_inactive: bool = Query(False)
):
    """
    Export menu in various formats
    
    - **Formats**: JSON, CSV, PDF
    - **Filtering**: Include/exclude inactive items
    - **Use cases**: Backup, integration, printing
    """
    # TODO: Implement export logic
    raise HTTPException(status_code=501, detail="Implementation pending")


# ============================================================================
# MENU ANALYTICS
# ============================================================================

@router.get("/analytics/{business_id}/top-items", response_model=List[dict])
async def get_top_menu_items(
    business_id: UUID,
    period: str = Query("7d", pattern=r"^(1d|7d|30d|90d)$"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get top-performing menu items
    
    - **Metrics**: Sales volume, revenue, profit margin
    - **Time periods**: 1 day, 7 days, 30 days, 90 days
    """
    # TODO: Implement analytics query
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.get("/analytics/{business_id}/category-performance", response_model=List[dict])
async def get_category_performance(
    business_id: UUID,
    period: str = Query("7d", regex="^(1d|7d|30d|90d)$")
):
    """
    Analyze category performance
    
    - **Metrics**: Sales by category, profit margins
    - **Insights**: Best and worst performing categories
    """
    # TODO: Implement category analytics
    raise HTTPException(status_code=501, detail="Implementation pending")


@router.get("/analytics/{business_id}/profit-margins", response_model=dict)
async def analyze_profit_margins(business_id: UUID):
    """
    Analyze profit margins across menu
    
    - **Overall margins**: Business-wide profit analysis
    - **Item-level**: Identify high and low margin items
    - **Recommendations**: Suggest pricing adjustments
    """
    # TODO: Implement profit margin analysis
    raise HTTPException(status_code=501, detail="Implementation pending")
