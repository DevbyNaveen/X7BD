"""
Food QR Code Management Models
Enterprise-grade data models for food QR code functionality

ENTERPRISE STRUCTURE:
- QR code generation and management
- Food tracking and analytics
- Table management with QR codes
- Integration with existing menu system
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class QRCodeBase(BaseModel):
    """Base QR code model"""
    type: str = Field(..., pattern=r"^(menu_item|table|order|menu_category|business)$")
    target_id: UUID
    business_id: UUID
    qr_data: str
    size: int = Field(default=200, ge=100, le=1000)
    format: str = Field(default="png", pattern=r"^(png|svg|base64)$")
    include_logo: bool = False
    custom_data: Optional[Dict[str, Any]] = None
    is_active: bool = True


class QRCodeCreate(QRCodeBase):
    """Create QR code"""
    pass


class QRCodeUpdate(BaseModel):
    """Update QR code"""
    is_active: Optional[bool] = None
    custom_data: Optional[Dict[str, Any]] = None


class QRCode(QRCodeBase):
    """QR code response model"""
    id: str
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    scan_count: int = Field(default=0, ge=0)
    
    class Config:
        from_attributes = True


class QRScanEvent(BaseModel):
    """QR code scan event"""
    qr_id: str
    qr_type: str
    target_id: UUID
    business_id: UUID
    scanner_location: Optional[str] = None
    scanner_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    scanned_at: datetime = Field(default_factory=datetime.utcnow)


class QRScanEventCreate(BaseModel):
    """Create QR scan event"""
    qr_id: str
    qr_type: str
    target_id: UUID
    business_id: UUID
    scanner_location: Optional[str] = None
    scanner_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class QRScanEventResponse(QRScanEvent):
    """QR scan event response"""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class TableBase(BaseModel):
    """Base table model"""
    table_number: str = Field(..., min_length=1, max_length=50)
    business_id: UUID
    location_id: Optional[UUID] = None
    capacity: Optional[int] = Field(None, ge=1, le=20)
    qr_code_id: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TableCreate(TableBase):
    """Create table"""
    pass


class TableUpdate(BaseModel):
    """Update table"""
    table_number: Optional[str] = Field(None, min_length=1, max_length=50)
    location_id: Optional[UUID] = None
    capacity: Optional[int] = Field(None, ge=1, le=20)
    qr_code_id: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class Table(TableBase):
    """Table response model"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TableWithQR(Table):
    """Table with QR code details"""
    qr_code: Optional[QRCode] = None


class FoodItemQR(BaseModel):
    """Food item with QR code"""
    item_id: UUID
    item_name: str
    item_price: Decimal
    qr_code: QRCode
    qr_url: Optional[str] = None
    created_at: datetime


class QRCodeAnalytics(BaseModel):
    """QR code analytics"""
    business_id: UUID
    period: str
    total_scans: int
    unique_scans: int
    scan_frequency: float
    top_scanned_items: List[Dict[str, Any]]
    scan_trends: List[Dict[str, Any]]
    conversion_rate: float
    peak_hours: List[Dict[str, Any]]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class QRCodeExport(BaseModel):
    """QR code export request"""
    business_id: UUID
    qr_type: Optional[str] = None
    format: str = Field(default="pdf", pattern=r"^(pdf|zip|csv)$")
    include_inactive: bool = False
    size: int = Field(default=200, ge=100, le=1000)
    include_logo: bool = False


class QRCodeExportResponse(BaseModel):
    """QR code export response"""
    export_id: str
    business_id: UUID
    format: str
    qr_count: int
    download_url: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)


class POSIntegration(BaseModel):
    """POS system integration"""
    business_id: UUID
    pos_system: str = Field(..., pattern=r"^(square|toast|clover|lightspeed)$")
    pos_config: Dict[str, Any]
    sync_enabled: bool = True
    last_sync: Optional[datetime] = None
    qr_codes_synced: int = Field(default=0, ge=0)
    menu_items_synced: int = Field(default=0, ge=0)


class POSIntegrationCreate(BaseModel):
    """Create POS integration"""
    business_id: UUID
    pos_system: str = Field(..., pattern=r"^(square|toast|clover|lightspeed)$")
    pos_config: Dict[str, Any]
    sync_enabled: bool = True


class POSIntegrationResponse(POSIntegration):
    """POS integration response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QRCodeBulkGenerate(BaseModel):
    """Bulk QR code generation request"""
    business_id: UUID
    qr_type: str = Field(..., pattern=r"^(menu_item|table|menu_category)$")
    target_ids: List[UUID]
    size: int = Field(default=200, ge=100, le=1000)
    format: str = Field(default="png", pattern=r"^(png|svg|base64)$")
    include_logo: bool = False


class QRCodeBulkGenerateResponse(BaseModel):
    """Bulk QR code generation response"""
    business_id: UUID
    qr_type: str
    generated_count: int
    failed_count: int
    qr_codes: List[QRCode]
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QRCodeSearch(BaseModel):
    """QR code search"""
    business_id: UUID
    qr_type: Optional[str] = None
    is_active: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class QRCodeSearchResponse(BaseModel):
    """QR code search response"""
    qr_codes: List[QRCode]
    total: int
    limit: int
    offset: int
    has_more: bool


class FoodTrackingEvent(BaseModel):
    """Food tracking event"""
    item_id: UUID
    business_id: UUID
    event_type: str = Field(..., pattern=r"^(created|scanned|ordered|prepared|served|wasted)$")
    event_data: Dict[str, Any] = Field(default_factory=dict)
    location: Optional[str] = None
    user_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FoodTrackingEventCreate(BaseModel):
    """Create food tracking event"""
    item_id: UUID
    business_id: UUID
    event_type: str = Field(..., pattern=r"^(created|scanned|ordered|prepared|served|wasted)$")
    event_data: Dict[str, Any] = Field(default_factory=dict)
    location: Optional[str] = None
    user_id: Optional[UUID] = None


class FoodTrackingEventResponse(FoodTrackingEvent):
    """Food tracking event response"""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class FoodItemAnalytics(BaseModel):
    """Food item analytics"""
    item_id: UUID
    item_name: str
    business_id: UUID
    total_scans: int
    total_orders: int
    conversion_rate: float
    avg_prep_time: Optional[float] = None
    popularity_score: float
    last_scan: Optional[datetime] = None
    scan_trend: List[Dict[str, Any]] = Field(default_factory=list)
    period: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class QRCodeTemplate(BaseModel):
    """QR code template"""
    name: str
    business_id: UUID
    template_data: Dict[str, Any]
    is_default: bool = False
    is_active: bool = True


class QRCodeTemplateCreate(BaseModel):
    """Create QR code template"""
    name: str
    business_id: UUID
    template_data: Dict[str, Any]
    is_default: bool = False


class QRCodeTemplateUpdate(BaseModel):
    """Update QR code template"""
    name: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class QRCodeTemplateResponse(QRCodeTemplate):
    """QR code template response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
