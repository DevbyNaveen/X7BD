"""
Real-time WebSocket Service
Enterprise-grade real-time updates for dashboard
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, List, Any
from uuid import UUID
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        # business_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # station -> set of websockets (for KDS)
        self.kds_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, business_id: str, connection_type: str = "dashboard"):
        """Connect a new WebSocket client"""
        await websocket.accept()
        
        if connection_type == "kds":
            if business_id not in self.kds_connections:
                self.kds_connections[business_id] = set()
            self.kds_connections[business_id].add(websocket)
        else:
            if business_id not in self.active_connections:
                self.active_connections[business_id] = set()
            self.active_connections[business_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, business_id: str, connection_type: str = "dashboard"):
        """Disconnect a WebSocket client"""
        if connection_type == "kds":
            if business_id in self.kds_connections:
                self.kds_connections[business_id].discard(websocket)
                if not self.kds_connections[business_id]:
                    del self.kds_connections[business_id]
        else:
            if business_id in self.active_connections:
                self.active_connections[business_id].discard(websocket)
                if not self.active_connections[business_id]:
                    del self.active_connections[business_id]
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def broadcast_to_business(self, message: Dict[str, Any], business_id: str):
        """Broadcast message to all clients of a business"""
        if business_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[business_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections[business_id].discard(connection)
    
    async def broadcast_to_kds(self, message: Dict[str, Any], business_id: str):
        """Broadcast message to KDS displays"""
        if business_id not in self.kds_connections:
            return
        
        disconnected = set()
        for connection in self.kds_connections[business_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to KDS: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.kds_connections[business_id].discard(connection)
    
    def get_connection_count(self, business_id: str) -> int:
        """Get number of active connections for a business"""
        return len(self.active_connections.get(business_id, set()))


# Singleton instance
manager = ConnectionManager()


class RealtimeEventPublisher:
    """Publish real-time events to connected clients"""
    
    @staticmethod
    async def publish_order_update(business_id: str, order_data: Dict[str, Any]):
        """Publish order update event"""
        message = {
            "event": "order_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": order_data
        }
        await manager.broadcast_to_business(message, business_id)
    
    @staticmethod
    async def publish_table_update(business_id: str, table_data: Dict[str, Any]):
        """Publish table status update"""
        message = {
            "event": "table_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": table_data
        }
        await manager.broadcast_to_business(message, business_id)
    
    @staticmethod
    async def publish_kds_update(business_id: str, kds_data: Dict[str, Any]):
        """Publish KDS order update"""
        message = {
            "event": "kds_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": kds_data
        }
        await manager.broadcast_to_kds(message, business_id)
    
    @staticmethod
    async def publish_inventory_alert(business_id: str, alert_data: Dict[str, Any]):
        """Publish inventory alert"""
        message = {
            "event": "inventory_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": alert_data
        }
        await manager.broadcast_to_business(message, business_id)
    
    @staticmethod
    async def publish_staff_update(business_id: str, staff_data: Dict[str, Any]):
        """Publish staff clock in/out update"""
        message = {
            "event": "staff_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": staff_data
        }
        await manager.broadcast_to_business(message, business_id)
    
    @staticmethod
    async def publish_revenue_update(business_id: str, revenue_data: Dict[str, Any]):
        """Publish real-time revenue update"""
        message = {
            "event": "revenue_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": revenue_data
        }
        await manager.broadcast_to_business(message, business_id)


class MetricsAggregator:
    """Aggregate and cache real-time metrics"""
    
    def __init__(self):
        self.metrics_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 5  # seconds
    
    async def get_realtime_metrics(self, business_id: str) -> Dict[str, Any]:
        """Get cached or fresh real-time metrics"""
        cache_key = f"metrics_{business_id}"
        
        # Check cache
        if cache_key in self.metrics_cache:
            cached = self.metrics_cache[cache_key]
            age = (datetime.utcnow() - cached["timestamp"]).total_seconds()
            if age < self.cache_ttl:
                return cached["data"]
        
        # Fetch fresh metrics
        metrics = await self._fetch_metrics(business_id)
        
        # Update cache
        self.metrics_cache[cache_key] = {
            "timestamp": datetime.utcnow(),
            "data": metrics
        }
        
        return metrics
    
    async def _fetch_metrics(self, business_id: str) -> Dict[str, Any]:
        """Fetch fresh metrics from database"""
        # TODO: Implement actual database queries
        return {
            "orders": {
                "active": 0,
                "completed_today": 0,
                "pending_kitchen": 0
            },
            "revenue": {
                "today": 0.0,
                "this_hour": 0.0
            },
            "tables": {
                "available": 0,
                "occupied": 0,
                "reserved": 0
            },
            "staff": {
                "clocked_in": 0,
                "on_break": 0
            }
        }
    
    def invalidate_cache(self, business_id: str):
        """Invalidate metrics cache"""
        cache_key = f"metrics_{business_id}"
        if cache_key in self.metrics_cache:
            del self.metrics_cache[cache_key]


# Singleton instance
metrics_aggregator = MetricsAggregator()


async def handle_websocket_connection(
    websocket: WebSocket,
    business_id: str,
    connection_type: str = "dashboard"
):
    """Handle WebSocket connection lifecycle"""
    await manager.connect(websocket, business_id, connection_type)
    
    try:
        # Send initial data
        initial_data = await metrics_aggregator.get_realtime_metrics(business_id)
        await manager.send_personal_message({
            "event": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "data": initial_data
        }, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                
                elif message.get("type") == "subscribe":
                    # Handle subscription to specific events
                    pass
                
            except asyncio.TimeoutError:
                # Send heartbeat
                await manager.send_personal_message({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, business_id, connection_type)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, business_id, connection_type)
