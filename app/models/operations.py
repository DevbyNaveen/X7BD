"""
Operations Management Models
Enterprise-grade data models for tables, floor plans, and kitchen operations
"""

from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, time
from decimal import Decimal
from uuid import UUID
from enum import Enum


class TableStatus(str, Enum):
    """Table statuses"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"


class KDSStatus(str, Enum):
    """Kitchen Display System statuses"""
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"


class ShiftStatus(str, Enum):
    """Staff shift statuses"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class LocationBase(BaseModel):
    """Base location model"""
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    timezone: str = Field(default="UTC", max_length=100)
    settings: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class LocationCreate(LocationBase):
    """Create location"""
    business_id: UUID


class LocationUpdate(BaseModel):
    """Update location"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=100)
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class Location(LocationBase):
    """Location response model"""
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FloorPlanBase(BaseModel):
    """Base floor plan model"""
    name: str = Field(..., min_length=1, max_length=255)
    location_id: Optional[UUID] = None
    layout: Dict[str, Any]  # SVG/canvas data
    is_active: bool = True


class FloorPlanCreate(FloorPlanBase):
    """Create floor plan"""
    business_id: UUID


class FloorPlanUpdate(BaseModel):
    """Update floor plan"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location_id: Optional[UUID] = None
    layout: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class FloorPlan(FloorPlanBase):
    """Floor plan response model"""
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TablePosition(BaseModel):
    """Table position on floor plan"""
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)
    rotation: float = Field(default=0, ge=0, lt=360)


class TableBase(BaseModel):
    """Base table model"""
    table_number: str = Field(..., min_length=1, max_length=50)
    capacity: int = Field(..., ge=1, le=50)
    location_id: Optional[UUID] = None
    floor_plan_id: Optional[UUID] = None
    position: Optional[TablePosition] = None
    shape: Optional[str] = Field(None, pattern=r"^(circle|square|rectangle|oval)$")
    status: TableStatus = TableStatus.AVAILABLE
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TableCreate(TableBase):
    """Create table"""
    business_id: UUID


class TableUpdate(BaseModel):
    """Update table"""
    table_number: Optional[str] = Field(None, min_length=1, max_length=50)
    capacity: Optional[int] = Field(None, ge=1, le=50)
    location_id: Optional[UUID] = None
    floor_plan_id: Optional[UUID] = None
    position: Optional[TablePosition] = None
    shape: Optional[str] = Field(None, pattern=r"^(circle|square|rectangle|oval)$")
    status: Optional[TableStatus] = None
    current_order_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None


class Table(TableBase):
    """Table response model"""
    id: UUID
    business_id: UUID
    current_order_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TableWithDetails(Table):
    """Table with full details"""
    location: Optional[Location] = None
    current_order: Optional[Dict[str, Any]] = None
    occupied_duration: Optional[int] = None  # minutes
    estimated_turnover: Optional[datetime] = None


class TableAssignment(BaseModel):
    """Assign table to order"""
    table_id: UUID
    order_id: UUID
    party_size: int = Field(..., ge=1)  # Change from str to int
    estimated_duration: Optional[int] = None  # minutes
    
    @validator('party_size', pre=True)
    def parse_party_size(cls, v):
        """Parse party_size from formats like '1:1' or '4'"""
        try:
            if isinstance(v, int):
                return v
                
            if ":" in str(v):
                # Format like "1:1" - take the first number
                return int(str(v).split(":")[0])
            else:
                # Format like "4" - direct integer
                return int(v)
        except (ValueError, IndexError, TypeError):
            raise ValueError("Invalid party_size format. Expected integer or format like '1:1'")

class KDSOrderItem(BaseModel):
    """Kitchen Display System order item"""
    menu_item_id: UUID
    name: str
    quantity: int = Field(..., ge=1)
    modifiers: List[str] = Field(default_factory=list)
    special_instructions: Optional[str] = None


class KDSOrderBase(BaseModel):
    """Base KDS order model"""
    order_id: UUID
    station: str = Field(..., max_length=100)  # grill, fryer, salad, bar
    items: List[KDSOrderItem]
    priority: int = Field(default=0, ge=0, le=10)
    target_time: Optional[datetime] = None


class KDSOrderCreate(KDSOrderBase):
    """Create KDS order"""
    business_id: UUID


class KDSOrderUpdate(BaseModel):
    """Update KDS order"""
    status: Optional[KDSStatus] = None
    assigned_to: Optional[UUID] = None
    prep_start_time: Optional[datetime] = None
    prep_end_time: Optional[datetime] = None


class KDSOrder(KDSOrderBase):
    """KDS order response model"""
    id: UUID
    business_id: UUID
    status: KDSStatus
    prep_start_time: Optional[datetime] = None
    prep_end_time: Optional[datetime] = None
    assigned_to: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class KDSOrderWithMetrics(KDSOrder):
    """KDS order with performance metrics"""
    prep_duration: Optional[int] = None  # minutes
    is_late: bool = False
    time_remaining: Optional[int] = None  # minutes
    
    @validator('prep_duration', always=True)
    def calculate_prep_duration(cls, v, values):
        if 'prep_start_time' in values and 'prep_end_time' in values:
            if values['prep_start_time'] and values['prep_end_time']:
                delta = values['prep_end_time'] - values['prep_start_time']
                return int(delta.total_seconds() / 60)
        return None
    
    @validator('is_late', always=True)
    def check_if_late(cls, v, values):
        if 'target_time' in values and values['target_time']:
            return datetime.utcnow() > values['target_time']
        return False


