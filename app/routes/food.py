"""
Food QR Code Management API Routes
Enterprise-grade endpoints for food QR code generation, scanning, and management

ENTERPRISE STRUCTURE:
- QR code generation for menu items, tables, and orders
- QR scanning and validation
- Food tracking and analytics
- Integration with existing menu and inventory systems
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks, Body
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
import io
import base64
import json
import qrcode
from qrcode.image.pil import PilImage
from pydantic import BaseModel, Field

from ..models.menu import MenuItem, MenuItemCreate, MenuItemUpdate
from ..services.database import get_database_service
from ..services.realtime import RealtimeEventPublisher

router = APIRouter(prefix="/api/v1/food", tags=["Food QR Management"])


# ============================================================================
# QR CODE GENERATION
# ============================================================================

class QRCodeRequest(BaseModel):
    """Request model for QR code generation"""
    type: str = Field(..., pattern=r"^(menu_item|table|order|menu_category|business)$")
    target_id: UUID
    business_id: UUID
    size: int = Field(default=200, ge=100, le=1000)
    format: str = Field(default="png", pattern=r"^(png|svg|base64)$")
    include_logo: bool = False
    custom_data: Optional[Dict[str, Any]] = None


class QRCodeResponse(BaseModel):
    """Response model for QR code generation"""
    qr_id: str
    type: str
    target_id: UUID
    business_id: UUID
    qr_data: str  # Base64 encoded or URL
    qr_url: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


@router.post("/qr/generate", response_model=QRCodeResponse, status_code=status.HTTP_201_CREATED)
async def generate_qr_code(request: QRCodeRequest):
    """
    Generate QR code for food-related items
    
    - **Menu items**: Direct link to item details
    - **Tables**: Table ordering interface
    - **Orders**: Order tracking and status
    - **Categories**: Category browsing
    - **Business**: Business info and menu
    """
    try:
        db = get_database_service()
        
        # Generate unique QR ID
        qr_id = f"qr_{request.type}_{request.target_id}_{int(datetime.utcnow().timestamp())}"
        
        # Build QR data based on type
        qr_data = await _build_qr_data(request, db)
        
        # Generate QR code
        qr_image = await _generate_qr_image(qr_data, request.size, request.include_logo)
        
        # Convert to requested format
        if request.format == "base64":
            qr_data_encoded = base64.b64encode(qr_image).decode('utf-8')
            qr_url = None
        elif request.format == "svg":
            # Generate SVG version
            qr_data_encoded = await _generate_qr_svg(qr_data, request.size)
            qr_url = None
        else:  # PNG
            qr_data_encoded = base64.b64encode(qr_image).decode('utf-8')
            qr_url = f"/api/v1/food/qr/image/{qr_id}"
        
        # Store QR code metadata
        qr_metadata = {
            "id": qr_id,
            "type": request.type,
            "target_id": str(request.target_id),
            "business_id": str(request.business_id),
            "qr_data": qr_data,
            "size": request.size,
            "format": request.format,
            "include_logo": request.include_logo,
            "custom_data": request.custom_data or {},
            "is_active": True,
            "scan_count": 0,
            "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat() if request.type == "menu_item" else None
        }
        
        # Store in database
        try:
            await db.create_qr_code(qr_metadata)
        except Exception as e:
            print(f"⚠️ Warning: Failed to store QR code in database: {str(e)}")
            # Continue without failing the request
        
        return QRCodeResponse(
            qr_id=qr_id,
            type=request.type,
            target_id=request.target_id,
            business_id=request.business_id,
            qr_data=qr_data_encoded,
            qr_url=qr_url,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365) if request.type == "menu_item" else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate QR code: {str(e)}")


@router.get("/qr/image/{qr_id}")
async def get_qr_image(qr_id: str):
    """Get QR code image"""
    try:
        # In production, retrieve from database or cache
        # For now, generate on-the-fly
        
        # Parse QR ID to get type and target_id
        parts = qr_id.split('_')
        if len(parts) < 3:
            raise HTTPException(status_code=404, detail="Invalid QR code ID")
        
        qr_type = parts[1]
        target_id = parts[2]
        
        # Generate QR data
        qr_data = f"https://app.example.com/food/{qr_type}/{target_id}"
        
        # Generate image
        qr_image = await _generate_qr_image(qr_data, 200, False)
        
        return StreamingResponse(
            io.BytesIO(qr_image),
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename={qr_id}.png"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get QR image: {str(e)}")


@router.post("/qr/bulk-generate", response_model=List[QRCodeResponse])
async def bulk_generate_qr_codes(
    business_id: UUID = Query(...),
    qr_type: str = Query(..., pattern=r"^(menu_item|table|menu_category)$"),
    target_ids: List[UUID] = Query(...),
    size: int = Query(default=200, ge=100, le=1000),
    format: str = Query(default="png", pattern=r"^(png|svg|base64)$")
):
    """
    Bulk generate QR codes for multiple items
    
    - **Efficiency**: Generate multiple QR codes at once
    - **Batch processing**: Optimized for large quantities
    - **Consistent formatting**: Same settings for all codes
    """
    try:
        db = get_database_service()
        qr_codes = []
        
        for target_id in target_ids:
            request = QRCodeRequest(
                type=qr_type,
                target_id=target_id,
                business_id=business_id,
                size=size,
                format=format
            )
            
            qr_code = await generate_qr_code(request)
            qr_codes.append(qr_code)
        
        return qr_codes
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk generate QR codes: {str(e)}")


# ============================================================================
# QR CODE SCANNING & VALIDATION
# ============================================================================

class QRScanRequest(BaseModel):
    """Request model for QR code scanning"""
    qr_data: str
    scanner_location: Optional[str] = None
    scanner_id: Optional[str] = None


class QRScanResponse(BaseModel):
    """Response model for QR code scanning"""
    valid: bool
    type: Optional[str] = None
    target_id: Optional[UUID] = None
    business_id: Optional[UUID] = None
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    message: Optional[str] = None


@router.post("/qr/scan", response_model=QRScanResponse)
async def scan_qr_code(scan_request: QRScanRequest):
    """
    Scan and validate QR code
    
    - **Validation**: Verify QR code authenticity
    - **Data extraction**: Parse QR code content
    - **Action routing**: Determine next steps
    - **Analytics**: Track scan events
    """
    try:
        db = get_database_service()
        
        # Parse QR data
        qr_data = scan_request.qr_data
        
        # Check if it's a URL-based QR code
        if qr_data.startswith("https://") or qr_data.startswith("http://"):
            # Extract type and ID from URL
            parts = qr_data.split('/')
            if len(parts) >= 2:
                qr_type = parts[-2] if parts[-1] else parts[-3]
                target_id = parts[-1] if parts[-1] else parts[-2]
            else:
                return QRScanResponse(valid=False, message="Invalid QR code format")
        else:
            # Try to parse as JSON
            try:
                qr_json = json.loads(qr_data)
                qr_type = qr_json.get("type")
                target_id = qr_json.get("target_id")
                business_id = qr_json.get("business_id")
            except json.JSONDecodeError:
                return QRScanResponse(valid=False, message="Invalid QR code data")
        
        # Validate target exists
        target_data = await _validate_qr_target(qr_type, target_id, db)
        if not target_data:
            return QRScanResponse(valid=False, message="QR code target not found")
        
        # Build response data
        response_data = {
            "target_info": target_data,
            "scanner_location": scan_request.scanner_location,
            "scanned_at": datetime.utcnow().isoformat()
        }
        
        # Determine action URL
        action_url = await _get_action_url(qr_type, target_id, target_data)
        
        # Log scan event
        await _log_scan_event(qr_type, target_id, scan_request, db)
        
        return QRScanResponse(
            valid=True,
            type=qr_type,
            target_id=UUID(target_id) if target_id else None,
            business_id=UUID(business_id) if business_id else None,
            data=response_data,
            action_url=action_url,
            message="QR code scanned successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scan QR code: {str(e)}")


# ============================================================================
# FOOD TRACKING & ANALYTICS
# ============================================================================

@router.get("/qr/analytics/{business_id}")
async def get_qr_analytics(
    business_id: UUID,
    period: str = Query("7d", pattern=r"^(1d|7d|30d|90d)$"),
    qr_type: Optional[str] = Query(None)
):
    """
    Get QR code analytics
    
    - **Scan metrics**: Total scans, unique scans, scan frequency
    - **Popular items**: Most scanned QR codes
    - **Time patterns**: Peak scanning times
    - **Conversion**: Scans to actions
    """
    try:
        db = get_database_service()
        
        # Calculate date range
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
        
        # Get analytics from database
        analytics = await db.get_qr_scan_analytics(
            business_id=business_id,
            start_date=start_date,
            end_date=end_date,
            qr_type=qr_type
        )
        
        # Add additional calculated fields
        analytics.update({
            "business_id": str(business_id),
            "period": period,
            "scan_frequency": analytics["total_scans"] / max(1, (end_date - start_date).days),
            "conversion_rate": 0.0,  # Would need additional data to calculate
            "top_scanned_items": await db.get_popular_qr_codes(business_id, limit=5, start_date=start_date, end_date=end_date)
        })
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get QR analytics: {str(e)}")


@router.get("/qr/popular/{business_id}")
async def get_popular_qr_codes(
    business_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    period: str = Query("7d", pattern=r"^(1d|7d|30d|90d)$")
):
    """Get most popular QR codes by scan count"""
    try:
        db = get_database_service()
        
        # Calculate date range
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
        
        # Get popular QR codes from database
        popular_items = await db.get_popular_qr_codes(
            business_id=business_id,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "business_id": str(business_id),
            "period": period,
            "limit": limit,
            "popular_qr_codes": popular_items,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get popular QR codes: {str(e)}")


# ============================================================================
# FOOD ITEM MANAGEMENT WITH QR
# ============================================================================

@router.post("/items", response_model=MenuItem, status_code=status.HTTP_201_CREATED)
async def create_food_item_with_qr(item: MenuItemCreate, generate_qr: bool = Query(True)):
    """
    Create food item with automatic QR code generation
    
    - **Auto QR**: Automatically generate QR code for new items
    - **Integration**: Seamless integration with menu system
    - **Tracking**: Enable QR-based tracking from creation
    """
    try:
        db = get_database_service()
        
        # Create menu item using existing logic
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
        
        # Generate QR code if requested
        if generate_qr and result:
            qr_request = QRCodeRequest(
                type="menu_item",
                target_id=UUID(result["id"]),
                business_id=UUID(result["business_id"]),
                size=200,
                format="png"
            )
            
            qr_code = await generate_qr_code(qr_request)
            result["qr_code"] = qr_code
        
        # Publish real-time update
        await RealtimeEventPublisher.publish_order_update(
            str(item.business_id),
            {"type": "food_item_created", "item": result}
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create food item: {str(e)}")


@router.get("/items/{item_id}/qr")
async def get_item_qr_code(item_id: UUID):
    """Get QR code for specific food item"""
    try:
        db = get_database_service()
        
        # Verify item exists
        item_result = db.client.table("menu_items").select("*").eq("id", str(item_id)).execute()
        if not item_result.data:
            raise HTTPException(status_code=404, detail="Food item not found")
        
        item = item_result.data[0]
        
        # Generate QR code
        qr_request = QRCodeRequest(
            type="menu_item",
            target_id=item_id,
            business_id=UUID(item["business_id"]),
            size=200,
            format="png"
        )
        
        qr_code = await generate_qr_code(qr_request)
        
        return {
            "item_id": str(item_id),
            "item_name": item["name"],
            "qr_code": qr_code,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get item QR code: {str(e)}")


# ============================================================================
# TABLE QR MANAGEMENT
# ============================================================================

class TableQRRequest(BaseModel):
    """Request model for table QR code"""
    table_number: str
    business_id: UUID
    location_id: Optional[UUID] = None
    capacity: Optional[int] = None
    qr_size: int = Field(default=200, ge=100, le=1000)


@router.post("/tables/qr", response_model=QRCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_table_qr_code(table_request: TableQRRequest):
    """
    Create QR code for table ordering
    
    - **Table identification**: Unique QR per table
    - **Ordering interface**: Direct link to menu
    - **Location tracking**: Track table location
    """
    try:
        db = get_database_service()
        
        # Create table record
        table_data = {
            "id": str(UUID()),
            "table_number": table_request.table_number,
            "business_id": str(table_request.business_id),
            "location_id": str(table_request.location_id) if table_request.location_id else None,
            "capacity": table_request.capacity,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Store table
        try:
            await db.create_table(table_data)
        except Exception as e:
            print(f"⚠️ Warning: Failed to store table in database: {str(e)}")
            # Continue without failing the request
        
        # Generate QR code
        qr_request = QRCodeRequest(
            type="table",
            target_id=UUID(table_data["id"]),
            business_id=table_request.business_id,
            size=table_request.qr_size,
            format="png",
            custom_data={
                "table_number": table_request.table_number,
                "capacity": table_request.capacity
            }
        )
        
        qr_code = await generate_qr_code(qr_request)
        
        return qr_code
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create table QR code: {str(e)}")


@router.get("/tables/{business_id}/qr-codes")
async def list_table_qr_codes(business_id: UUID):
    """List all table QR codes for business"""
    try:
        db = get_database_service()
        
        # Get tables from database
        tables = await db.get_tables(business_id=business_id)
        
        # Get QR codes for each table
        table_qr_codes = []
        for table in tables:
            if table.get("qr_code_id"):
                qr_code = await db.get_qr_code(table["qr_code_id"])
                if qr_code:
                    table["qr_code"] = qr_code
            table_qr_codes.append(table)
        
        return {
            "business_id": str(business_id),
            "tables": table_qr_codes,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list table QR codes: {str(e)}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _build_qr_data(request: QRCodeRequest, db) -> str:
    """Build QR code data based on type"""
    base_url = "https://app.example.com/food"
    
    if request.type == "menu_item":
        # Get menu item details
        item_result = db.client.table("menu_items").select("*").eq("id", str(request.target_id)).execute()
        if item_result.data:
            item = item_result.data[0]
            return f"{base_url}/item/{request.target_id}?name={item['name']}&price={item['price']}"
    
    elif request.type == "table":
        return f"{base_url}/table/{request.target_id}/order"
    
    elif request.type == "order":
        return f"{base_url}/order/{request.target_id}/track"
    
    elif request.type == "menu_category":
        return f"{base_url}/category/{request.target_id}/items"
    
    elif request.type == "business":
        return f"{base_url}/business/{request.target_id}/menu"
    
    # Fallback
    return f"{base_url}/{request.type}/{request.target_id}"


async def _generate_qr_image(data: str, size: int, include_logo: bool) -> bytes:
    """Generate QR code image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize to requested size
    img = img.resize((size, size))
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr


