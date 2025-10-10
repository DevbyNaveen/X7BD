"""
Pydantic models for Retail Template
(Retail Store, Boutique, Grocery Store, Pharmacy, Electronics Store, etc.)
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID


# ============================================================================
# PRODUCTS MODELS
# ============================================================================

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    price: float = Field(..., ge=0)
    cost: Optional[float] = Field(None, ge=0)
    compare_at_price: Optional[float] = Field(None, ge=0)
    tax_rate: float = Field(default=0, ge=0, le=100)
    weight: Optional[float] = Field(None, ge=0)
    weight_unit: Optional[str] = Field(None, max_length=20)
    dimensions: Optional[dict] = None
    image_urls: Optional[List[str]] = []
    is_available: bool = True
    track_inventory: bool = True
    inventory_quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=10, ge=0)
    tags: Optional[List[str]] = []
    variants: Optional[List[dict]] = []
    metadata: Optional[dict] = {}


class ProductCreate(ProductBase):
    business_id: UUID


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    price: Optional[float] = Field(None, ge=0)
    cost: Optional[float] = Field(None, ge=0)
    compare_at_price: Optional[float] = Field(None, ge=0)
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    weight: Optional[float] = Field(None, ge=0)
    weight_unit: Optional[str] = Field(None, max_length=20)
    dimensions: Optional[dict] = None
    image_urls: Optional[List[str]] = None
    is_available: Optional[bool] = None
    track_inventory: Optional[bool] = None
    inventory_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    tags: Optional[List[str]] = None
    variants: Optional[List[dict]] = None
    metadata: Optional[dict] = None


class ProductResponse(ProductBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CUSTOMERS MODELS
# ============================================================================

class CustomerBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    customer_type: str = Field(default="regular", pattern="^(regular|vip|wholesale)$")
    tags: Optional[List[str]] = []
    notes: Optional[str] = None
    marketing_consent: bool = False
    is_active: bool = True


class CustomerCreate(CustomerBase):
    business_id: UUID


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    customer_type: Optional[str] = Field(None, pattern="^(regular|vip|wholesale)$")
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    marketing_consent: Optional[bool] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    id: UUID
    business_id: UUID
    loyalty_points: int = 0
    total_orders: int = 0
    total_spent: float = 0
    avg_order_value: float = 0
    last_order_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CUSTOMER ANALYTICS
# ============================================================================

class CustomerAnalyticsResponse(BaseModel):
    customer: CustomerResponse
    purchase_history: List[dict]
    favorite_products: List[dict]
    total_orders: int
    total_spent: float
    avg_order_value: float
    last_purchase_date: Optional[datetime]
    lifetime_value: float
