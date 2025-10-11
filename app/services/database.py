"""
Database Service Layer
Enterprise-grade database operations with Supabase
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
import os
from supabase import create_client, Client


class DatabaseService:
    """Centralized database operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        self.client: Client = create_client(supabase_url, supabase_key)
    
    # ========================================================================
    # MENU OPERATIONS
    # ========================================================================
    
    def create_menu_category(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create menu category"""
        result = self.client.table("menu_categories").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_menu_categories(
        self,
        business_id: UUID,
        parent_id: Optional[UUID] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get menu categories with filtering"""
        query = self.client.table("menu_categories").select("*").eq("business_id", str(business_id))
        
        if parent_id is not None:
            query = query.eq("parent_id", str(parent_id))
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        query = query.order("display_order")
        result = query.execute()
        return result.data
    
    def create_menu_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create menu item"""
        result = self.client.table("menu_items").insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_menu_items(
        self,
        business_id: UUID,
        category_id: Optional[UUID] = None,
        is_available: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get menu items with filtering and pagination"""
        query = self.client.table("menu_items").select("*").eq("business_id", str(business_id))
        
        if category_id:
            query = query.eq("category_id", str(category_id))
        if is_available is not None:
            query = query.eq("is_available", is_available)
        
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        return result.data
    
    def get_menu_item_with_details(self, item_id: UUID) -> Optional[Dict[str, Any]]:
        """Get menu item with category and modifiers"""
        # Get item
        item_result = self.client.table("menu_items").select("*").eq("id", str(item_id)).execute()
        if not item_result.data:
            return None
        
        item = item_result.data[0]
        
        # Get category
        if item.get("category_id"):
            category_result = self.client.table("menu_categories").select("*").eq("id", item["category_id"]).execute()
            item["category"] = category_result.data[0] if category_result.data else None
        
        # Get modifiers
        if item.get("modifiers"):
            modifier_ids = item["modifiers"]
            modifiers_result = self.client.table("item_modifiers").select("*").in_("id", modifier_ids).execute()
            item["modifier_details"] = modifiers_result.data
        
        return item
    
    def update_menu_item(self, item_id: UUID, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update menu item"""
        result = self.client.table("menu_items").update(updates).eq("id", str(item_id)).execute()
        return result.data[0] if result.data else None
    
    def delete_menu_item(self, item_id: UUID, soft_delete: bool = True) -> bool:
        """Delete menu item (soft or hard)"""
        if soft_delete:
            result = self.client.table("menu_items").update({"is_available": False}).eq("id", str(item_id)).execute()
        else:
            result = self.client.table("menu_items").delete().eq("id", str(item_id)).execute()
        return bool(result.data)
    
    # ========================================================================
    # INVENTORY OPERATIONS
    # ========================================================================
    
    async def create_inventory_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create inventory item"""
        result = self.client.table("inventory_items").insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_inventory_items(
        self,
        business_id: UUID,
        location_id: Optional[UUID] = None,
        low_stock_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get inventory items with filtering"""
        query = self.client.table("inventory_items").select("*").eq("business_id", str(business_id))
        
        if location_id:
            query = query.eq("location_id", str(location_id))
        
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        
        # Filter for low stock items if requested
        if low_stock_only:
            filtered_data = []
            for item in result.data:
                current_stock = float(item.get("current_stock", 0))
                min_stock = float(item.get("min_stock", 0))
                if current_stock <= min_stock:
                    filtered_data.append(item)
            return filtered_data
        
        return result.data
    
    async def create_inventory_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create inventory transaction"""
        result = self.client.table("inventory_transactions").insert(data).execute()
        return result.data[0] if result.data else None
    
    async def adjust_inventory_stock(
        self,
        item_id: UUID,
        new_quantity: Decimal,
        reason: str,
        performed_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Adjust inventory stock with transaction logging"""
        # Get current stock
        item_result = self.client.table("inventory_items").select("*").eq("id", str(item_id)).execute()
        if not item_result.data:
            raise ValueError(f"Inventory item {item_id} not found")
        
        item = item_result.data[0]
        old_quantity = Decimal(str(item["current_stock"]))
        quantity_change = new_quantity - old_quantity
        
        # Update stock
        update_result = self.client.table("inventory_items").update({
            "current_stock": float(new_quantity),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(item_id)).execute()
        
        # Create transaction
        transaction_data = {
            "business_id": item["business_id"],
            "inventory_item_id": str(item_id),
            "transaction_type": "adjustment",
            "quantity": float(quantity_change),
            "notes": reason,
            "performed_by": str(performed_by) if performed_by else None
        }
        await self.create_inventory_transaction(transaction_data)
        
        return update_result.data[0] if update_result.data else None
    
    async def get_low_stock_items(self, business_id: UUID) -> List[Dict[str, Any]]:
        """Get items below reorder point"""
        result = self.client.rpc("get_low_stock_items", {"p_business_id": str(business_id)}).execute()
        return result.data
    
    async def create_purchase_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create purchase order"""
        # Generate order number
        data["order_number"] = f"PO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{data['business_id'][:8]}"
        
        result = self.client.table("purchase_orders").insert(data).execute()
        return result.data[0] if result.data else None
    
    # ========================================================================
    # USER OPERATIONS
    # ========================================================================
    
    async def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user"""
        try:
            # Convert UUID fields to strings for JSON serialization
            if "id" in data:
                data["id"] = str(data["id"])
            
            print(f"🔍 DEBUG: Creating user with data: {data}")
            result = self.client.table("users").insert(data).execute()
            print(f"🔍 DEBUG: User creation result: {result}")
            
            if not result.data:
                raise Exception("User creation returned no data")
            
            return result.data[0]
        except Exception as e:
            print(f"💥 DEBUG: Error in create_user: {str(e)}")
            raise
    
    async def user_exists(self, user_id: UUID) -> bool:
        """Check if user exists"""
        result = self.client.table("users").select("id").eq("id", str(user_id)).execute()
        return len(result.data) > 0 if result.data else False

    # ========================================================================
    # OPERATIONS
    # ========================================================================
    
    async def create_table(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create table"""
        result = self.client.table("tables").insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_tables(
        self,
        business_id: UUID,
        location_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tables with filtering"""
        query = self.client.table("tables").select("*").eq("business_id", str(business_id))
        
        if location_id:
            query = query.eq("location_id", str(location_id))
        if status:
            query = query.eq("status", status)
        
        result = query.execute()
        return result.data
    
    async def update_table_status(
        self,
        table_id: UUID,
        status: str,
        order_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Update table status"""
        updates = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        if order_id:
            updates["current_order_id"] = str(order_id)
        else:
            updates["current_order_id"] = None
        
        result = self.client.table("tables").update(updates).eq("id", str(table_id)).execute()
        return result.data[0] if result.data else None
    
    async def order_exists(self, order_id: UUID) -> bool:
        """Check if order exists"""
        result = self.client.table("orders").select("id").eq("id", str(order_id)).execute()
        return len(result.data) > 0 if result.data else False
    
    async def create_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create order"""
        try:
            # Convert UUID fields to strings for JSON serialization
            if "business_id" in data:
                data["business_id"] = str(data["business_id"])
            if "id" in data:
                data["id"] = str(data["id"])
            
            print(f"🔍 DEBUG: Creating order with data: {data}")
            result = self.client.table("orders").insert(data).execute()
            print(f"🔍 DEBUG: Order creation result: {result}")
            
            if not result.data:
                raise Exception("Order creation returned no data")
            
            return result.data[0]
        except Exception as e:
            print(f"💥 DEBUG: Error in create_order: {str(e)}")
            raise
    
    async def create_kds_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create KDS order"""
        # Convert UUID fields to strings for JSON serialization
        if "business_id" in data:
            data["business_id"] = str(data["business_id"])
        if "order_id" in data:
            data["order_id"] = str(data["order_id"])
        if "assigned_to" in data and data["assigned_to"]:
            data["assigned_to"] = str(data["assigned_to"])
        
        # Convert UUID fields in items
        if "items" in data and data["items"]:
            for item in data["items"]:
                if "menu_item_id" in item:
                    item["menu_item_id"] = str(item["menu_item_id"])
        
        result = self.client.table("kds_orders").insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_active_kds_orders(
        self,
        business_id: UUID,
        station: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active KDS orders"""
        query = self.client.table("kds_orders").select("*").eq("business_id", str(business_id))
        
        # Filter for active statuses using OR conditions
        query = query.or_("status.eq.pending,status.eq.preparing")
        
        if station:
            query = query.eq("station", station)
        
        query = query.order("priority", desc=True).order("created_at")
        result = query.execute()
        return result.data
    
    async def update_kds_order_status(
        self,
        order_id: UUID,
        status: str,
        timestamp_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update KDS order status"""
        updates = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if timestamp_field:
            updates[timestamp_field] = datetime.utcnow().isoformat()
        
        result = self.client.table("kds_orders").update(updates).eq("id", str(order_id)).execute()
        return result.data[0] if result.data else None
    
    async def update_kds_order_fields(
        self,
        order_id: UUID,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update KDS order fields"""
        # Add updated_at timestamp
        updates["updated_at"] = datetime.utcnow().isoformat()
        
        # Convert UUID fields to strings
        if "assigned_to" in updates and updates["assigned_to"]:
            updates["assigned_to"] = str(updates["assigned_to"])
        
        result = self.client.table("kds_orders").update(updates).eq("id", str(order_id)).execute()
        return result.data[0] if result.data else None
    
    # ========================================================================
    # STAFF OPERATIONS
    # ========================================================================
    
    async def create_staff_member(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create staff member"""
        result = self.client.table("staff_members").insert(data).execute()
        return result.data[0] if result.data else None
    
    async def clock_in_staff(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clock in staff member"""
        result = self.client.table("time_clock").insert(data).execute()
        return result.data[0] if result.data else None
    
    async def clock_out_staff(self, clock_id: UUID, clock_out_time: datetime) -> Dict[str, Any]:
        """Clock out staff member"""
        # Get clock-in record
        clock_result = self.client.table("time_clock").select("*").eq("id", str(clock_id)).execute()
        if not clock_result.data:
            raise ValueError(f"Time clock record {clock_id} not found")
        
        clock_record = clock_result.data[0]
        clock_in_time = datetime.fromisoformat(clock_record["clock_in"])
        
        # Calculate hours
        total_seconds = (clock_out_time - clock_in_time).total_seconds()
        total_hours = Decimal(str(total_seconds / 3600)).quantize(Decimal('0.01'))
        
        # Calculate overtime (over 8 hours)
        overtime_hours = max(Decimal('0'), total_hours - Decimal('8'))
        
        updates = {
            "clock_out": clock_out_time.isoformat(),
            "total_hours": float(total_hours),
            "overtime_hours": float(overtime_hours),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = self.client.table("time_clock").update(updates).eq("id", str(clock_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_clocked_in_staff(self, business_id: UUID) -> List[Dict[str, Any]]:
        """Get currently clocked-in staff"""
        query = self.client.table("time_clock").select("*, staff_members(*)")
        query = query.eq("business_id", str(business_id))
        query = query.is_("clock_out", "null")
        result = query.execute()
        return result.data
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    async def get_daily_sales_summary(
        self,
        business_id: UUID,
        date: date
    ) -> Optional[Dict[str, Any]]:
        """Get daily sales summary"""
        result = self.client.table("daily_sales_summary").select("*").eq("business_id", str(business_id)).eq("date", date.isoformat()).execute()
        return result.data[0] if result.data else None
    
    async def calculate_daily_sales(
        self,
        business_id: UUID,
        date: date
    ) -> Dict[str, Any]:
        """Calculate daily sales summary"""
        result = self.client.rpc("calculate_daily_sales", {
            "p_business_id": str(business_id),
            "p_date": date.isoformat()
        }).execute()
        return result.data
    
    async def get_top_menu_items(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top-performing menu items"""
        query = self.client.table("item_performance").select("*, menu_items(*)")
        query = query.eq("business_id", str(business_id))
        query = query.gte("date", start_date.isoformat())
        query = query.lte("date", end_date.isoformat())
        query = query.order("revenue", desc=True)
        query = query.limit(limit)
        result = query.execute()
        return result.data
    
    async def get_inventory_valuation(
        self,
        business_id: UUID,
        location_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Calculate inventory valuation"""
        query = self.client.table("inventory_items").select("current_stock, unit_cost")
        query = query.eq("business_id", str(business_id))
        query = query.eq("is_tracked", True)
        
        if location_id:
            query = query.eq("location_id", str(location_id))
        
        result = query.execute()
        
        total_value = sum(
            Decimal(str(item["current_stock"])) * Decimal(str(item["unit_cost"] or 0))
            for item in result.data
        )
        
        return {
            "total_items": len(result.data),
            "total_value": float(total_value),
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton instance
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get database service singleton"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