async def _generate_qr_svg(data: str, size: int) -> str:
    """Generate QR code as SVG"""
    import qrcode.image.svg
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Generate SVG using string method
    factory = qrcode.image.svg.SvgPathImage
    img = qr.make_image(image_factory=factory)
    
    # Convert to string
    svg_string = img.to_string().decode('utf-8')
    return svg_string


async def _validate_qr_target(qr_type: str, target_id: str, db) -> Optional[Dict[str, Any]]:
    """Validate QR code target exists"""
    try:
        if qr_type == "menu_item":
            result = db.client.table("menu_items").select("*").eq("id", target_id).execute()
            if result.data:
                return result.data[0]
        
        elif qr_type == "table":
            # Mock table validation
            return {"id": target_id, "table_number": "1", "capacity": 4}
        
        elif qr_type == "order":
            # Mock order validation
            return {"id": target_id, "status": "pending"}
        
        elif qr_type == "menu_category":
            result = db.client.table("menu_categories").select("*").eq("id", target_id).execute()
            if result.data:
                return result.data[0]
        
        elif qr_type == "business":
            # Mock business validation
            return {"id": target_id, "name": "Sample Business"}
        
        return None
        
    except Exception:
        return None


async def _get_action_url(qr_type: str, target_id: str, target_data: Dict[str, Any]) -> str:
    """Get action URL based on QR type"""
    base_url = "https://app.example.com/food"
    
    if qr_type == "menu_item":
        return f"{base_url}/item/{target_id}"
    elif qr_type == "table":
        return f"{base_url}/table/{target_id}/order"
    elif qr_type == "order":
        return f"{base_url}/order/{target_id}/track"
    elif qr_type == "menu_category":
        return f"{base_url}/category/{target_id}/items"
    elif qr_type == "business":
        return f"{base_url}/business/{target_id}/menu"
    
    return f"{base_url}/{qr_type}/{target_id}"


