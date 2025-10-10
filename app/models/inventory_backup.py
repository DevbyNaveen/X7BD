"""
Inventory Management Models
Enterprise-grade data models for inventory tracking and management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from enum import Enum


class TransactionType(str, Enum):
    """Inventory transaction types"""
    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    WASTE = "waste"
    RETURN = "return"


class AlertType(str, Enum):
    """Stock alert types"""
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRING = "expiring"
    OVERSTOCKED = "overstocked"


class PurchaseOrderStatus(str, Enum):
    """Purchase order statuses"""
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class InventoryItemBase(BaseModel):
    """Base inventory item model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    unit: str = Field(..., max_length=50)  # kg, lbs, units, etc.
    current_stock: Decimal = Field(default=Decimal("0.00"), ge=0)
    min_stock: Decimal = Field(default=Decimal("0.00"), ge=0)
    max_stock: Optional[Decimal] = Field(None, ge=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0, )
    supplier_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    category: Optional[str] = Field(None, max_length=100)
    is_tracked: bool = True
    
    @validator('max_stock')
    def validate_max_stock(cls, v, values):
        if v is not None and 'min_stock' in values:
            if v < values['min_stock']:
                raise ValueError('max_stock must be >= min_stock')
        return v


class InventoryItemCreate(InventoryItemBase):
    """Create inventory item"""
    business_id: UUID


class InventoryItemUpdate(BaseModel):
    """Update inventory item"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    current_stock: Optional[Decimal] = Field(None, ge=0)
    min_stock: Optional[Decimal] = Field(None, ge=0)
    max_stock: Optional[Decimal] = Field(None, ge=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0, )
    supplier_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    category: Optional[str] = Field(None, max_length=100)
    is_tracked: Optional[bool] = None


class InventoryItem(InventoryItemBase):
    """Inventory item response model"""
    id: UUID
    business_id: UUID
    last_counted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InventoryItemWithMetrics(InventoryItem):
    """Inventory item with calculated metrics"""
    stock_percentage: Optional[Decimal] = None
    stock_value: Optional[Decimal] = None
    needs_reorder: bool = False
    days_of_stock: Optional[int] = None
    
    @validator('stock_percentage', always=True)
    def calculate_stock_percentage(cls, v, values):
        if 'current_stock' in values and 'max_stock' in values and values['max_stock']:
            return (values['current_stock'] / values['max_stock'] * 100).quantize(Decimal('0.01'))
        return None
    
    @validator('stock_value', always=True)
    def calculate_stock_value(cls, v, values):
        if 'current_stock' in values and 'unit_cost' in values and values['unit_cost']:
            return (values['current_stock'] * values['unit_cost']).quantize(Decimal('0.01'))
        return None
    
    @validator('needs_reorder', always=True)
    def check_reorder(cls, v, values):
        if 'current_stock' in values and 'min_stock' in values:
            return values['current_stock'] <= values['min_stock']
        return False


class InventoryTransactionBase(BaseModel):
    """Base inventory transaction model"""
    inventory_item_id: UUID
    transaction_type: TransactionType
    quantity: Decimal = Field(..., )
    unit_cost: Optional[Decimal] = Field(None, ge=0, )
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[UUID] = None
    notes: Optional[str] = None


class InventoryTransactionCreate(InventoryTransactionBase):
    """Create inventory transaction"""
    business_id: UUID
    performed_by: Optional[UUID] = None


class InventoryTransaction(InventoryTransactionBase):
    """Inventory transaction response model"""
    id: UUID
    business_id: UUID
    performed_by: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class StockAdjustment(BaseModel):
    """Quick stock adjustment"""
    inventory_item_id: UUID
    new_quantity: Decimal = Field(..., ge=0)
    reason: str
    notes: Optional[str] = None


class StockAlertBase(BaseModel):
    """Base stock alert model"""
    inventory_item_id: UUID
    alert_type: AlertType
    threshold: Optional[Decimal] = Field(None, ge=0)
    is_active: bool = True


class StockAlertCreate(StockAlertBase):
    """Create stock alert"""
    business_id: UUID


class StockAlert(StockAlertBase):
    """Stock alert response model"""
    id: UUID
    business_id: UUID
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SupplierBase(BaseModel):
    """Base supplier model"""
    name: str = Field(..., min_length=1, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class SupplierCreate(SupplierBase):
    """Create supplier"""
    business_id: UUID


class SupplierUpdate(BaseModel):
    """Update supplier"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class Supplier(SupplierBase):
    """Supplier response model"""
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PurchaseOrderItem(BaseModel):
    """Purchase order item"""
    inventory_item_id: UUID
    quantity: Decimal = Field(..., gt=0, )
    unit_cost: Decimal = Field(..., ge=0, )
    total_amount: Decimal = Field(..., ge=0, )


class PurchaseOrderBase(BaseModel):
    """Base purchase order model"""
    supplier_id: UUID
{{ ... }}
    expected_delivery_date: Optional[datetime] = None
    items: List[PurchaseOrderItem]
    notes: Optional[str] = None
    
    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('Purchase order must have at least one item')
        return v


class PurchaseOrderCreate(PurchaseOrderBase):
    """Create purchase order"""
    business_id: UUID


class PurchaseOrderUpdate(BaseModel):
    """Update purchase order"""
    status: Optional[PurchaseOrderStatus] = None
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None


class PurchaseOrder(PurchaseOrderBase):
    """Purchase order response model"""
    id: UUID
    business_id: UUID
    order_number: str
    status: PurchaseOrderStatus
    total_amount: Decimal
    actual_delivery_date: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InventoryReport(BaseModel):
    """Inventory report"""
    business_id: UUID
    report_date: datetime
    total_items: int
    total_value: Decimal
    low_stock_items: int
    out_of_stock_items: int
    items_by_category: Dict[str, int]
    top_value_items: List[Dict[str, Any]]


class InventorySearch(BaseModel):
    """Search inventory items"""
    query: Optional[str] = None
    category: Optional[str] = None
    supplier_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    low_stock_only: bool = False
    out_of_stock_only: bool = False
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
