"""
Menu Management Models
Enterprise-grade data models for menu items, categories, and modifiers
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class MenuCategoryBase(BaseModel):
    """Base menu category model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    display_order: int = Field(default=0, ge=0)
    icon_url: Optional[str] = None
    is_active: bool = True


class MenuCategoryCreate(MenuCategoryBase):
    """Create menu category"""
    business_id: UUID


class MenuCategoryUpdate(BaseModel):
    """Update menu category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    display_order: Optional[int] = Field(None, ge=0)
    icon_url: Optional[str] = None
    is_active: Optional[bool] = None


class MenuCategory(MenuCategoryBase):
    """Menu category response model"""
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ModifierOption(BaseModel):
    """Modifier option (e.g., specific topping)"""
    name: str
    price: Decimal = Field(default=Decimal("0.00"), ge=0)
    is_default: bool = False


class ItemModifierBase(BaseModel):
    """Base item modifier model"""
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern=r"^(single|multiple)$")
    required: bool = False
    min_selections: int = Field(default=0, ge=0)
    max_selections: Optional[int] = Field(None, ge=1)
    options: List[ModifierOption]
    
    @validator('max_selections')
    def validate_max_selections(cls, v, values):
        if v is not None and 'min_selections' in values:
            if v < values['min_selections']:
                raise ValueError('max_selections must be >= min_selections')
        return v


class ItemModifierCreate(ItemModifierBase):
    """Create item modifier"""
    business_id: UUID


class ItemModifierUpdate(BaseModel):
    """Update item modifier"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, pattern=r"^(single|multiple)$")
    required: Optional[bool] = None
    min_selections: Optional[int] = Field(None, ge=0)
    max_selections: Optional[int] = Field(None, ge=1)
    options: Optional[List[ModifierOption]] = None


class ItemModifier(ItemModifierBase):
    """Item modifier response model"""
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MenuItemVariant(BaseModel):
    """Menu item variant (e.g., size, color)"""
    name: str
    price_adjustment: Decimal = Decimal("0.00")
    sku_suffix: Optional[str] = None


class AvailabilitySchedule(BaseModel):
    """Time-based availability"""
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    end_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")


class MenuItemBase(BaseModel):
    """Base menu item model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    price: Decimal = Field(..., ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    image_url: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    is_available: bool = True
    prep_time: Optional[int] = Field(None, ge=0)  # minutes
    calories: Optional[int] = Field(None, ge=0)
    allergens: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    variants: List[MenuItemVariant] = Field(default_factory=list)
    modifiers: List[UUID] = Field(default_factory=list)  # modifier IDs
    availability_schedule: Optional[List[AvailabilitySchedule]] = None
    locations: List[UUID] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MenuItemCreate(MenuItemBase):
    """Create menu item"""
    business_id: UUID


class MenuItemUpdate(BaseModel):
    """Update menu item"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    price: Optional[Decimal] = Field(None, ge=0, )
    cost: Optional[Decimal] = Field(None, ge=0, )
    image_url: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    is_available: Optional[bool] = None
    prep_time: Optional[int] = Field(None, ge=0)
    calories: Optional[int] = Field(None, ge=0)
    allergens: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    variants: Optional[List[MenuItemVariant]] = None
    modifiers: Optional[List[UUID]] = None
    availability_schedule: Optional[List[AvailabilitySchedule]] = None
    locations: Optional[List[UUID]] = None
    metadata: Optional[Dict[str, Any]] = None


class MenuItem(MenuItemBase):
    """Menu item response model"""
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MenuItemWithDetails(MenuItem):
    """Menu item with full details including modifiers"""
    category: Optional[MenuCategory] = None
    modifier_details: List[ItemModifier] = Field(default_factory=list)
    profit_margin: Optional[Decimal] = None
    
    @validator('profit_margin', always=True)
    def calculate_profit_margin(cls, v, values):
        if 'price' in values and 'cost' in values and values['cost']:
            price = values['price']
            cost = values['cost']
            if price > 0:
                return ((price - cost) / price * 100).quantize(Decimal('0.01'))
        return None


class BulkMenuItemUpdate(BaseModel):
    """Bulk update menu items"""
    item_ids: List[UUID]
    updates: MenuItemUpdate


class MenuItemSearch(BaseModel):
    """Search menu items"""
    query: Optional[str] = None
    category_id: Optional[UUID] = None
    is_available: Optional[bool] = None
    tags: Optional[List[str]] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class MenuImport(BaseModel):
    """Import menu from external source"""
    source: str = Field(..., pattern=r"^(pdf|csv|json|toast|doordash)$")
    data: Dict[str, Any]
    business_id: UUID
    auto_create_categories: bool = True
    overwrite_existing: bool = False