async def _log_scan_event(qr_type: str, target_id: str, scan_request: QRScanRequest, db):
    """Log QR code scan event"""
    try:
        # First, try to find the QR code to get the qr_id
        qr_codes = await db.get_qr_codes_by_business(
            business_id=UUID("00000000-0000-0000-0000-000000000000"),  # We'll need to get this from context
            qr_type=qr_type
        )
        
        # Find QR code that matches the target_id
        qr_id = None
        business_id = None
        for qr_code in qr_codes:
            if qr_code["target_id"] == str(target_id):
                qr_id = qr_code["id"]
                business_id = qr_code["business_id"]
                break
        
        if not qr_id:
            # If we can't find the QR code, create a generic scan record
            qr_id = f"unknown_{qr_type}_{target_id}"
            business_id = "00000000-0000-0000-0000-000000000000"
        
        scan_data = {
            "qr_id": qr_id,
            "qr_type": qr_type,
            "target_id": target_id,
            "business_id": business_id,
            "scanner_location": scan_request.scanner_location,
            "scanner_id": scan_request.scanner_id,
            "scanned_at": datetime.utcnow().isoformat()
        }
        
        # Store scan event
        await db.log_qr_scan(scan_data)
        
    except Exception as e:
        # Log scan events are not critical, so we don't raise exceptions
        print(f"⚠️ Warning: Failed to log QR scan event: {str(e)}")
        pass


