"""
WebSocket Routes for Real-time Updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from uuid import UUID
from ..services.realtime import handle_websocket_connection

router = APIRouter(prefix="/api/v1/ws", tags=["websocket"])


@router.websocket("/dashboard/{business_id}")
async def dashboard_websocket(
    websocket: WebSocket,
    business_id: str
):
    """
    WebSocket endpoint for real-time dashboard updates
    
    **Events published:**
    - `order_update`: New orders, status changes
    - `table_update`: Table status changes
    - `revenue_update`: Real-time revenue updates
    - `inventory_alert`: Low stock alerts
    - `staff_update`: Clock in/out events
    
    **Client messages:**
    - `{"type": "ping"}`: Keepalive ping
    - `{"type": "subscribe", "events": ["order_update"]}`: Subscribe to specific events
    """
    await handle_websocket_connection(websocket, business_id, "dashboard")


@router.websocket("/kds/{business_id}")
async def kds_websocket(
    websocket: WebSocket,
    business_id: str,
    station: str = Query(None)
):
    """
    WebSocket endpoint for Kitchen Display System
    
    **Events published:**
    - `kds_update`: New orders, status changes
    - `order_priority`: Priority order alerts
    - `order_late`: Late order warnings
    
    **Client messages:**
    - `{"type": "status_update", "order_id": "...", "status": "preparing"}`: Update order status
    """
    await handle_websocket_connection(websocket, business_id, "kds")


@router.websocket("/tables/{business_id}")
async def tables_websocket(
    websocket: WebSocket,
    business_id: str,
    location_id: str = Query(None)
):
    """
    WebSocket endpoint for table management
    
    **Events published:**
    - `table_update`: Table status changes
    - `reservation_update`: New reservations
    - `seating_alert`: Seating recommendations
    """
    await handle_websocket_connection(websocket, business_id, "tables")