class StaffMemberBase(BaseModel):
    """Base staff member model"""
    employee_id: Optional[str] = Field(None, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    position: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    hourly_rate: Optional[Decimal] = Field(None, ge=0, )
    hire_date: Optional[datetime] = Field(None)
    status: str = Field(default="active", pattern=r"^(active|inactive|terminated)$")
    permissions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('hire_date', mode='before')
    @classmethod
    def validate_hire_date(cls, v):
        """Convert empty string to None for hire_date"""
        if v == "":
            return None
        return v


class StaffMemberCreate(StaffMemberBase):
    """Create staff member"""
    business_id: UUID
    user_id: Optional[UUID] = None


class StaffMemberUpdate(BaseModel):
    """Update staff member"""
    employee_id: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    position: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    hourly_rate: Optional[Union[str, float]] = None  # Accept both string and number
    hire_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern=r"^(active|inactive|terminated)$")
    permissions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('hire_date', mode='before')
    @classmethod
    def validate_hire_date(cls, v):
        """Convert empty string to None for hire_date"""
        if v == "":
            return None
        return v


class StaffMember(StaffMemberBase):
    """Staff member response model"""
    id: UUID
    business_id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StaffScheduleBase(BaseModel):
    """Base staff schedule model"""
    staff_id: UUID
    location_id: Optional[UUID] = None
    shift_date: datetime
    shift_start: time
    shift_end: time
    break_duration: Optional[int] = Field(None, ge=0)  # minutes
    position: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    status: ShiftStatus = ShiftStatus.SCHEDULED

    @field_validator('shift_date', mode='before')
    @classmethod
    def validate_shift_date(cls, v):
        """Convert empty string to None for shift_date"""
        if v == "":
            return None
        return v

    @field_validator('shift_start', mode='before')
    @classmethod
    def validate_shift_start(cls, v):
        """Convert empty string to None for shift_start"""
        if v == "":
            return None
        return v

    @field_validator('shift_end', mode='before')
    @classmethod
    def validate_shift_end(cls, v):
        """Convert empty string to None for shift_end"""
        if v == "":
            return None
        return v


class StaffScheduleCreate(StaffScheduleBase):
    """Create staff schedule"""
    business_id: UUID


class StaffScheduleUpdate(BaseModel):
    """Update staff schedule"""
    shift_date: Optional[datetime] = None
    shift_start: Optional[time] = None
    shift_end: Optional[time] = None
    break_duration: Optional[int] = Field(None, ge=0)
    position: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    status: Optional[ShiftStatus] = None


class StaffSchedule(StaffScheduleBase):
    """Staff schedule response model"""
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TimeClockBase(BaseModel):
    """Base time clock model"""
    staff_id: UUID
    clock_in: datetime
    location_id: Optional[UUID] = None
    notes: Optional[str] = None

    @field_validator('clock_in', mode='before')
    @classmethod
    def validate_clock_in(cls, v):
        """Convert empty string to None for clock_in"""
        if v == "":
            return None
        return v


class TimeClockCreate(TimeClockBase):
    """Clock in"""
    business_id: UUID


class TimeClockUpdate(BaseModel):
    """Clock out or update"""
    clock_out: Optional[datetime] = None
    break_start: Optional[datetime] = None
    break_end: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator('clock_out', mode='before')
    @classmethod
    def validate_clock_out(cls, v):
        """Convert empty string to None for clock_out"""
        if v == "":
            return None
        return v

    @field_validator('break_start', mode='before')
    @classmethod
    def validate_break_start(cls, v):
        """Convert empty string to None for break_start"""
        if v == "":
            return None
        return v

    @field_validator('break_end', mode='before')
    @classmethod
    def validate_break_end(cls, v):
        """Convert empty string to None for break_end"""
        if v == "":
            return None
        return v


class TimeClock(TimeClockBase):
    """Time clock response model"""
    id: UUID
    business_id: UUID
    clock_out: Optional[datetime] = None
    break_start: Optional[datetime] = None
    break_end: Optional[datetime] = None
    total_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OperationsDashboard(BaseModel):
    """Real-time operations dashboard"""
    business_id: UUID
    timestamp: datetime
    tables: Dict[str, Any]  # available, occupied, reserved counts
    kitchen: Dict[str, Any]  # pending, preparing, ready counts
    staff: Dict[str, Any]  # clocked_in, on_break counts
    orders: Dict[str, Any]  # active, completed today
    revenue_today: Decimal
    avg_table_turnover: Optional[int] = None  # minutes
    avg_prep_time: Optional[int] = None  # minutes
