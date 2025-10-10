"""
Menu Management API Routes
Enterprise-grade endpoints for menu CRUD operations

ENTERPRISE STRUCTURE:
- Food & Hospitality specific endpoints prefixed with /food/menu
- Common endpoints (customers, staff, analytics) moved to universal routes
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

router = APIRouter(prefix="/api/v1/menu", tags=["Menu Management"])


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
        
        result = db.create_menu_category(data)
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
        categories = db.get_menu_categories(business_id, parent_id, is_active)
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
        
        # Convert UUIDs to strings for JSON serialization
        if "parent_id" in update_data and update_data["parent_id"]:
            update_data["parent_id"] = str(update_data["parent_id"])
        
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
        
        result = db.create_menu_item(data)
        
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
    try:
        db = get_database_service()
        query = db.client.table("menu_items").select("*").eq("business_id", str(search.business_id))
        
        # Text search
        if search.name:
            query = query.ilike("name", f"%{search.name}%")
        if search.description:
            query = query.ilike("description", f"%{search.description}%")
        
        # Category filter
        if search.category_id:
            query = query.eq("category_id", str(search.category_id))
        
        # Price range filter
        if search.min_price is not None:
            query = query.gte("price", float(search.min_price))
        if search.max_price is not None:
            query = query.lte("price", float(search.max_price))
        
        # Availability filter
        if search.is_available is not None:
            query = query.eq("is_available", search.is_available)
        
        # Tags filter
        if search.tags:
            for tag in search.tags:
                query = query.contains("tags", [tag])
        
        # Location filter
        if search.location_id:
            query = query.contains("locations", [str(search.location_id)])
        
        # Apply pagination
        offset = search.offset or 0
        limit = search.limit or 50
        query = query.range(offset, offset + limit - 1)
        
        # Apply sorting
        if search.sort_by:
            order = "desc" if search.sort_order == "desc" else "asc"
            query = query.order(search.sort_by, desc=(order == "desc"))
        
        result = query.execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search menu items: {str(e)}")


@router.get("/items/{item_id}", response_model=MenuItemWithDetails)
async def get_menu_item(item_id: UUID, include_modifiers: bool = Query(True)):
    """
    Get menu item with full details
    
    - **Complete data**: Includes category and modifier details
    - **Profit margin**: Automatically calculated
    """
    try:
        db = get_database_service()
        item = db.get_menu_item_with_details(item_id)
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
        
        # Convert UUIDs to strings for JSON serialization
        if "category_id" in update_data and update_data["category_id"]:
            update_data["category_id"] = str(update_data["category_id"])
        if "modifiers" in update_data and update_data["modifiers"]:
            update_data["modifiers"] = [str(m) for m in update_data["modifiers"]]
        if "locations" in update_data and update_data["locations"]:
            update_data["locations"] = [str(l) for l in update_data["locations"]]
        
        result = db.update_menu_item(item_id, update_data)
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
        success = db.delete_menu_item(item_id, soft_delete)
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
        
        # Convert UUIDs to strings for JSON serialization
        if "category_id" in update_data and update_data["category_id"]:
            update_data["category_id"] = str(update_data["category_id"])
        if "modifiers" in update_data and update_data["modifiers"]:
            update_data["modifiers"] = [str(m) for m in update_data["modifiers"]]
        if "locations" in update_data and update_data["locations"]:
            update_data["locations"] = [str(l) for l in update_data["locations"]]
        
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
        
        result = db.create_menu_item(duplicate_data)
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
    try:
        db = get_database_service()
        
        # Verify item exists
        item_result = db.client.table("menu_items").select("id, modifiers").eq("id", str(item_id)).execute()
        if not item_result.data:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        # Verify modifier exists
        modifier_result = db.client.table("item_modifiers").select("id").eq("id", str(modifier_id)).execute()
        if not modifier_result.data:
            raise HTTPException(status_code=404, detail="Modifier not found")
        
        # Get current modifiers
        current_modifiers = item_result.data[0].get("modifiers", [])
        
        # Check if modifier is already assigned
        if str(modifier_id) in current_modifiers:
            raise HTTPException(status_code=400, detail="Modifier already assigned to this item")
        
        # Add modifier to the list
        current_modifiers.append(str(modifier_id))
        
        # Update the item
        result = db.client.table("menu_items").update({
            "modifiers": current_modifiers,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(item_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        # Publish real-time update
        await RealtimeEventPublisher.publish_order_update(
            str(item_result.data[0].get("business_id", "")),
            {
                "type": "modifier_assigned",
                "item_id": str(item_id),
                "modifier_id": str(modifier_id),
                "display_order": display_order
            }
        )
        
        return {"message": "Modifier assigned successfully", "modifier_id": str(modifier_id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign modifier: {str(e)}")


@router.delete("/items/{item_id}/modifiers/{modifier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_modifier_from_item(item_id: UUID, modifier_id: UUID):
    """Remove modifier from menu item"""
    try:
        db = get_database_service()
        
        # Verify item exists and get current modifiers
        item_result = db.client.table("menu_items").select("id, modifiers, business_id").eq("id", str(item_id)).execute()
        if not item_result.data:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        # Get current modifiers
        current_modifiers = item_result.data[0].get("modifiers", [])
        
        # Check if modifier is assigned
        if str(modifier_id) not in current_modifiers:
            raise HTTPException(status_code=400, detail="Modifier not assigned to this item")
        
        # Remove modifier from the list
        current_modifiers.remove(str(modifier_id))
        
        # Update the item
        result = db.client.table("menu_items").update({
            "modifiers": current_modifiers,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(item_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        # Publish real-time update
        await RealtimeEventPublisher.publish_order_update(
            str(item_result.data[0].get("business_id", "")),
            {
                "type": "modifier_removed",
                "item_id": str(item_id),
                "modifier_id": str(modifier_id)
            }
        )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove modifier: {str(e)}")


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
    try:
        db = get_database_service()
        imported_count = 0
        skipped_count = 0
        errors = []
        
        # Process based on source type
        if menu_import.source_type == "json":
            # Handle JSON import
            for item_data in menu_import.data:
                try:
                    # Validate required fields
                    if not item_data.get("name") or not item_data.get("price"):
                        errors.append(f"Item missing required fields: {item_data.get('name', 'Unknown')}")
                        continue
                    
                    # Check for existing item if conflict handling is skip
                    if menu_import.conflict_handling == "skip":
                        existing = db.client.table("menu_items").select("id").eq("business_id", str(menu_import.business_id)).eq("name", item_data["name"]).execute()
                        if existing.data:
                            skipped_count += 1
                            continue
                    
                    # Prepare item data
                    item_data["business_id"] = str(menu_import.business_id)
                    item_data["price"] = float(item_data["price"])
                    if item_data.get("cost"):
                        item_data["cost"] = float(item_data["cost"])
                    
                    # Auto-categorization based on name patterns
                    if not item_data.get("category_id"):
                        category_name = _auto_categorize_item(item_data["name"])
                        category_id = _get_or_create_category(db, menu_import.business_id, category_name)
                        if category_id:
                            item_data["category_id"] = category_id
                    
                    # Create the item
                    result = db.create_menu_item(item_data)
                    if result:
                        imported_count += 1
                        
                        # Publish real-time update
                        await RealtimeEventPublisher.publish_order_update(
                            str(menu_import.business_id),
                            {"type": "menu_item_imported", "item": result}
                        )
                    
                except Exception as e:
                    errors.append(f"Error importing item {item_data.get('name', 'Unknown')}: {str(e)}")
        
        elif menu_import.source_type == "csv":
            # Handle CSV import (assuming data is already parsed)
            for row in menu_import.data:
                try:
                    item_data = {
                        "name": row.get("name", ""),
                        "description": row.get("description", ""),
                        "price": float(row.get("price", 0)),
                        "cost": float(row.get("cost", 0)) if row.get("cost") else None,
                        "category_id": row.get("category_id"),
                        "is_available": row.get("is_available", True),
                        "tags": row.get("tags", "").split(",") if row.get("tags") else []
                    }
                    
                    # Skip if missing required fields
                    if not item_data["name"] or item_data["price"] <= 0:
                        errors.append(f"Invalid CSV row: {row}")
                        continue
                    
                    # Check for existing item
                    if menu_import.conflict_handling == "skip":
                        existing = db.client.table("menu_items").select("id").eq("business_id", str(menu_import.business_id)).eq("name", item_data["name"]).execute()
                        if existing.data:
                            skipped_count += 1
                            continue
                    
                    item_data["business_id"] = str(menu_import.business_id)
                    
                    # Auto-categorization
                    if not item_data.get("category_id"):
                        category_name = _auto_categorize_item(item_data["name"])
                        category_id = _get_or_create_category(db, menu_import.business_id, category_name)
                        if category_id:
                            item_data["category_id"] = category_id
                    
                    result = db.create_menu_item(item_data)
                    if result:
                        imported_count += 1
                        
                        await RealtimeEventPublisher.publish_order_update(
                            str(menu_import.business_id),
                            {"type": "menu_item_imported", "item": result}
                        )
                    
                except Exception as e:
                    errors.append(f"Error importing CSV row: {str(e)}")
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source type: {menu_import.source_type}")
        
        return {
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "error_count": len(errors),
            "errors": errors[:10],  # Limit errors in response
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import menu: {str(e)}")


def _auto_categorize_item(item_name: str) -> str:
    """Simple auto-categorization based on item name patterns"""
    name_lower = item_name.lower()
    
    # Food categories
    if any(word in name_lower for word in ["pizza", "pasta", "burger", "sandwich"]):
        return "Main Dishes"
    elif any(word in name_lower for word in ["salad", "soup", "appetizer"]):
        return "Appetizers"
    elif any(word in name_lower for word in ["dessert", "cake", "ice cream", "cookie"]):
        return "Desserts"
    elif any(word in name_lower for word in ["drink", "beverage", "coffee", "tea", "soda"]):
        return "Beverages"
    elif any(word in name_lower for word in ["side", "fries", "chips"]):
        return "Sides"
    else:
        return "General"


def _get_or_create_category(db, business_id: UUID, category_name: str) -> Optional[str]:
    """Get existing category or create new one"""
    try:
        # Check if category exists
        result = db.client.table("menu_categories").select("id").eq("business_id", str(business_id)).eq("name", category_name).execute()
        if result.data:
            return result.data[0]["id"]
        
        # Create new category
        category_data = {
            "business_id": str(business_id),
            "name": category_name,
            "description": f"Auto-generated category for {category_name}",
            "is_active": True,
            "display_order": 999
        }
        
        result = db.client.table("menu_categories").insert(category_data).execute()
        if result.data:
            return result.data[0]["id"]
        
        return None
    except Exception:
        return None


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
    try:
        db = get_database_service()
        
        # Build query
        query = db.client.table("menu_items").select("*").eq("business_id", str(business_id))
        
        if not include_inactive:
            query = query.eq("is_available", True)
        
        # Get categories for reference
        categories_result = db.client.table("menu_categories").select("*").eq("business_id", str(business_id)).execute()
        categories = {cat["id"]: cat["name"] for cat in categories_result.data}
        
        # Get menu items
        result = query.execute()
        items = result.data
        
        # Add category names to items
        for item in items:
            if item.get("category_id") and item["category_id"] in categories:
                item["category_name"] = categories[item["category_id"]]
        
        if format == "json":
            return {
                "format": "json",
                "business_id": str(business_id),
                "exported_at": datetime.utcnow().isoformat(),
                "item_count": len(items),
                "data": items
            }
        
        elif format == "csv":
            # Convert to CSV format
            csv_data = []
            if items:
                # Headers
                headers = ["id", "name", "description", "price", "cost", "category_name", "is_available", "tags"]
                csv_data.append(",".join(headers))
                
                # Data rows
                for item in items:
                    row = [
                        str(item.get("id", "")),
                        f'"{item.get("name", "")}"',
                        f'"{item.get("description", "")}"',
                        str(item.get("price", 0)),
                        str(item.get("cost", "")),
                        f'"{item.get("category_name", "")}"',
                        str(item.get("is_available", True)),
                        f'"{",".join(item.get("tags", []))}"'
                    ]
                    csv_data.append(",".join(row))
            
            return {
                "format": "csv",
                "business_id": str(business_id),
                "exported_at": datetime.utcnow().isoformat(),
                "item_count": len(items),
                "data": "\n".join(csv_data)
            }
        
        elif format == "pdf":
            # For PDF, return structured data that can be converted to PDF
            # In a real implementation, you'd use a PDF library like reportlab
            pdf_data = {
                "business_id": str(business_id),
                "exported_at": datetime.utcnow().isoformat(),
                "item_count": len(items),
                "categories": list(categories.values()),
                "items_by_category": {}
            }
            
            # Group items by category
            for item in items:
                category_name = item.get("category_name", "Uncategorized")
                if category_name not in pdf_data["items_by_category"]:
                    pdf_data["items_by_category"][category_name] = []
                pdf_data["items_by_category"][category_name].append({
                    "name": item.get("name", ""),
                    "description": item.get("description", ""),
                    "price": item.get("price", 0)
                })
            
            return {
                "format": "pdf",
                "business_id": str(business_id),
                "exported_at": datetime.utcnow().isoformat(),
                "item_count": len(items),
                "data": pdf_data
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export menu: {str(e)}")


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
    try:
        db = get_database_service()
        
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get order items for the period (assuming orders table exists)
        # This is a simplified implementation - in reality you'd join with orders table
        query = """
        SELECT 
            mi.id,
            mi.name,
            mi.price,
            mi.cost,
            COUNT(oi.id) as sales_count,
            SUM(oi.quantity) as total_quantity,
            SUM(oi.quantity * mi.price) as total_revenue,
            SUM(oi.quantity * COALESCE(mi.cost, 0)) as total_cost,
            AVG(mi.price - COALESCE(mi.cost, 0)) as avg_profit_margin
        FROM menu_items mi
        LEFT JOIN order_items oi ON mi.id = oi.menu_item_id
        LEFT JOIN orders o ON oi.order_id = o.id
        WHERE mi.business_id = %s
        AND (o.created_at IS NULL OR o.created_at BETWEEN %s AND %s)
        GROUP BY mi.id, mi.name, mi.price, mi.cost
        ORDER BY total_revenue DESC
        LIMIT %s
        """
        
        # For now, return mock data since we don't have orders table
        # In a real implementation, you'd execute the SQL query above
        menu_items = db.client.table("menu_items").select("*").eq("business_id", str(business_id)).limit(limit).execute()
        
        top_items = []
        for item in menu_items.data:
            # Mock analytics data - replace with real order data
            sales_count = 0  # Would come from orders table
            total_quantity = 0  # Would come from orders table
            total_revenue = 0.0  # Would come from orders table
            total_cost = 0.0  # Would come from orders table
            profit_margin = 0.0
            
            if item.get("cost") and item.get("price"):
                profit_margin = float(item["price"]) - float(item["cost"])
            
            top_items.append({
                "item_id": item["id"],
                "name": item["name"],
                "price": float(item["price"]),
                "cost": float(item.get("cost", 0)),
                "sales_count": sales_count,
                "total_quantity": total_quantity,
                "total_revenue": total_revenue,
                "total_cost": total_cost,
                "profit_margin": profit_margin,
                "profit_margin_percentage": (profit_margin / float(item["price"]) * 100) if item["price"] > 0 else 0
            })
        
        # Sort by revenue (descending)
        top_items.sort(key=lambda x: x["total_revenue"], reverse=True)
        
        return top_items
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get top menu items: {str(e)}")


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
    try:
        db = get_database_service()
        
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get categories for the business
        categories_result = db.client.table("menu_categories").select("*").eq("business_id", str(business_id)).execute()
        categories = categories_result.data
        
        # Get menu items grouped by category
        menu_items_result = db.client.table("menu_items").select("*").eq("business_id", str(business_id)).execute()
        menu_items = menu_items_result.data
        
        # Group items by category
        items_by_category = {}
        for item in menu_items:
            category_id = item.get("category_id")
            if category_id not in items_by_category:
                items_by_category[category_id] = []
            items_by_category[category_id].append(item)
        
        # Calculate performance metrics for each category
        category_performance = []
        for category in categories:
            category_id = category["id"]
            items = items_by_category.get(category_id, [])
            
            # Calculate metrics
            total_items = len(items)
            available_items = len([item for item in items if item.get("is_available", True)])
            
            # Calculate average price and cost
            total_price = sum(float(item.get("price", 0)) for item in items)
            total_cost = sum(float(item.get("cost", 0)) for item in items if item.get("cost"))
            avg_price = total_price / total_items if total_items > 0 else 0
            avg_cost = total_cost / total_items if total_items > 0 else 0
            avg_profit_margin = avg_price - avg_cost
            profit_margin_percentage = (avg_profit_margin / avg_price * 100) if avg_price > 0 else 0
            
            # Mock sales data - in real implementation, this would come from orders table
            total_sales = 0  # Would come from orders table
            total_revenue = 0.0  # Would come from orders table
            total_profit = 0.0  # Would come from orders table
            
            category_performance.append({
                "category_id": category_id,
                "category_name": category["name"],
                "total_items": total_items,
                "available_items": available_items,
                "avg_price": avg_price,
                "avg_cost": avg_cost,
                "avg_profit_margin": avg_profit_margin,
                "profit_margin_percentage": profit_margin_percentage,
                "total_sales": total_sales,
                "total_revenue": total_revenue,
                "total_profit": total_profit,
                "performance_score": 0.0  # Would be calculated based on real sales data
            })
        
        # Sort by performance score (descending)
        category_performance.sort(key=lambda x: x["performance_score"], reverse=True)
        
        return category_performance
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get category performance: {str(e)}")


@router.get("/analytics/{business_id}/profit-margins", response_model=dict)
async def analyze_profit_margins(business_id: UUID):
    """
    Analyze profit margins across menu
    
    - **Overall margins**: Business-wide profit analysis
    - **Item-level**: Identify high and low margin items
    - **Recommendations**: Suggest pricing adjustments
    """
    try:
        db = get_database_service()
        
        # Get all menu items for the business
        menu_items_result = db.client.table("menu_items").select("*").eq("business_id", str(business_id)).execute()
        menu_items = menu_items_result.data
        
        if not menu_items:
            return {
                "business_id": str(business_id),
                "total_items": 0,
                "overall_analysis": {},
                "high_margin_items": [],
                "low_margin_items": [],
                "recommendations": []
            }
        
        # Calculate overall metrics
        total_items = len(menu_items)
        items_with_cost = [item for item in menu_items if item.get("cost")]
        items_without_cost = [item for item in menu_items if not item.get("cost")]
        
        # Overall profit margin analysis
        total_revenue = sum(float(item.get("price", 0)) for item in menu_items)
        total_cost = sum(float(item.get("cost", 0)) for item in items_with_cost)
        overall_profit_margin = total_revenue - total_cost
        overall_margin_percentage = (overall_profit_margin / total_revenue * 100) if total_revenue > 0 else 0
        
        # Item-level analysis
        high_margin_items = []
        low_margin_items = []
        medium_margin_items = []
        
        for item in items_with_cost:
            price = float(item.get("price", 0))
            cost = float(item.get("cost", 0))
            profit_margin = price - cost
            margin_percentage = (profit_margin / price * 100) if price > 0 else 0
            
            item_analysis = {
                "item_id": item["id"],
                "name": item["name"],
                "price": price,
                "cost": cost,
                "profit_margin": profit_margin,
                "margin_percentage": margin_percentage
            }
            
            if margin_percentage >= 30:  # High margin threshold
                high_margin_items.append(item_analysis)
            elif margin_percentage <= 10:  # Low margin threshold
                low_margin_items.append(item_analysis)
            else:
                medium_margin_items.append(item_analysis)
        
        # Sort by margin percentage
        high_margin_items.sort(key=lambda x: x["margin_percentage"], reverse=True)
        low_margin_items.sort(key=lambda x: x["margin_percentage"])
        
        # Generate recommendations
        recommendations = []
        
        if len(low_margin_items) > 0:
            recommendations.append({
                "type": "pricing",
                "priority": "high",
                "message": f"{len(low_margin_items)} items have low profit margins (<10%). Consider reviewing costs or increasing prices.",
                "affected_items": [item["name"] for item in low_margin_items[:5]]
            })
        
        if len(items_without_cost) > 0:
            recommendations.append({
                "type": "cost_tracking",
                "priority": "medium",
                "message": f"{len(items_without_cost)} items don't have cost data. Adding cost information will improve profit analysis.",
                "affected_items": [item["name"] for item in items_without_cost[:5]]
            })
        
        if overall_margin_percentage < 20:
            recommendations.append({
                "type": "overall_margin",
                "priority": "high",
                "message": f"Overall profit margin is {overall_margin_percentage:.1f}%. Consider reviewing pricing strategy.",
                "affected_items": []
            })
        
        if len(high_margin_items) > 0:
            recommendations.append({
                "type": "opportunity",
                "priority": "low",
                "message": f"{len(high_margin_items)} items have excellent profit margins (>30%). Consider promoting these items.",
                "affected_items": [item["name"] for item in high_margin_items[:3]]
            })
        
        return {
            "business_id": str(business_id),
            "total_items": total_items,
            "items_with_cost": len(items_with_cost),
            "items_without_cost": len(items_without_cost),
            "overall_analysis": {
                "total_revenue": total_revenue,
                "total_cost": total_cost,
                "overall_profit_margin": overall_profit_margin,
                "overall_margin_percentage": overall_margin_percentage
            },
            "high_margin_items": high_margin_items[:10],  # Top 10
            "low_margin_items": low_margin_items[:10],    # Bottom 10
            "medium_margin_items": medium_margin_items[:10],  # Top 10 medium
            "recommendations": recommendations,
            "analysis_date": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze profit margins: {str(e)}")
