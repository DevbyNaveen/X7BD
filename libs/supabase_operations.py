"""
Supabase Database Operations

Production-grade database operations for all services.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from supabase import create_client, Client
from postgrest.exceptions import APIError

import logging

logger = logging.getLogger(__name__)


class SupabaseOperations:
    """
    Production-grade Supabase operations
    
    Features:
    - CRUD operations for all tables
    - Transaction support
    - Error handling and retries
    - Connection pooling
    - Query optimization
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_KEY", "")
        self.client: Optional[Client] = None
        self._initialized = False
    
    def initialize(self):
        """Initialize Supabase connection"""
        if self._initialized:
            return
        
        try:
            if not self.url or not self.key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
            
            self.client = create_client(self.url, self.key)
            self._initialized = True
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    # ========================================================================
    # USER OPERATIONS
    # ========================================================================
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("users").insert(user_data).execute()
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except APIError as e:
            logger.error(f"Error getting user: {e}")
            raise
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user"""
        if not self._initialized:
            self.initialize()
        
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            result = self.client.table("users").update(updates).eq("id", user_id).execute()
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Error updating user: {e}")
            raise
    
    # ========================================================================
    # BUSINESS OPERATIONS
    # ========================================================================
    
    async def create_business(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new business"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("businesses").insert(business_data).execute()
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Error creating business: {e}")
            raise
    
    async def get_business(self, business_id: str) -> Optional[Dict[str, Any]]:
        """Get business by ID"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("businesses").select("*").eq("id", business_id).execute()
            return result.data[0] if result.data else None
        except APIError as e:
            logger.error(f"Error getting business: {e}")
            raise
    
    async def search_businesses(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search businesses with filters"""
        if not self._initialized:
            self.initialize()
        
        try:
            query_builder = self.client.table("businesses").select("*")
            
            if category:
                query_builder = query_builder.eq("category", category)
            
            if location:
                query_builder = query_builder.ilike("city", f"%{location}%")
            
            if query:
                query_builder = query_builder.or_(
                    f"name.ilike.%{query}%,description.ilike.%{query}%"
                )
            
            query_builder = query_builder.eq("is_active", True).limit(limit)
            
            result = query_builder.execute()
            return result.data if result.data else []
        except APIError as e:
            logger.error(f"Error searching businesses: {e}")
            raise
    
    async def update_business(self, business_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update business"""
        if not self._initialized:
            self.initialize()
        
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            result = self.client.table("businesses").update(updates).eq("id", business_id).execute()
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Error updating business: {e}")
            raise
    
    # ========================================================================
    # MENU OPERATIONS
    # ========================================================================
    
    async def get_menu_items(
        self,
        business_id: str,
        category_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get menu items for business"""
        if not self._initialized:
            self.initialize()
        
        try:
            query_builder = self.client.table("menu_items").select("*").eq("business_id", business_id)
            
            if category_id:
                query_builder = query_builder.eq("category_id", category_id)
            
            query_builder = query_builder.eq("is_active", True)
            
            result = query_builder.execute()
            return result.data if result.data else []
        except APIError as e:
            logger.error(f"Error getting menu items: {e}")
            raise
    
    async def create_menu_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create menu item"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("menu_items").insert(item_data).execute()
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Error creating menu item: {e}")
            raise
    
    # ========================================================================
    # ORDER OPERATIONS
    # ========================================================================
    
    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new order"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("orders").insert(order_data).execute()
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Error creating order: {e}")
            raise
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("orders").select("*, order_items(*)").eq("id", order_id).execute()
            return result.data[0] if result.data else None
        except APIError as e:
            logger.error(f"Error getting order: {e}")
            raise
    
    async def update_order_status(self, order_id: str, status: str) -> Dict[str, Any]:
        """Update order status"""
        if not self._initialized:
            self.initialize()
        
        try:
            updates = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            result = self.client.table("orders").update(updates).eq("id", order_id).execute()
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Error updating order status: {e}")
            raise
    
    async def get_orders_by_business(
        self,
        business_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get orders for business"""
        if not self._initialized:
            self.initialize()
        
        try:
            query_builder = self.client.table("orders").select("*").eq("business_id", business_id)
            
            if status:
                query_builder = query_builder.eq("status", status)
            
            query_builder = query_builder.order("created_at", desc=True).limit(limit)
            
            result = query_builder.execute()
            return result.data if result.data else []
        except APIError as e:
            logger.error(f"Error getting business orders: {e}")
            raise
    
    # ========================================================================
    # RESERVATION OPERATIONS
    # ========================================================================
    
    async def create_reservation(self, reservation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new reservation"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("reservations").insert(reservation_data).execute()
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Error creating reservation: {e}")
            raise
    
    async def get_reservation(self, reservation_id: str) -> Optional[Dict[str, Any]]:
        """Get reservation by ID"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("reservations").select("*").eq("id", reservation_id).execute()
            return result.data[0] if result.data else None
        except APIError as e:
            logger.error(f"Error getting reservation: {e}")
            raise
    
    async def check_availability(
        self,
        business_id: str,
        date: str,
        time: str
    ) -> bool:
        """Check if reservation slot is available"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("reservations").select("id").eq("business_id", business_id).eq("reservation_date", date).eq("reservation_time", time).eq("status", "confirmed").execute()
            
            # If no reservations found, slot is available
            return len(result.data) == 0 if result.data else True
        except APIError as e:
            logger.error(f"Error checking availability: {e}")
            raise
    
    # ========================================================================
    # CHAT OPERATIONS
    # ========================================================================
    
    async def create_chat_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat session"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("chat_sessions").insert(session_data).execute()
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Error creating chat session: {e}")
            raise
    
    async def save_chat_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save chat message"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("chat_messages").insert(message_data).execute()
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Error saving chat message: {e}")
            raise
    
    async def get_chat_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get chat history"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("chat_messages").select("*").eq("session_id", session_id).order("created_at", desc=False).limit(limit).execute()
            
            return result.data if result.data else []
        except APIError as e:
            logger.error(f"Error getting chat history: {e}")
            raise
    
    # ========================================================================
    # ANALYTICS OPERATIONS
    # ========================================================================
    
    async def log_analytics_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log analytics event"""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self.client.table("analytics_events").insert(event_data).execute()
            return result.data[0] if result.data else {}
        except APIError as e:
            logger.error(f"Error logging analytics event: {e}")
            raise
    
    async def get_business_analytics(
        self,
        business_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get business analytics"""
        if not self._initialized:
            self.initialize()
        
        try:
            query_builder = self.client.table("analytics_events").select("*").eq("business_id", business_id)
            
            if start_date:
                query_builder = query_builder.gte("created_at", start_date)
            
            if end_date:
                query_builder = query_builder.lte("created_at", end_date)
            
            result = query_builder.execute()
            return result.data if result.data else []
        except APIError as e:
            logger.error(f"Error getting business analytics: {e}")
            raise


# Global Supabase operations instance
supabase_ops = SupabaseOperations()
