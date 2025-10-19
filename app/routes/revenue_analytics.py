"""
Revenue Analytics API Routes
Enterprise-grade endpoints for comprehensive revenue tracking and analysis

ENTERPRISE STRUCTURE:
- Revenue-specific analytics endpoints prefixed with /api/v1/analytics/revenue
- Comprehensive revenue tracking across all business types
- Real-time data processing and financial insights
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
import json

from ..models.analytics import (
    # Revenue Analytics Models
    RevenueOverview, RevenueTrendData, RevenueByChannel, RevenueByHour,
    PaymentMethodData, RevenueByCategory, TopRevenueItem, RevenueProjection,
    RevenueAnalyticsResponse, RevenueTrendResponse,
    RevenueByChannelResponse, RevenueByHourResponse, PaymentMethodsResponse,
    RevenueByCategoryResponse, TopRevenueItemsResponse, RevenueProjectionResponse
)
from ..services.database import get_database_service
from ..services.realtime import RealtimeEventPublisher

router = APIRouter(prefix="/api/v1/analytics/revenue", tags=["Revenue Analytics"])


# ============================================================================
# REVENUE ANALYTICS OVERVIEW
# ============================================================================

@router.get("/overview/{business_id}", response_model=RevenueOverview)
async def get_revenue_overview(
    business_id: UUID,
    period: str = Query("7d", pattern=r"^(1d|7d|30d|90d|1y)$"),
    include_trends: bool = Query(True)
):
    """
    Get comprehensive revenue analytics overview
    
    - **Key Metrics**: Total revenue, daily/weekly/monthly revenue
    - **Growth Trends**: Period-over-period growth calculations
    - **Performance Indicators**: Revenue per customer, average order value
    """
    try:
        db = get_database_service()
        
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get orders data for detailed analysis
        orders_result = db.client.table("orders").select("*").eq("business_id", str(business_id)).gte("created_at", start_date.isoformat()).execute()
        orders = orders_result.data if orders_result.data else []
        
        # Calculate revenue directly from orders (same logic as Revenue by Channel)
        total_revenue = sum(float(order.get("total_amount", 0)) for order in orders)
        
        # Calculate daily revenue (last day)
        today = end_date.date()
        daily_revenue = 0.0
        for order in orders:
            try:
                order_date = datetime.fromisoformat(order.get("created_at", "")).date()
                if order_date == today:
                    daily_revenue += float(order.get("total_amount", 0))
            except:
                continue
        
        # Calculate weekly revenue (last 7 days)
        weekly_start = end_date - timedelta(days=7)
        weekly_revenue = 0.0
        for order in orders:
            try:
                order_date = datetime.fromisoformat(order.get("created_at", "")).date()
                if order_date >= weekly_start.date():
                    weekly_revenue += float(order.get("total_amount", 0))
            except:
                continue
        
        # Calculate monthly revenue (last 30 days)
        monthly_start = end_date - timedelta(days=30)
        monthly_revenue = 0.0
        for order in orders:
            try:
                order_date = datetime.fromisoformat(order.get("created_at", "")).date()
                if order_date >= monthly_start.date():
                    monthly_revenue += float(order.get("total_amount", 0))
            except:
                continue
        
        # Calculate growth trends by comparing with previous period
        previous_start_date = start_date - (end_date - start_date)
        previous_orders_result = db.client.table("orders").select("*").eq("business_id", str(business_id)).gte("created_at", previous_start_date.isoformat()).lt("created_at", start_date.isoformat()).execute()
        previous_orders = previous_orders_result.data if previous_orders_result.data else []
        
        previous_total_revenue = sum(float(order.get("total_amount", 0)) for order in previous_orders)
        
        # Calculate growth percentages
        if previous_total_revenue > 0:
            revenue_growth = ((total_revenue - previous_total_revenue) / previous_total_revenue * 100)
        else:
            revenue_growth = 100.0 if total_revenue > 0 else 0.0
        
        # Calculate additional metrics from orders
        total_orders = len(orders)
        
        # Count unique customers
        unique_customers = set()
        for order in orders:
            customer_id = order.get("customer_id")
            if customer_id:
                unique_customers.add(customer_id)
        total_customers = len(unique_customers)
        
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        revenue_per_customer = total_revenue / total_customers if total_customers > 0 else 0
        
        # Calculate daily growth
        yesterday = end_date - timedelta(days=1)
        yesterday_revenue = 0.0
        for order in orders:
            try:
                order_date = datetime.fromisoformat(order.get("created_at", "")).date()
                if order_date == yesterday.date():
                    yesterday_revenue += float(order.get("total_amount", 0))
            except:
                continue
        
        daily_growth = ((daily_revenue - yesterday_revenue) / yesterday_revenue * 100) if yesterday_revenue > 0 else 0.0
        
        # Calculate weekly growth
        previous_week_start = weekly_start - timedelta(days=7)
        previous_week_revenue = 0.0
        for order in previous_orders:
            try:
                order_date = datetime.fromisoformat(order.get("created_at", "")).date()
                if order_date >= previous_week_start.date() and order_date < weekly_start.date():
                    previous_week_revenue += float(order.get("total_amount", 0))
            except:
                continue
        
        weekly_growth = ((weekly_revenue - previous_week_revenue) / previous_week_revenue * 100) if previous_week_revenue > 0 else 0.0
        
        # Calculate monthly growth
        previous_month_start = monthly_start - timedelta(days=30)
        previous_month_revenue = 0.0
        for order in previous_orders:
            try:
                order_date = datetime.fromisoformat(order.get("created_at", "")).date()
                if order_date >= previous_month_start.date() and order_date < monthly_start.date():
                    previous_month_revenue += float(order.get("total_amount", 0))
            except:
                continue
        
        monthly_growth = ((monthly_revenue - previous_month_revenue) / previous_month_revenue * 100) if previous_month_revenue > 0 else 0.0
        
        return RevenueOverview(
            business_id=str(business_id),
            period=period,
            total_revenue=round(total_revenue, 2),
            daily_revenue=round(daily_revenue, 2),
            weekly_revenue=round(weekly_revenue, 2),
            monthly_revenue=round(monthly_revenue, 2),
            revenue_growth=round(revenue_growth, 1),
            daily_growth=round(daily_growth, 1),
            weekly_growth=round(weekly_growth, 1),
            monthly_growth=round(monthly_growth, 1),
            average_order_value=round(average_order_value, 2),
            revenue_per_customer=round(revenue_per_customer, 2),
            total_orders=total_orders,
            total_customers=total_customers,
            last_updated=datetime.utcnow(),
            trends_included=include_trends
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get revenue overview: {str(e)}")


# ============================================================================
# REVENUE TREND ANALYSIS
# ============================================================================

@router.get("/trend/{business_id}", response_model=RevenueTrendResponse)
async def get_revenue_trend(
    business_id: UUID,
    period: str = Query("7d", pattern=r"^(1d|7d|30d|90d|1y)$")
):
    """
    Get daily revenue trend data for charts
    
    - **Daily Volume**: Revenue by day with order counts
    - **Chart Data**: Formatted for line/bar charts
    - **Time Period**: Configurable date ranges
    """
    try:
        db = get_database_service()
        
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get daily sales summary data
        sales_summary_result = db.client.table("daily_sales_summary").select("*").eq("business_id", str(business_id)).gte("date", start_date.date().isoformat()).execute()
        sales_summary = sales_summary_result.data if sales_summary_result.data else []
        
        # Create lookup for sales data
        sales_lookup = {}
        for sale in sales_summary:
            date_str = sale.get("date")
            if date_str:
                sales_lookup[date_str] = {
                    "revenue": float(sale.get("total_sales", 0)),
                    "orders": sale.get("total_orders", 0)
                }
        
        # Generate trend data with day names
        trend_data = []
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        # For periods longer than 7 days, show weekly aggregates
        if period in ["30d", "90d", "1y"]:
            # Group by week
            weekly_data = {}
            for sale in sales_summary:
                date_str = sale.get("date")
                if date_str:
                    date_obj = datetime.fromisoformat(date_str).date()
                    week_start = date_obj - timedelta(days=date_obj.weekday())
                    week_key = week_start.isoformat()
                    
                    if week_key not in weekly_data:
                        weekly_data[week_key] = {"revenue": 0.0, "orders": 0}
                    
                    weekly_data[week_key]["revenue"] += float(sale.get("total_sales", 0))
                    weekly_data[week_key]["orders"] += sale.get("total_orders", 0)
            
            # Convert to trend data
            for week_key in sorted(weekly_data.keys()):
                week_start = datetime.fromisoformat(week_key).date()
                week_end = week_start + timedelta(days=6)
                week_label = f"{week_start.strftime('%m/%d')}-{week_end.strftime('%m/%d')}"
                
                trend_data.append(RevenueTrendData(
                    day=week_label,
                    revenue=round(weekly_data[week_key]["revenue"], 2),
                    orders=weekly_data[week_key]["orders"]
                ))
        else:
            # Daily data for shorter periods
            for i in range(7 if period == "7d" else 1):
                date = (end_date - timedelta(days=i)).date()
                day_key = date.isoformat()
                day_name = days[date.weekday()]
                
                revenue = sales_lookup.get(day_key, {}).get("revenue", 0.0)
                orders = sales_lookup.get(day_key, {}).get("orders", 0)
                
                trend_data.append(RevenueTrendData(
                    day=day_name,
                    revenue=round(revenue, 2),
                    orders=orders
                ))
        
        # Reverse to get chronological order
        trend_data.reverse()
        
        return RevenueTrendResponse(
            business_id=str(business_id),
            period=period,
            trend_data=trend_data,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get revenue trend: {str(e)}")


# ============================================================================
# REVENUE BY CHANNEL ANALYSIS
# ============================================================================

@router.get("/by-channel/{business_id}", response_model=RevenueByChannelResponse)
async def get_revenue_by_channel(
    business_id: UUID,
    period: str = Query("7d", pattern=r"^(1d|7d|30d|90d|1y)$")
):
    """
    Get revenue distribution by channel (dine-in, takeout, delivery)
    
    - **Channel Breakdown**: Revenue and percentage by channel
    - **Chart Data**: Formatted for pie charts
    - **Performance**: Channel performance comparison
    """
    try:
        db = get_database_service()
        
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get orders data
        orders_result = db.client.table("orders").select("*").eq("business_id", str(business_id)).gte("created_at", start_date.isoformat()).execute()
        orders = orders_result.data if orders_result.data else []
        
        # Calculate revenue by channel
        channel_revenue = {"Dine-in": 0.0, "Takeout": 0.0, "Delivery": 0.0}
        
        for order in orders:
            order_amount = float(order.get("total_amount", 0))
            
            # Determine channel based on order characteristics
            if order.get("table_id"):
                # Has table_id = dine-in
                channel_revenue["Dine-in"] += order_amount
            elif order.get("delivery_address") or order.get("order_type") == "delivery":
                # Has delivery info = delivery
                channel_revenue["Delivery"] += order_amount
            else:
                # Default to takeout
                channel_revenue["Takeout"] += order_amount
        
        # Calculate total revenue and percentages
        total_revenue = sum(channel_revenue.values())
        
        channel_data = []
        for channel, revenue in channel_revenue.items():
            percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            channel_data.append(RevenueByChannel(
                channel=channel,
                revenue=round(revenue, 2),
                percentage=round(percentage, 1)
            ))
        
        # Sort by revenue (descending)
        channel_data.sort(key=lambda x: x.revenue, reverse=True)
        
        return RevenueByChannelResponse(
            business_id=str(business_id),
            period=period,
            channel_data=channel_data,
            total_revenue=round(total_revenue, 2),
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get revenue by channel: {str(e)}")


# ============================================================================
# REVENUE BY HOUR ANALYSIS
# ============================================================================

@router.get("/by-hour/{business_id}", response_model=RevenueByHourResponse)
async def get_revenue_by_hour(
    business_id: UUID,
    period: str = Query("7d", pattern=r"^(1d|7d|30d|90d|1y)$")
):
    """
    Get revenue distribution by hour for peak time analysis
    
    - **Hourly Distribution**: Revenue by hour of day
    - **Peak Hours**: Identify highest revenue times
    - **Chart Data**: Formatted for bar charts
    """
    try:
        db = get_database_service()
        
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get orders data
        orders_result = db.client.table("orders").select("*").eq("business_id", str(business_id)).gte("created_at", start_date.isoformat()).execute()
        orders = orders_result.data if orders_result.data else []
        
        # Group revenue by time ranges
        hourly_revenue = {}
        for order in orders:
            try:
                # Handle different datetime formats from Supabase
                created_at = order["created_at"]
                
                # Normalize the datetime string
                if created_at.endswith('Z'):
                    created_at = created_at[:-1] + '+00:00'
                
                # Fix microseconds format (ensure 6 digits)
                if '.' in created_at and '+' in created_at:
                    # Split by timezone
                    dt_part, tz_part = created_at.rsplit('+', 1)
                    if '.' in dt_part:
                        date_part, micro_part = dt_part.split('.')
                        # Pad microseconds to 6 digits
                        micro_part = micro_part.ljust(6, '0')[:6]
                        created_at = f"{date_part}.{micro_part}+{tz_part}"
                
                # Parse the datetime
                order_time = datetime.fromisoformat(created_at)
                hour = order_time.hour
                order_amount = float(order.get("total_amount", 0))
                
                # Map hour to time range
                if 6 <= hour < 9:
                    time_range = "6AM"
                elif 9 <= hour < 12:
                    time_range = "9AM"
                elif 12 <= hour < 15:
                    time_range = "12PM"
                elif 15 <= hour < 18:
                    time_range = "3PM"
                elif 18 <= hour < 21:
                    time_range = "6PM"
                elif 21 <= hour < 24 or 0 <= hour < 6:
                    time_range = "9PM"
                else:
                    time_range = "Other"
                
                if time_range not in hourly_revenue:
                    hourly_revenue[time_range] = {"revenue": 0.0, "orders": 0}
                
                hourly_revenue[time_range]["revenue"] += order_amount
                hourly_revenue[time_range]["orders"] += 1
                
            except ValueError as e:
                # Skip orders with invalid datetime formats
                print(f"Warning: Skipping order with invalid datetime format: {order.get('created_at')} - {e}")
                continue
        
        # Generate hour data with formatted labels
        time_ranges = ["6AM", "9AM", "12PM", "3PM", "6PM", "9PM"]
        
        hour_data = []
        peak_hour_revenue = 0.0
        peak_hour_label = "6PM"
        
        for time_range in time_ranges:
            revenue = hourly_revenue.get(time_range, {}).get("revenue", 0.0)
            orders = hourly_revenue.get(time_range, {}).get("orders", 0)
            
            hour_data.append(RevenueByHour(
                hour=time_range,
                revenue=round(revenue, 2),
                orders=orders
            ))
            
            if revenue > peak_hour_revenue:
                peak_hour_revenue = revenue
                peak_hour_label = time_range
        
        return RevenueByHourResponse(
            business_id=str(business_id),
            period=period,
            hour_data=hour_data,
            peak_hour=peak_hour_label,
            peak_hour_revenue=round(peak_hour_revenue, 2),
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get revenue by hour: {str(e)}")


# ============================================================================
# PAYMENT METHODS ANALYSIS
# ============================================================================

@router.get("/payment-methods/{business_id}", response_model=PaymentMethodsResponse)
async def get_payment_methods_revenue(
    business_id: UUID,
    period: str = Query("7d", pattern=r"^(1d|7d|30d|90d|1y)$")
):
    """
    Get revenue distribution by payment methods
    
    - **Payment Types**: Credit Card, Cash, Mobile Pay, etc.
    - **Distribution**: Revenue and percentage breakdown
    - **Chart Data**: Formatted for pie charts
    """
    try:
        db = get_database_service()
        
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get orders data
        orders_result = db.client.table("orders").select("*").eq("business_id", str(business_id)).gte("created_at", start_date.isoformat()).execute()
        orders = orders_result.data if orders_result.data else []
        
        # Calculate revenue by payment method
        payment_revenue = {}
        
        for order in orders:
            order_amount = float(order.get("total_amount", 0))
            payment_method = order.get("payment_method", "Cash")  # Default to Cash if not specified
            
            # Normalize payment method names
            if payment_method.lower() in ["card", "credit_card", "credit card"]:
                payment_method = "Credit Card"
            elif payment_method.lower() in ["mobile", "mobile_pay", "mobile pay", "apple_pay", "google_pay"]:
                payment_method = "Mobile Pay"
            elif payment_method.lower() in ["cash"]:
                payment_method = "Cash"
            else:
                payment_method = "Other"
            
            if payment_method not in payment_revenue:
                payment_revenue[payment_method] = 0.0
            
            payment_revenue[payment_method] += order_amount
        
        # Calculate total revenue and percentages
        total_revenue = sum(payment_revenue.values())
        
        payment_data = []
        for method, revenue in payment_revenue.items():
            percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            payment_data.append(PaymentMethodData(
                method=method,
                revenue=round(revenue, 2),
                percentage=round(percentage, 1)
            ))
        
        # Sort by revenue (descending)
        payment_data.sort(key=lambda x: x.revenue, reverse=True)
        
        return PaymentMethodsResponse(
            business_id=str(business_id),
            period=period,
            payment_data=payment_data,
            total_revenue=round(total_revenue, 2),
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment methods revenue: {str(e)}")


# ============================================================================
# REVENUE BY CATEGORY ANALYSIS
# ============================================================================

@router.get("/by-category/{business_id}", response_model=RevenueByCategoryResponse)
async def get_revenue_by_category(
    business_id: UUID,
    period: str = Query("7d", pattern=r"^(1d|7d|30d|90d|1y)$")
):
    """
    Get revenue distribution by menu categories
    
    - **Category Breakdown**: Revenue and percentage by category
    - **Performance**: Category performance comparison
    - **Chart Data**: Formatted for bar charts
    """
    try:
        db = get_database_service()
        
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get item performance data
        item_performance_result = db.client.table("item_performance").select("*").eq("business_id", str(business_id)).gte("date", start_date.date().isoformat()).execute()
        item_performance = item_performance_result.data if item_performance_result.data else []
        
        # Get menu items for category mapping
        menu_items_result = db.client.table("menu_items").select("*").eq("business_id", str(business_id)).execute()
        menu_items = menu_items_result.data if menu_items_result.data else []
        
        # Get categories
        categories_result = db.client.table("menu_categories").select("*").eq("business_id", str(business_id)).execute()
        categories = {cat["id"]: cat["name"] for cat in categories_result.data} if categories_result.data else {}
        
        # Create item to category mapping
        item_to_category = {item["id"]: item.get("category_id") for item in menu_items}
        
        # Calculate revenue by category
        category_revenue = {}
        
        for perf in item_performance:
            item_id = perf.get("menu_item_id")
            if item_id and item_id in item_to_category:
                category_id = item_to_category[item_id]
                category_name = categories.get(category_id, "Uncategorized")
                revenue = float(perf.get("revenue", 0))
                
                if category_name not in category_revenue:
                    category_revenue[category_name] = 0.0
                
                category_revenue[category_name] += revenue
        
        # Calculate total revenue and percentages
        total_revenue = sum(category_revenue.values())
        
        category_data = []
        for category, revenue in category_revenue.items():
            percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            category_data.append(RevenueByCategory(
                category=category,
                revenue=round(revenue, 2),
                percentage=round(percentage, 1)
            ))
        
        # Sort by revenue (descending)
        category_data.sort(key=lambda x: x.revenue, reverse=True)
        
        return RevenueByCategoryResponse(
            business_id=str(business_id),
            period=period,
            category_data=category_data,
            total_revenue=round(total_revenue, 2),
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get revenue by category: {str(e)}")


# ============================================================================
# TOP REVENUE ITEMS ANALYSIS
# ============================================================================

@router.get("/top-items/{business_id}", response_model=TopRevenueItemsResponse)
async def get_top_revenue_items(
    business_id: UUID,
    period: str = Query("7d", pattern=r"^(1d|7d|30d|90d|1y)$"),
    limit: int = Query(5, ge=1, le=20)
):
    """
    Get top revenue-generating menu items
    
    - **Top Items**: Highest revenue menu items
    - **Metrics**: Revenue and order counts
    - **Ranking**: Sorted by revenue generated
    """
    try:
        db = get_database_service()
        
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get item performance data
        item_performance_result = db.client.table("item_performance").select("*").eq("business_id", str(business_id)).gte("date", start_date.date().isoformat()).execute()
        item_performance = item_performance_result.data if item_performance_result.data else []
        
        # Get menu items for name lookup
        menu_items_result = db.client.table("menu_items").select("*").eq("business_id", str(business_id)).execute()
        menu_items = {item["id"]: item for item in menu_items_result.data} if menu_items_result.data else {}
        
        # Aggregate revenue by item
        item_revenue = {}
        
        for perf in item_performance:
            item_id = perf.get("menu_item_id")
            if item_id and item_id in menu_items:
                item_name = menu_items[item_id]["name"]
                revenue = float(perf.get("revenue", 0))
                orders = perf.get("quantity_sold", 0)
                
                if item_name not in item_revenue:
                    item_revenue[item_name] = {"revenue": 0.0, "orders": 0}
                
                item_revenue[item_name]["revenue"] += revenue
                item_revenue[item_name]["orders"] += orders
        
        # Convert to top items list and sort by revenue
        top_items = []
        for name, data in item_revenue.items():
            top_items.append(TopRevenueItem(
                name=name,
                revenue=round(data["revenue"], 2),
                orders=data["orders"]
            ))
        
        # Sort by revenue and limit results
        top_items.sort(key=lambda x: x.revenue, reverse=True)
        top_items = top_items[:limit]
        
        return TopRevenueItemsResponse(
            business_id=str(business_id),
            period=period,
            top_items=top_items,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get top revenue items: {str(e)}")


# ============================================================================
# REVENUE PROJECTION ANALYSIS
# ============================================================================

@router.get("/projection/{business_id}", response_model=RevenueProjectionResponse)
async def get_revenue_projection(
    business_id: UUID,
    months: int = Query(6, ge=1, le=12)
):
    """
    Get revenue projection based on historical data
    
    - **Historical Data**: Past revenue trends
    - **Projections**: Future revenue estimates
    - **Chart Data**: Formatted for line charts
    """
    try:
        db = get_database_service()
        
        # Get historical data for the past months
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months * 30)
        
        # Get daily sales summary data
        sales_summary_result = db.client.table("daily_sales_summary").select("*").eq("business_id", str(business_id)).gte("date", start_date.date().isoformat()).execute()
        sales_summary = sales_summary_result.data if sales_summary_result.data else []
        
        # Group by month
        monthly_revenue = {}
        for sale in sales_summary:
            date_str = sale.get("date")
            if date_str:
                date_obj = datetime.fromisoformat(date_str).date()
                month_key = date_obj.strftime("%Y-%m")
                
                if month_key not in monthly_revenue:
                    monthly_revenue[month_key] = 0.0
                
                monthly_revenue[month_key] += float(sale.get("total_sales", 0))
        
        # Generate projection data
        projection_data = []
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        # Calculate average monthly growth
        monthly_values = list(monthly_revenue.values())
        if len(monthly_values) >= 2:
            # Calculate average growth rate
            growth_rates = []
            for i in range(1, len(monthly_values)):
                if monthly_values[i-1] > 0:
                    growth_rate = (monthly_values[i] - monthly_values[i-1]) / monthly_values[i-1]
                    growth_rates.append(growth_rate)
            
            avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0.0
        else:
            avg_growth_rate = 0.0
        
        # Generate data for the requested months
        current_date = start_date
        for i in range(months):
            month_key = current_date.strftime("%Y-%m")
            month_name = month_names[current_date.month - 1]
            
            actual_revenue = monthly_revenue.get(month_key, 0.0)
            
            # Calculate projected revenue for future months
            if current_date > end_date:
                # Future month - use projection
                if len(monthly_values) > 0:
                    last_month_revenue = monthly_values[-1]
                    projected_revenue = last_month_revenue * (1 + avg_growth_rate)
                else:
                    projected_revenue = 0.0
            else:
                # Past month - use actual data
                projected_revenue = actual_revenue
            
            projection_data.append(RevenueProjection(
                month=month_name,
                actual=round(actual_revenue, 2),
                projected=round(projected_revenue, 2)
            ))
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return RevenueProjectionResponse(
            business_id=str(business_id),
            months=months,
            projection_data=projection_data,
            avg_growth_rate=round(avg_growth_rate * 100, 1),
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get revenue projection: {str(e)}")


# ============================================================================
# REVENUE ANALYTICS DASHBOARD
# ============================================================================

@router.get("/dashboard/{business_id}", response_model=RevenueAnalyticsResponse)
async def get_revenue_analytics_dashboard(
    business_id: UUID,
    period: str = Query("7d", pattern=r"^(1d|7d|30d|90d|1y)$"),
    include_trends: bool = Query(True)
):
    """
    Get comprehensive revenue analytics dashboard data
    
    - **Combined Data**: Overview, trends, distributions, projections
    - **Real-time**: Latest data with caching considerations
    - **Customizable**: Configurable time periods and data inclusion
    """
    try:
        # Get all revenue analytics data in parallel
        overview = await get_revenue_overview(business_id, period, include_trends)
        trend_data = await get_revenue_trend(business_id, period)
        channel_data = await get_revenue_by_channel(business_id, period)
        hour_data = await get_revenue_by_hour(business_id, period)
        payment_methods = await get_payment_methods_revenue(business_id, period)
        category_data = await get_revenue_by_category(business_id, period)
        top_items = await get_top_revenue_items(business_id, period, 5)
        projection_data = await get_revenue_projection(business_id, 6)
        
        return RevenueAnalyticsResponse(
            business_id=str(business_id),
            period=period,
            overview=overview,
            trend_data=trend_data,
            channel_data=channel_data,
            hour_data=hour_data,
            payment_methods=payment_methods,
            category_data=category_data,
            top_items=top_items,
            projection_data=projection_data,
            generated_at=datetime.utcnow(),
            cache_expires_at=datetime.utcnow() + timedelta(minutes=5)  # 5-minute cache
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get revenue analytics dashboard: {str(e)}")


# ============================================================================
# REAL-TIME REVENUE UPDATES
# ============================================================================

@router.post("/refresh/{business_id}")
async def refresh_revenue_analytics(
    business_id: UUID,
    force_refresh: bool = Query(False)
):
    """
    Refresh revenue analytics data
    
    - **Cache Invalidation**: Clear cached analytics data
    - **Real-time Update**: Force recalculation of all metrics
    - **WebSocket Notification**: Notify frontend of data refresh
    """
    try:
        # Publish real-time update
        await RealtimeEventPublisher.publish_order_update(
            str(business_id),
            {
                "type": "revenue_analytics_refreshed",
                "business_id": str(business_id),
                "timestamp": datetime.utcnow().isoformat(),
                "force_refresh": force_refresh
            }
        )
        
        return {
            "message": "Revenue analytics refreshed successfully",
            "business_id": str(business_id),
            "timestamp": datetime.utcnow().isoformat(),
            "force_refresh": force_refresh
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh revenue analytics: {str(e)}")
