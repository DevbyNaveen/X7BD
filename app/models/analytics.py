"""
Analytics Models
Enterprise-grade data models for menu analytics and performance metrics
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# ============================================================================
# MENU ANALYTICS OVERVIEW MODELS
# ============================================================================

class MenuAnalyticsOverview(BaseModel):
    """Menu analytics overview with key metrics and trends"""
    business_id: str
    period: str
    total_menu_items: int
    popular_items: int
    average_rating: float
    total_categories: int
    items_growth: float
    rating_growth: float
    categories_growth: float
    popularity_growth: float
    performance_score: float
    last_updated: datetime
    trends_included: bool = True


# ============================================================================
# MENU ITEM PERFORMANCE MODELS
# ============================================================================

class MenuItemPerformance(BaseModel):
    """Individual menu item performance metrics"""
    item_id: str
    name: str
    category_name: str
    price: float
    cost: float
    sales_count: int
    total_quantity: int
    total_revenue: float
    total_cost: float
    profit_margin: float
    margin_percentage: float
    image_url: Optional[str] = None
    is_available: bool = True
    tags: List[str] = Field(default_factory=list)


class TopMenuItemsResponse(BaseModel):
    """Response model for top menu items analytics"""
    business_id: str
    period: str
    sort_by: str
    total_items: int
    items: List[MenuItemPerformance]
    generated_at: datetime


# ============================================================================
# CATEGORY PERFORMANCE MODELS
# ============================================================================

class CategoryPerformance(BaseModel):
    """Category performance metrics"""
    category_id: str
    category_name: str
    total_items: int
    available_items: int
    avg_price: float
    avg_cost: float
    avg_profit_margin: float
    profit_margin_percentage: float
    total_sales: int
    total_revenue: float
    total_profit: float
    performance_score: float
    growth_percentage: float
    description: Optional[str] = None
    is_active: bool = True


class CategoryPerformanceResponse(BaseModel):
    """Response model for category performance analytics"""
    business_id: str
    period: str
    total_categories: int
    categories: List[CategoryPerformance]
    include_details: bool = True
    generated_at: datetime


# ============================================================================
# PROFIT MARGIN ANALYSIS MODELS
# ============================================================================

class ProfitMarginAnalysis(BaseModel):
    """Individual item profit margin analysis"""
    item_id: str
    name: str
    price: float
    cost: float
    profit_margin: float
    margin_percentage: float
    category_id: Optional[str] = None
    is_available: bool = True


class ProfitMarginRecommendation(BaseModel):
    """Profit margin optimization recommendation"""
    type: str  # pricing, cost_tracking, overall_margin, opportunity
    priority: str  # high, medium, low
    title: str
    message: str
    affected_items: List[str]
    action: str


class ProfitMarginResponse(BaseModel):
    """Response model for profit margin analysis"""
    business_id: str
    total_items: int
    items_with_cost: int
    items_without_cost: int
    overall_analysis: Dict[str, Any]
    high_margin_items: List[Dict[str, Any]]
    low_margin_items: List[Dict[str, Any]]
    medium_margin_items: List[Dict[str, Any]]
    margin_distribution: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    analysis_date: datetime


# ============================================================================
# COMPREHENSIVE ANALYTICS RESPONSE MODELS
# ============================================================================

class MenuAnalyticsResponse(BaseModel):
    """Comprehensive menu analytics dashboard response"""
    business_id: str
    period: str
    overview: MenuAnalyticsOverview
    top_items: TopMenuItemsResponse
    category_performance: CategoryPerformanceResponse
    profit_margins: ProfitMarginResponse
    generated_at: datetime
    cache_expires_at: datetime


# ============================================================================
# ANALYTICS FILTER MODELS
# ============================================================================

class AnalyticsFilter(BaseModel):
    """Analytics filtering options"""
    period: str = Field(default="7d", pattern=r"^(1d|7d|30d|90d)$")
    business_id: UUID
    include_trends: bool = True
    include_details: bool = True
    include_recommendations: bool = True
    margin_threshold_high: float = Field(default=70.0, ge=0, le=100)
    margin_threshold_low: float = Field(default=30.0, ge=0, le=100)
    sort_by: str = Field(default="revenue", pattern=r"^(sales|revenue|margin)$")
    limit: int = Field(default=10, ge=1, le=50)


# ============================================================================
# ANALYTICS EXPORT MODELS
# ============================================================================

class AnalyticsExportRequest(BaseModel):
    """Request model for analytics data export"""
    business_id: UUID
    export_format: str = Field(default="json", pattern=r"^(json|csv|pdf)$")
    period: str = Field(default="7d", pattern=r"^(1d|7d|30d|90d)$")
    include_charts: bool = True
    include_recommendations: bool = True


class AnalyticsExportResponse(BaseModel):
    """Response model for analytics export"""
    export_id: str
    business_id: str
    export_format: str
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    generated_at: datetime
    expires_at: datetime


# ============================================================================
# REVENUE ANALYTICS MODELS
# ============================================================================

class RevenueOverview(BaseModel):
    """Revenue analytics overview with key metrics and trends"""
    business_id: str
    period: str
    total_revenue: float
    daily_revenue: float
    weekly_revenue: float
    monthly_revenue: float
    revenue_growth: float
    daily_growth: float
    weekly_growth: float
    monthly_growth: float
    average_order_value: float
    revenue_per_customer: float
    total_orders: int
    total_customers: int
    last_updated: datetime
    trends_included: bool = True


class RevenueTrendData(BaseModel):
    """Daily revenue trend data point"""
    day: str
    revenue: float
    orders: int


class RevenueByChannel(BaseModel):
    """Revenue distribution by channel"""
    channel: str
    revenue: float
    percentage: float


class RevenueByHour(BaseModel):
    """Revenue distribution by hour"""
    hour: str
    revenue: float
    orders: int


class PaymentMethodData(BaseModel):
    """Revenue distribution by payment method"""
    method: str
    revenue: float
    percentage: float


class RevenueByCategory(BaseModel):
    """Revenue distribution by category"""
    category: str
    revenue: float
    percentage: float


class TopRevenueItem(BaseModel):
    """Top revenue-generating item"""
    name: str
    revenue: float
    orders: int


class RevenueProjection(BaseModel):
    """Revenue projection data point"""
    month: str
    actual: float
    projected: float


# Revenue Analytics Response Models
class RevenueTrendResponse(BaseModel):
    """Revenue trend response"""
    business_id: str
    period: str
    trend_data: List[RevenueTrendData]
    generated_at: datetime


class RevenueByChannelResponse(BaseModel):
    """Revenue by channel response"""
    business_id: str
    period: str
    channel_data: List[RevenueByChannel]
    total_revenue: float
    generated_at: datetime


class RevenueByHourResponse(BaseModel):
    """Revenue by hour response"""
    business_id: str
    period: str
    hour_data: List[RevenueByHour]
    peak_hour: str
    peak_hour_revenue: float
    generated_at: datetime


class PaymentMethodsResponse(BaseModel):
    """Payment methods revenue response"""
    business_id: str
    period: str
    payment_data: List[PaymentMethodData]
    total_revenue: float
    generated_at: datetime


class RevenueByCategoryResponse(BaseModel):
    """Revenue by category response"""
    business_id: str
    period: str
    category_data: List[RevenueByCategory]
    total_revenue: float
    generated_at: datetime


class TopRevenueItemsResponse(BaseModel):
    """Top revenue items response"""
    business_id: str
    period: str
    top_items: List[TopRevenueItem]
    generated_at: datetime


class RevenueProjectionResponse(BaseModel):
    """Revenue projection response"""
    business_id: str
    months: int
    projection_data: List[RevenueProjection]
    avg_growth_rate: float
    generated_at: datetime


class RevenueAnalyticsResponse(BaseModel):
    """Comprehensive revenue analytics dashboard response"""
    business_id: str
    period: str
    overview: RevenueOverview
    trend_data: RevenueTrendResponse
    channel_data: RevenueByChannelResponse
    hour_data: RevenueByHourResponse
    payment_methods: PaymentMethodsResponse
    category_data: RevenueByCategoryResponse
    top_items: TopRevenueItemsResponse
    projection_data: RevenueProjectionResponse
    generated_at: datetime
    cache_expires_at: datetime


# ============================================================================
# ORDERS ANALYTICS MODELS
# ============================================================================

class OrdersOverview(BaseModel):
    """Orders analytics overview with key metrics"""
    business_id: str
    period: str
    total_orders: int
    completed_orders: int
    pending_orders: int
    cancelled_orders: int
    total_revenue: float
    average_order_value: float
    orders_growth: float
    revenue_growth: float
    completion_rate: float
    cancellation_rate: float
    last_updated: datetime


class OrderTrendData(BaseModel):
    """Daily order trend data"""
    day: str
    orders: int
    revenue: float


class OrderHourData(BaseModel):
    """Hourly order data"""
    hour: str
    orders: int


class OrderStatusData(BaseModel):
    """Order status distribution data"""
    status: str
    count: int
    percentage: float


class OrderTypeData(BaseModel):
    """Order type distribution data"""
    type: str
    count: int
    percentage: float


class TopSellingItem(BaseModel):
    """Top selling menu item"""
    name: str
    quantity: int
    revenue: float


class OrdersTrendResponse(BaseModel):
    """Response model for orders trend analytics"""
    business_id: str
    period: str
    trend_data: List[OrderTrendData]
    generated_at: datetime


class OrdersByHourResponse(BaseModel):
    """Response model for orders by hour analytics"""
    business_id: str
    period: str
    hour_data: List[OrderHourData]
    peak_hour: str
    generated_at: datetime


class OrderStatusDistributionResponse(BaseModel):
    """Response model for order status distribution"""
    business_id: str
    period: str
    status_data: List[OrderStatusData]
    generated_at: datetime


class OrderTypesResponse(BaseModel):
    """Response model for order types distribution"""
    business_id: str
    period: str
    type_data: List[OrderTypeData]
    generated_at: datetime


class TopSellingItemsResponse(BaseModel):
    """Response model for top selling items"""
    business_id: str
    period: str
    top_items: List[TopSellingItem]
    generated_at: datetime


class OrdersAnalyticsResponse(BaseModel):
    """Comprehensive orders analytics dashboard response"""
    business_id: str
    period: str
    overview: OrdersOverview
    trend_data: OrdersTrendResponse
    status_distribution: OrderStatusDistributionResponse
    hour_data: OrdersByHourResponse
    order_types: OrderTypesResponse
    top_items: TopSellingItemsResponse
    generated_at: datetime
    cache_expires_at: datetime


# ============================================================================
# REAL-TIME ANALYTICS MODELS
# ============================================================================

class AnalyticsUpdateEvent(BaseModel):
    """Real-time analytics update event"""
    event_type: str  # analytics_refreshed, data_updated, cache_invalidated
    business_id: str
    timestamp: datetime
    data_type: Optional[str] = None  # overview, top_items, categories, margins
    force_refresh: bool = False


class AnalyticsCacheStatus(BaseModel):
    """Analytics cache status"""
    business_id: str
    cache_key: str
    is_cached: bool
    cached_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    data_size: Optional[int] = None