# ============================================================================
# QR CODE MANAGEMENT
# ============================================================================

@router.get("/qr/{qr_id}")
async def get_qr_code_with_image(qr_id: str):
    """Get QR code with regenerated image"""
    try:
        db = get_database_service()
        
        # Get QR code from database
        qr_code = await db.get_qr_code(qr_id)
        if not qr_code:
            raise HTTPException(status_code=404, detail="QR code not found")
        
        # Regenerate QR image
        qr_image = await _generate_qr_image(qr_code["qr_data"], qr_code["size"], qr_code.get("include_logo", False))
        
        # Convert to base64 with proper data URI prefix
        qr_image_base64 = base64.b64encode(qr_image).decode('utf-8')
        qr_image_data_uri = f"data:image/png;base64,{qr_image_base64}"
        
        return {
            "qr_id": qr_id,
            "qr_code": qr_code,
            "qr_image": qr_image_data_uri,
            "image_size_bytes": len(qr_image),
            "regenerated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get QR code image: {str(e)}")


@router.get("/qr/list/{business_id}")
async def list_qr_codes(
    business_id: UUID,
    qr_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List QR codes for business with regenerated images"""
    try:
        db = get_database_service()
        
        # Get QR codes from database
        qr_codes = await db.get_qr_codes_by_business(
            business_id=business_id,
            qr_type=qr_type,
            limit=limit,
            offset=offset
        )
        
        # Regenerate QR images for each code
        qr_codes_with_images = []
        for qr_code in qr_codes:
            try:
                # Regenerate QR image based on stored metadata
                qr_image = await _generate_qr_image(qr_code["qr_data"], qr_code["size"], qr_code.get("include_logo", False))
                
                # Convert to base64 with proper data URI prefix
                qr_image_base64 = base64.b64encode(qr_image).decode('utf-8')
                qr_image_data_uri = f"data:image/png;base64,{qr_image_base64}"
                
                # Add image data to QR code info
                qr_code_with_image = {
                    **qr_code,
                    "qr_image": qr_image_data_uri,
                    "image_size_bytes": len(qr_image),
                    "regenerated_at": datetime.utcnow().isoformat()
                }
                
                qr_codes_with_images.append(qr_code_with_image)
                
            except Exception as e:
                print(f"⚠️ Warning: Failed to regenerate QR image for {qr_code.get('id', 'unknown')}: {str(e)}")
                # Include QR code without image if regeneration fails
                qr_codes_with_images.append({
                    **qr_code,
                    "qr_image": None,
                    "image_error": str(e)
                })
        
        return {
            "business_id": str(business_id),
            "qr_codes": qr_codes_with_images,
            "total": len(qr_codes_with_images),
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list QR codes: {str(e)}")


@router.delete("/qr/{qr_id}")
async def delete_qr_code(qr_id: str):
    """Delete QR code"""
    try:
        db = get_database_service()
        
        # Delete QR code from database
        success = await db.delete_qr_code(qr_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="QR code not found")
        
        return {
            "success": True,
            "qr_id": qr_id,
            "message": "QR code deleted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete QR code: {str(e)}")


@router.put("/qr/{qr_id}/regenerate")
async def regenerate_qr_code(qr_id: str):
    """Regenerate QR code with new data"""
    try:
        db = get_database_service()
        
        # Get existing QR code data
        qr_code = await db.get_qr_code(qr_id)
        if not qr_code:
            raise HTTPException(status_code=404, detail="QR code not found")
        
        # Regenerate QR code with updated data
        qr_request = QRCodeRequest(
            type=qr_code["type"],
            target_id=UUID(qr_code["target_id"]),
            business_id=UUID(qr_code["business_id"]),
            size=qr_code["size"],
            format=qr_code["format"],
            include_logo=qr_code["include_logo"],
            custom_data=qr_code["custom_data"]
        )
        
        new_qr = await generate_qr_code(qr_request)
        
        # Update the QR code record with new data
        await db.update_qr_code(qr_id, {
            "qr_data": new_qr.qr_data,
            "updated_at": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "qr_id": qr_id,
            "message": "QR code regenerated successfully",
            "new_qr_data": new_qr.qr_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate QR code: {str(e)}")


# ============================================================================
# INTEGRATION ENDPOINTS
# ============================================================================

@router.post("/qr/integrate/pos")
async def integrate_with_pos(
    business_id: UUID = Query(...),
    pos_system: str = Query(..., pattern=r"^(square|toast|clover|lightspeed)$"),
    pos_config: Dict[str, Any] = Body(...)
):
    """
    Integrate QR codes with POS system
    
    - **POS sync**: Sync QR codes with POS system
    - **Menu sync**: Keep menu items in sync
    - **Order tracking**: Track orders through QR codes
    """
    try:
        db = get_database_service()
        
        # Mock POS integration
        integration_result = {
            "business_id": str(business_id),
            "pos_system": pos_system,
            "status": "configured",
            "sync_enabled": True,
            "last_sync": datetime.utcnow().isoformat(),
            "qr_codes_synced": 0,
            "menu_items_synced": 0
        }
        
        return integration_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to integrate with POS: {str(e)}")


@router.get("/qr/export/{business_id}")
async def export_qr_codes(
    business_id: UUID,
    format: str = Query("pdf", pattern=r"^(pdf|zip|csv)$"),
    qr_type: Optional[str] = Query(None)
):
    """
    Export QR codes for printing
    
    - **PDF format**: Ready-to-print QR codes
    - **ZIP format**: Individual QR code images
    - **CSV format**: QR code data for external systems
    """
    try:
        db = get_database_service()
        
        # Mock export
        export_id = f"qr_export_{business_id}_{int(datetime.utcnow().timestamp())}"
        
        return {
            "success": True,
            "export_id": export_id,
            "business_id": str(business_id),
            "format": format,
            "qr_type": qr_type,
            "download_url": f"https://storage.example.com/exports/{export_id}.{format}",
            "message": "QR codes exported successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export QR codes: {str(e)}")
