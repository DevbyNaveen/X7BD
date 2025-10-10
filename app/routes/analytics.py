"""
Enhanced Analytics API Routes
Enterprise-grade analytics and reporting endpoints
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date, timedelta
from decimal import Decimal

from ..services.database import get_database_service

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


# ============================================================================
# REAL-TIME ANALYTICS
# ============================================================================

@router.get("/realtime/{business_id}", response_model=Dict[str, Any])
async def get_realtime_analytics(
    business_id: UUID,
    location_id: Optional[UUID] = Query(None)
):
    """
    Real-time business analytics dashboard
    
    - **Live metrics**: Current orders, revenue, customers
    - **Staff status**: Who's working, breaks, overtime
    - **Table status**: Available, occupied, reserved
    - **Kitchen status**: Active orders, prep times
    - **Inventory alerts**: Low stock items
    """
    try:
        db = get_database_service()
        
        # Get today's date
        today = date.today()
        
        # Get daily sales summary
        daily_sales = await db.get_daily_sales_summary(business_id, today)
        
        # Get table status
        tables = await db.get_tables(business_id, location_id, None)
        table_stats = {
            "total": len(tables),
            "available": sum(1 for t in tables if t.get("status") == "available"),
            "occupied": sum(1 for t in tables if t.get("status") == "occupied"),
            "reserved": sum(1 for t in tables if t.get("status") == "reserved")
        }
        
        # Get clocked-in staff
        clocked_in_staff = await db.get_clocked_in_staff(business_id)
        
        # Get active KDS orders
        kds_orders = await db.get_active_kds_orders(business_id, None)
        
        # Get low stock items
        low_stock = await db.get_low_stock_items(business_id)
        
        return {
            "business_id": str(business_id),
            "timestamp": datetime.utcnow().isoformat(),
            "orders": {
                "active": len(kds_orders),
                "completed_today": daily_sales.get("total_orders", 0) if daily_sales else 0,
                "pending_kitchen": sum(1 for o in kds_orders if o.get("status") == "pending"),
                "avg_prep_time": 0
            },
            "revenue": {
                "today": float(daily_sales.get("total_revenue", 0)) if daily_sales else 0.0,
                "this_hour": 0.0,
                "avg_order_value": float(daily_sales.get("avg_order_value", 0)) if daily_sales else 0.0
            },
            "tables": table_stats,
            "staff": {
                "clocked_in": len(clocked_in_staff),
                "on_break": 0,
                "total_hours_today": sum(float(s.get("total_hours", 0)) for s in clocked_in_staff)
            },
            "inventory": {
                "low_stock_items": len(low_stock),
                "out_of_stock_items": sum(1 for item in low_stock if item.get("current_stock", 0) == 0)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch real-time analytics: {str(e)}")


@router.get("/dashboard/{business_id}", response_model=Dict[str, Any])
async def get_comprehensive_dashboard(
    business_id: UUID,
    period: str = Query("7d", pattern=r"^(1d|7d|30d|90d|1y)$"),
    location_id: Optional[UUID] = Query(None)
):
    """
    Comprehensive analytics dashboard
    
    - **Sales trends**: Revenue, orders, customers over time
    - **Performance metrics**: Top items, categories, staff
    - **Operational metrics**: Table turnover, prep times
    - **Financial metrics**: Revenue, costs, profit margins
    - **Comparisons**: Period-over-period growth
    """
    try:
        db = get_database_service()
        
        # Calculate date range based on period
        end_date = date.today()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        else:  # 1y
            start_date = end_date - timedelta(days=365)
        
        # Get daily sales data
        sales_query = db.client.table("daily_sales_summary").select("*")
        sales_query = sales_query.eq("business_id", str(business_id))
        if location_id:
            sales_query = sales_query.eq("location_id", str(location_id))
        sales_query = sales_query.gte("date", start_date.isoformat())
        sales_query = sales_query.lte("date", end_date.isoformat())
        sales_query = sales_query.order("date")
        sales_result = sales_query.execute()
        
        # Calculate summary metrics
        total_revenue = sum(float(r.get("total_sales", 0)) for r in sales_result.data)
        total_orders = sum(int(r.get("total_orders", 0)) for r in sales_result.data)
        total_customers = sum(int(r.get("total_customers", 0)) for r in sales_result.data)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
        
        # Calculate growth rate (compare with previous period)
        prev_start = start_date - (end_date - start_date)
        prev_query = db.client.table("daily_sales_summary").select("total_sales")
        prev_query = prev_query.eq("business_id", str(business_id))
        prev_query = prev_query.gte("date", prev_start.isoformat())
        prev_query = prev_query.lt("date", start_date.isoformat())
        prev_result = prev_query.execute()
        prev_revenue = sum(float(r.get("total_sales", 0)) for r in prev_result.data)
        growth_rate = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0.0
        
        # Build trends data
        trends = {
            "revenue": [{"date": r["date"], "value": float(r.get("total_sales", 0))} for r in sales_result.data],
            "orders": [{"date": r["date"], "value": int(r.get("total_orders", 0))} for r in sales_result.data],
            "customers": [{"date": r["date"], "value": int(r.get("total_customers", 0))} for r in sales_result.data]
        }
        
        # Get top performing items
        top_items = await db.get_top_menu_items(business_id, start_date, end_date, 5)
        
        # Get operational metrics
        kds_query = db.client.table("kds_orders").select("prep_start_time, prep_end_time")
        kds_query = kds_query.eq("business_id", str(business_id))
        kds_query = kds_query.gte("created_at", start_date.isoformat())
        kds_query = kds_query.not_.is_("prep_start_time", "null")
        kds_query = kds_query.not_.is_("prep_end_time", "null")
        kds_result = kds_query.execute()
        
        prep_times = []
        for order in kds_result.data:
            if order.get("prep_start_time") and order.get("prep_end_time"):
                start = datetime.fromisoformat(order["prep_start_time"].replace('Z', '+00:00'))
                end = datetime.fromisoformat(order["prep_end_time"].replace('Z', '+00:00'))
                prep_times.append((end - start).total_seconds() / 60)
        
        avg_prep_time = sum(prep_times) / len(prep_times) if prep_times else 0
        
        return {
            "business_id": str(business_id),
            "period": period,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "total_orders": total_orders,
                "total_customers": total_customers,
                "avg_order_value": round(avg_order_value, 2),
                "growth_rate": round(growth_rate, 2)
            },
            "trends": trends,
            "top_performers": {
                "items": top_items[:5],
                "categories": [],
                "staff": []
            },
            "operational": {
                "avg_table_turnover": 0,
                "avg_prep_time": round(avg_prep_time, 2),
                "peak_hours": []
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard: {str(e)}")


# ============================================================================
# SALES ANALYTICS
# ============================================================================

@router.get("/sales/summary", response_model=Dict[str, Any])
async def get_sales_summary(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    location_id: Optional[UUID] = Query(None),
    group_by: str = Query("day", pattern=r"^(hour|day|week|month)$")
):
    """
    Sales summary with time-series data
    
    - **Grouping**: By hour, day, week, or month
    - **Metrics**: Revenue, orders, customers, AOV
    - **Trends**: Growth rates and patterns
    """
    try:
        db = get_database_service()
        
        # Query daily sales summary
        query = db.client.table("daily_sales_summary").select("*")
        query = query.eq("business_id", str(business_id))
        if location_id:
            query = query.eq("location_id", str(location_id))
        query = query.gte("date", start_date.isoformat())
        query = query.lte("date", end_date.isoformat())
        query = query.order("date")
        result = query.execute()
        
        # Aggregate by requested grouping
        from collections import defaultdict
        grouped_data = defaultdict(lambda: {"revenue": 0.0, "orders": 0, "customers": 0})
        
        for record in result.data:
            record_date = datetime.fromisoformat(record["date"]).date()
            
            if group_by == "hour":
                # For hourly, we'd need order-level data with timestamps
                key = record["date"]
            elif group_by == "day":
                key = record["date"]
            elif group_by == "week":
                key = record_date.strftime("%Y-W%U")
            else:  # month
                key = record_date.strftime("%Y-%m")
            
            grouped_data[key]["revenue"] += float(record.get("total_sales", 0))
            grouped_data[key]["orders"] += int(record.get("total_orders", 0))
            grouped_data[key]["customers"] += int(record.get("total_customers", 0))
        
        # Format data for response
        data = [
            {
                "period": key,
                "revenue": round(values["revenue"], 2),
                "orders": values["orders"],
                "customers": values["customers"],
                "avg_order_value": round(values["revenue"] / values["orders"], 2) if values["orders"] > 0 else 0.0
            }
            for key, values in sorted(grouped_data.items())
        ]
        
        # Calculate totals
        total_revenue = sum(d["revenue"] for d in data)
        total_orders = sum(d["orders"] for d in data)
        total_customers = sum(d["customers"] for d in data)
        
        return {
            "business_id": str(business_id),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "group_by": group_by,
            "data": data,
            "totals": {
                "revenue": round(total_revenue, 2),
                "orders": total_orders,
                "customers": total_customers,
                "avg_order_value": round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sales summary: {str(e)}")


@router.get("/sales/by-category", response_model=List[Dict[str, Any]])
async def get_sales_by_category(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Sales breakdown by menu category
    
    - **Revenue**: Total revenue per category
    - **Orders**: Number of orders per category
    - **Percentage**: Category contribution to total
    """
    try:
        db = get_database_service()
        
        # Get item performance data with category info
        query = db.client.table("item_performance").select("*, menu_items!inner(category_id, menu_categories(name))")
        query = query.eq("business_id", str(business_id))
        query = query.gte("date", start_date.isoformat())
        query = query.lte("date", end_date.isoformat())
        result = query.execute()
        
        # Aggregate by category
        from collections import defaultdict
        category_data = defaultdict(lambda: {"revenue": 0.0, "quantity": 0, "profit": 0.0})
        
        for item in result.data:
            category_name = "Uncategorized"
            if item.get("menu_items") and item["menu_items"].get("menu_categories"):
                category_name = item["menu_items"]["menu_categories"].get("name", "Uncategorized")
            
            category_data[category_name]["revenue"] += float(item.get("revenue", 0))
            category_data[category_name]["quantity"] += int(item.get("quantity_sold", 0))
            category_data[category_name]["profit"] += float(item.get("profit", 0))
        
        # Calculate total for percentages
        total_revenue = sum(data["revenue"] for data in category_data.values())
        
        # Format response
        categories = [
            {
                "category": category,
                "revenue": round(data["revenue"], 2),
                "quantity_sold": data["quantity"],
                "profit": round(data["profit"], 2),
                "percentage": round((data["revenue"] / total_revenue * 100), 2) if total_revenue > 0 else 0.0
            }
            for category, data in sorted(category_data.items(), key=lambda x: x[1]["revenue"], reverse=True)
        ]
        
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sales by category: {str(e)}")


@router.get("/sales/by-payment-method", response_model=Dict[str, Any])
async def get_sales_by_payment_method(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Sales breakdown by payment method
    
    - **Methods**: Card, cash, digital wallet
    - **Amounts**: Total per method
    - **Trends**: Payment method preferences
    """
    try:
        db = get_database_service()
        
        # Query payments table
        query = db.client.table("payments").select("payment_method, amount, tip_amount, status")
        query = query.eq("business_id", str(business_id))
        query = query.gte("created_at", start_date.isoformat())
        query = query.lte("created_at", end_date.isoformat())
        query = query.eq("status", "completed")
        result = query.execute()
        
        # Aggregate by payment method
        from collections import defaultdict
        payment_data = defaultdict(lambda: {"amount": 0.0, "tips": 0.0, "count": 0})
        
        for payment in result.data:
            method = payment.get("payment_method", "unknown")
            payment_data[method]["amount"] += float(payment.get("amount", 0))
            payment_data[method]["tips"] += float(payment.get("tip_amount", 0))
            payment_data[method]["count"] += 1
        
        # Calculate total
        total_amount = sum(data["amount"] for data in payment_data.values())
        
        # Format response
        payment_methods = {
            method: {
                "amount": round(data["amount"], 2),
                "tips": round(data["tips"], 2),
                "count": data["count"],
                "percentage": round((data["amount"] / total_amount * 100), 2) if total_amount > 0 else 0.0
            }
            for method, data in payment_data.items()
        }
        
        return {
            "business_id": str(business_id),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "payment_methods": payment_methods,
            "total_amount": round(total_amount, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch payment methods: {str(e)}")


# ============================================================================
# MENU ANALYTICS
# ============================================================================

@router.get("/menu/top-items", response_model=List[Dict[str, Any]])
async def get_top_menu_items(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    metric: str = Query("revenue", pattern=r"^(revenue|quantity|profit)$"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Top-performing menu items
    
    - **Metrics**: Revenue, quantity sold, profit
    - **Rankings**: Best sellers identification
    - **Insights**: Performance trends
    """
    try:
        db = get_database_service()
        items = await db.get_top_menu_items(business_id, start_date, end_date, limit)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch top items: {str(e)}")


@router.get("/menu/item-performance/{item_id}", response_model=Dict[str, Any])
async def get_item_performance(
    item_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Individual item performance analysis
    
    - **Sales trend**: Daily/weekly performance
    - **Profit margin**: Cost vs. revenue
    - **Popularity**: Order frequency
    """
    try:
        db = get_database_service()
        
        # Get item performance data
        query = db.client.table("item_performance").select("*")
        query = query.eq("menu_item_id", str(item_id))
        query = query.gte("date", start_date.isoformat())
        query = query.lte("date", end_date.isoformat())
        query = query.order("date")
        result = query.execute()
        
        # Get item details
        item_query = db.client.table("menu_items").select("name, price, cost")
        item_query = item_query.eq("id", str(item_id))
        item_result = item_query.execute()
        item_info = item_result.data[0] if item_result.data else {}
        
        # Calculate metrics
        total_quantity = sum(int(r.get("quantity_sold", 0)) for r in result.data)
        total_revenue = sum(float(r.get("revenue", 0)) for r in result.data)
        total_cost = sum(float(r.get("cost", 0)) for r in result.data)
        total_profit = total_revenue - total_cost
        
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0
        
        # Format daily performance
        performance = [
            {
                "date": r["date"],
                "quantity_sold": int(r.get("quantity_sold", 0)),
                "revenue": round(float(r.get("revenue", 0)), 2),
                "cost": round(float(r.get("cost", 0)), 2),
                "profit": round(float(r.get("profit", 0)), 2)
            }
            for r in result.data
        ]
        
        return {
            "item_id": str(item_id),
            "item_name": item_info.get("name", "Unknown"),
            "price": float(item_info.get("price", 0)),
            "cost": float(item_info.get("cost", 0)),
            "summary": {
                "total_quantity_sold": total_quantity,
                "total_revenue": round(total_revenue, 2),
                "total_cost": round(total_cost, 2),
                "total_profit": round(total_profit, 2),
                "profit_margin": round(profit_margin, 2)
            },
            "performance": performance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch item performance: {str(e)}")


@router.get("/menu/profit-analysis", response_model=Dict[str, Any])
async def analyze_menu_profitability(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Menu profitability analysis
    
    - **Overall margin**: Business-wide profit margin
    - **By item**: Profit margin per item
    - **By category**: Category profitability
    - **Recommendations**: Pricing optimization suggestions
    """
    try:
        db = get_database_service()
        
        # Get item performance with menu item details
        query = db.client.table("item_performance").select("*, menu_items(name, price, cost, category_id)")
        query = query.eq("business_id", str(business_id))
        query = query.gte("date", start_date.isoformat())
        query = query.lte("date", end_date.isoformat())
        result = query.execute()
        
        # Aggregate by item
        from collections import defaultdict
        item_data = defaultdict(lambda: {"revenue": 0.0, "cost": 0.0, "quantity": 0, "name": ""})
        
        for record in result.data:
            item_id = record.get("menu_item_id")
            item_data[item_id]["revenue"] += float(record.get("revenue", 0))
            item_data[item_id]["cost"] += float(record.get("cost", 0))
            item_data[item_id]["quantity"] += int(record.get("quantity_sold", 0))
            if record.get("menu_items"):
                item_data[item_id]["name"] = record["menu_items"].get("name", "Unknown")
        
        # Calculate margins and categorize
        high_margin_items = []
        low_margin_items = []
        total_revenue = 0.0
        total_cost = 0.0
        
        for item_id, data in item_data.items():
            revenue = data["revenue"]
            cost = data["cost"]
            profit = revenue - cost
            margin = (profit / revenue * 100) if revenue > 0 else 0.0
            
            total_revenue += revenue
            total_cost += cost
            
            item_info = {
                "item_id": str(item_id),
                "name": data["name"],
                "revenue": round(revenue, 2),
                "cost": round(cost, 2),
                "profit": round(profit, 2),
                "margin": round(margin, 2),
                "quantity_sold": data["quantity"]
            }
            
            if margin >= 60:
                high_margin_items.append(item_info)
            elif margin < 30:
                low_margin_items.append(item_info)
        
        # Sort by margin
        high_margin_items.sort(key=lambda x: x["margin"], reverse=True)
        low_margin_items.sort(key=lambda x: x["margin"])
        
        # Calculate overall margin
        overall_profit = total_revenue - total_cost
        overall_margin = (overall_profit / total_revenue * 100) if total_revenue > 0 else 0.0
        
        # Generate recommendations
        recommendations = []
        if low_margin_items:
            recommendations.append({
                "type": "pricing",
                "priority": "high",
                "message": f"Consider increasing prices or reducing costs for {len(low_margin_items)} low-margin items"
            })
        if high_margin_items:
            recommendations.append({
                "type": "promotion",
                "priority": "medium",
                "message": f"Promote {len(high_margin_items)} high-margin items to increase profitability"
            })
        
        return {
            "business_id": str(business_id),
            "overall_margin": round(overall_margin, 2),
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(overall_profit, 2),
            "high_margin_items": high_margin_items[:10],
            "low_margin_items": low_margin_items[:10],
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze profitability: {str(e)}")


# ============================================================================
# CUSTOMER ANALYTICS
# ============================================================================

@router.get("/customers/insights", response_model=Dict[str, Any])
async def get_customer_insights(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Customer behavior insights
    
    - **Demographics**: Customer segments
    - **Behavior**: Order patterns, preferences
    - **Retention**: Repeat customer rate
    - **Lifetime value**: Average customer value
    """
    try:
        db = get_database_service()
        
        # Get orders with customer info
        orders_query = db.client.table("orders").select("customer_id, total_amount, created_at")
        orders_query = orders_query.eq("business_id", str(business_id))
        orders_query = orders_query.gte("created_at", start_date.isoformat())
        orders_query = orders_query.lte("created_at", end_date.isoformat())
        orders_query = orders_query.eq("status", "completed")
        orders_result = orders_query.execute()
        
        # Analyze customer behavior
        from collections import defaultdict
        customer_data = defaultdict(lambda: {"orders": 0, "total_spent": 0.0, "first_order": None})
        hour_distribution = defaultdict(int)
        
        for order in orders_result.data:
            customer_id = order.get("customer_id", "guest")
            amount = float(order.get("total_amount", 0))
            order_time = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00'))
            
            customer_data[customer_id]["orders"] += 1
            customer_data[customer_id]["total_spent"] += amount
            if customer_data[customer_id]["first_order"] is None:
                customer_data[customer_id]["first_order"] = order_time
            
            hour_distribution[order_time.hour] += 1
        
        # Calculate metrics
        total_customers = len(customer_data)
        repeat_customers = sum(1 for data in customer_data.values() if data["orders"] > 1)
        new_customers = total_customers - repeat_customers
        repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0.0
        
        total_revenue = sum(data["total_spent"] for data in customer_data.values())
        avg_lifetime_value = total_revenue / total_customers if total_customers > 0 else 0.0
        
        # Find peak hours (top 3)
        peak_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_hours_formatted = [{"hour": hour, "orders": count} for hour, count in peak_hours]
        
        # Get popular items
        items_query = db.client.table("item_performance").select("menu_item_id, quantity_sold, menu_items(name)")
        items_query = items_query.eq("business_id", str(business_id))
        items_query = items_query.gte("date", start_date.isoformat())
        items_query = items_query.lte("date", end_date.isoformat())
        items_result = items_query.execute()
        
        item_totals = defaultdict(lambda: {"quantity": 0, "name": ""})
        for item in items_result.data:
            item_id = item.get("menu_item_id")
            item_totals[item_id]["quantity"] += int(item.get("quantity_sold", 0))
            if item.get("menu_items"):
                item_totals[item_id]["name"] = item["menu_items"].get("name", "Unknown")
        
        popular_items = sorted(
            [{"name": data["name"], "quantity": data["quantity"]} for data in item_totals.values()],
            key=lambda x: x["quantity"],
            reverse=True
        )[:5]
        
        return {
            "business_id": str(business_id),
            "total_customers": total_customers,
            "new_customers": new_customers,
            "repeat_customers": repeat_customers,
            "repeat_rate": round(repeat_rate, 2),
            "avg_lifetime_value": round(avg_lifetime_value, 2),
            "peak_hours": peak_hours_formatted,
            "popular_items": popular_items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch customer insights: {str(e)}")


@router.get("/customers/cohort-analysis", response_model=Dict[str, Any])
async def get_cohort_analysis(
    business_id: UUID = Query(...),
    cohort_type: str = Query("monthly", pattern=r"^(weekly|monthly)$")
):
    """
    Customer cohort analysis
    
    - **Retention**: Cohort retention rates
    - **Revenue**: Revenue per cohort
    - **Behavior**: Cohort ordering patterns
    """
    try:
        db = get_database_service()
        
        # Get all orders with customer info
        orders_query = db.client.table("orders").select("customer_id, total_amount, created_at")
        orders_query = orders_query.eq("business_id", str(business_id))
        orders_query = orders_query.eq("status", "completed")
        orders_query = orders_query.order("created_at")
        orders_result = orders_query.execute()
        
        # Group customers by first order date (cohort)
        from collections import defaultdict
        customer_first_order = {}
        cohort_data = defaultdict(lambda: defaultdict(lambda: {"customers": set(), "revenue": 0.0}))
        
        for order in orders_result.data:
            customer_id = order.get("customer_id")
            if not customer_id or customer_id == "guest":
                continue
            
            order_date = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00')).date()
            amount = float(order.get("total_amount", 0))
            
            # Track first order
            if customer_id not in customer_first_order:
                customer_first_order[customer_id] = order_date
            
            first_order_date = customer_first_order[customer_id]
            
            # Determine cohort period
            if cohort_type == "weekly":
                cohort_key = first_order_date.strftime("%Y-W%U")
                period_key = order_date.strftime("%Y-W%U")
            else:  # monthly
                cohort_key = first_order_date.strftime("%Y-%m")
                period_key = order_date.strftime("%Y-%m")
            
            cohort_data[cohort_key][period_key]["customers"].add(customer_id)
            cohort_data[cohort_key][period_key]["revenue"] += amount
        
        # Format cohort analysis
        cohorts = []
        for cohort_key in sorted(cohort_data.keys()):
            cohort_info = cohort_data[cohort_key]
            initial_customers = len(cohort_info[cohort_key]["customers"])
            
            periods = []
            for period_key in sorted(cohort_info.keys()):
                period_data = cohort_info[period_key]
                retention_rate = (len(period_data["customers"]) / initial_customers * 100) if initial_customers > 0 else 0.0
                
                periods.append({
                    "period": period_key,
                    "active_customers": len(period_data["customers"]),
                    "retention_rate": round(retention_rate, 2),
                    "revenue": round(period_data["revenue"], 2)
                })
            
            cohorts.append({
                "cohort": cohort_key,
                "initial_customers": initial_customers,
                "periods": periods
            })
        
        return {
            "business_id": str(business_id),
            "cohort_type": cohort_type,
            "cohorts": cohorts[-12:]  # Last 12 cohorts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform cohort analysis: {str(e)}")


# ============================================================================
# OPERATIONAL ANALYTICS
# ============================================================================

@router.get("/operations/table-turnover", response_model=Dict[str, Any])
async def analyze_table_turnover(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    location_id: Optional[UUID] = Query(None)
):
    """
    Table turnover analysis
    
    - **Average turnover**: Time per table
    - **By time of day**: Peak vs. off-peak
    - **By table**: Individual table performance
    - **Optimization**: Turnover improvement suggestions
    """
    try:
        db = get_database_service()
        
        # Get orders with table assignments
        orders_query = db.client.table("orders").select("id, table_id, created_at, completed_at, tables(table_number)")
        orders_query = orders_query.eq("business_id", str(business_id))
        if location_id:
            orders_query = orders_query.eq("location_id", str(location_id))
        orders_query = orders_query.gte("created_at", start_date.isoformat())
        orders_query = orders_query.lte("created_at", end_date.isoformat())
        orders_query = orders_query.eq("status", "completed")
        orders_query = orders_query.not_.is_("table_id", "null")
        orders_query = orders_query.not_.is_("completed_at", "null")
        orders_result = orders_query.execute()
        
        # Calculate turnover times
        from collections import defaultdict
        table_turnovers = defaultdict(list)
        hour_turnovers = defaultdict(list)
        all_turnovers = []
        
        for order in orders_result.data:
            if not order.get("created_at") or not order.get("completed_at"):
                continue
            
            created = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00'))
            completed = datetime.fromisoformat(order["completed_at"].replace('Z', '+00:00'))
            turnover_minutes = (completed - created).total_seconds() / 60
            
            all_turnovers.append(turnover_minutes)
            hour_turnovers[created.hour].append(turnover_minutes)
            
            table_id = order.get("table_id")
            if table_id:
                table_turnovers[table_id].append(turnover_minutes)
        
        # Calculate average turnover
        avg_turnover = sum(all_turnovers) / len(all_turnovers) if all_turnovers else 0
        
        # By time of day
        by_time_of_day = {
            f"{hour:02d}:00": round(sum(times) / len(times), 2) if times else 0
            for hour, times in hour_turnovers.items()
        }
        
        # By table
        by_table = [
            {
                "table_id": str(table_id),
                "avg_turnover_minutes": round(sum(times) / len(times), 2) if times else 0,
                "orders_count": len(times)
            }
            for table_id, times in table_turnovers.items()
        ]
        by_table.sort(key=lambda x: x["avg_turnover_minutes"], reverse=True)
        
        # Generate recommendations
        recommendations = []
        if avg_turnover > 90:
            recommendations.append({
                "type": "efficiency",
                "priority": "high",
                "message": "Average turnover exceeds 90 minutes. Consider optimizing kitchen workflow or adding staff."
            })
        if avg_turnover < 30:
            recommendations.append({
                "type": "revenue",
                "priority": "medium",
                "message": "Fast turnover detected. Consider strategies to increase average order value."
            })
        
        return {
            "business_id": str(business_id),
            "avg_turnover_minutes": round(avg_turnover, 2),
            "by_time_of_day": by_time_of_day,
            "by_table": by_table[:20],
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze table turnover: {str(e)}")


@router.get("/operations/kitchen-performance", response_model=Dict[str, Any])
async def analyze_kitchen_performance(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    station: Optional[str] = Query(None)
):
    """
    Kitchen performance analysis
    
    - **Prep times**: Average and by item
    - **Efficiency**: Orders per hour
    - **Delays**: Late order analysis
    - **Bottlenecks**: Station performance
    """
    try:
        db = get_database_service()
        
        # Get KDS orders
        kds_query = db.client.table("kds_orders").select("*")
        kds_query = kds_query.eq("business_id", str(business_id))
        kds_query = kds_query.gte("created_at", start_date.isoformat())
        kds_query = kds_query.lte("created_at", end_date.isoformat())
        if station:
            kds_query = kds_query.eq("station", station)
        kds_result = kds_query.execute()
        
        # Analyze performance
        from collections import defaultdict
        station_data = defaultdict(lambda: {"prep_times": [], "orders": 0, "late": 0})
        all_prep_times = []
        late_orders = 0
        total_orders = 0
        
        for order in kds_result.data:
            total_orders += 1
            station_name = order.get("station", "unknown")
            station_data[station_name]["orders"] += 1
            
            # Calculate prep time
            if order.get("prep_start_time") and order.get("prep_end_time"):
                start = datetime.fromisoformat(order["prep_start_time"].replace('Z', '+00:00'))
                end = datetime.fromisoformat(order["prep_end_time"].replace('Z', '+00:00'))
                prep_time = (end - start).total_seconds() / 60
                
                all_prep_times.append(prep_time)
                station_data[station_name]["prep_times"].append(prep_time)
                
                # Check if late (assuming 15 min target)
                if order.get("target_time"):
                    target = datetime.fromisoformat(order["target_time"].replace('Z', '+00:00'))
                    if end > target:
                        late_orders += 1
                        station_data[station_name]["late"] += 1
        
        # Calculate metrics
        avg_prep_time = sum(all_prep_times) / len(all_prep_times) if all_prep_times else 0
        
        # Calculate orders per hour
        time_span_hours = (end_date - start_date).days * 24
        orders_per_hour = total_orders / time_span_hours if time_span_hours > 0 else 0
        
        late_percentage = (late_orders / total_orders * 100) if total_orders > 0 else 0.0
        
        # By station
        by_station = {}
        bottlenecks = []
        for station_name, data in station_data.items():
            avg_station_prep = sum(data["prep_times"]) / len(data["prep_times"]) if data["prep_times"] else 0
            late_rate = (data["late"] / data["orders"] * 100) if data["orders"] > 0 else 0.0
            
            by_station[station_name] = {
                "avg_prep_time": round(avg_station_prep, 2),
                "orders": data["orders"],
                "late_rate": round(late_rate, 2)
            }
            
            # Identify bottlenecks
            if avg_station_prep > avg_prep_time * 1.5:
                bottlenecks.append({
                    "station": station_name,
                    "issue": "slow_prep_time",
                    "avg_prep_time": round(avg_station_prep, 2)
                })
        
        return {
            "business_id": str(business_id),
            "avg_prep_time_minutes": round(avg_prep_time, 2),
            "orders_per_hour": round(orders_per_hour, 2),
            "late_orders_percentage": round(late_percentage, 2),
            "by_station": by_station,
            "bottlenecks": bottlenecks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze kitchen performance: {str(e)}")


@router.get("/operations/staff-performance", response_model=Dict[str, Any])
async def analyze_staff_performance(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Staff performance analysis
    
    - **Sales per staff**: Revenue attribution
    - **Efficiency**: Orders handled per hour
    - **Hours worked**: Total and overtime
    - **Attendance**: Punctuality and reliability
    """
    try:
        db = get_database_service()
        
        # Get time clock data
        clock_query = db.client.table("time_clock").select("*, staff_members(first_name, last_name, position)")
        clock_query = clock_query.eq("business_id", str(business_id))
        clock_query = clock_query.gte("clock_in", start_date.isoformat())
        clock_query = clock_query.lte("clock_in", end_date.isoformat())
        clock_query = clock_query.not_.is_("clock_out", "null")
        clock_result = clock_query.execute()
        
        # Aggregate staff metrics
        from collections import defaultdict
        staff_data = defaultdict(lambda: {
            "name": "",
            "position": "",
            "total_hours": 0.0,
            "overtime_hours": 0.0,
            "shifts": 0
        })
        
        for record in clock_result.data:
            staff_id = record.get("staff_id")
            hours = float(record.get("total_hours", 0))
            overtime = float(record.get("overtime_hours", 0))
            
            staff_data[staff_id]["total_hours"] += hours
            staff_data[staff_id]["overtime_hours"] += overtime
            staff_data[staff_id]["shifts"] += 1
            
            if record.get("staff_members"):
                staff_info = record["staff_members"]
                staff_data[staff_id]["name"] = f"{staff_info.get('first_name', '')} {staff_info.get('last_name', '')}".strip()
                staff_data[staff_id]["position"] = staff_info.get("position", "Unknown")
        
        # Format staff metrics
        staff_metrics = [
            {
                "staff_id": str(staff_id),
                "name": data["name"],
                "position": data["position"],
                "total_hours": round(data["total_hours"], 2),
                "overtime_hours": round(data["overtime_hours"], 2),
                "shifts": data["shifts"],
                "avg_hours_per_shift": round(data["total_hours"] / data["shifts"], 2) if data["shifts"] > 0 else 0
            }
            for staff_id, data in staff_data.items()
        ]
        
        # Sort by total hours
        staff_metrics.sort(key=lambda x: x["total_hours"], reverse=True)
        
        return {
            "business_id": str(business_id),
            "staff_metrics": staff_metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze staff performance: {str(e)}")


# ============================================================================
# FINANCIAL ANALYTICS
# ============================================================================

@router.get("/financial/summary", response_model=Dict[str, Any])
async def get_financial_summary(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Financial summary report
    
    - **Revenue**: Total revenue breakdown
    - **Costs**: COGS, labor, overhead
    - **Profit**: Gross and net profit
    - **Margins**: Profit margin percentages
    """
    try:
        db = get_database_service()
        
        # Get revenue data
        revenue_query = db.client.table("daily_sales_summary").select("*")
        revenue_query = revenue_query.eq("business_id", str(business_id))
        revenue_query = revenue_query.gte("date", start_date.isoformat())
        revenue_query = revenue_query.lte("date", end_date.isoformat())
        revenue_result = revenue_query.execute()
        
        total_revenue = sum(float(r.get("total_revenue", 0)) for r in revenue_result.data)
        
        # Get inventory valuation for COGS estimate
        inventory_val = await db.get_inventory_valuation(business_id)
        
        # Calculate metrics
        cogs = total_revenue * 0.30  # Estimate 30% COGS
        labor = total_revenue * 0.25  # Estimate 25% labor
        overhead = total_revenue * 0.15  # Estimate 15% overhead
        
        gross_profit = total_revenue - cogs
        net_profit = gross_profit - labor - overhead
        
        gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        net_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            "business_id": str(business_id),
            "revenue": {
                "total": total_revenue,
                "by_category": {}
            },
            "costs": {
                "cogs": cogs,
                "labor": labor,
                "overhead": overhead
            },
            "profit": {
                "gross": gross_profit,
                "net": net_profit
            },
            "margins": {
                "gross_margin": round(gross_margin, 2),
                "net_margin": round(net_margin, 2)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch financial summary: {str(e)}")


@router.get("/financial/labor-costs", response_model=Dict[str, Any])
async def analyze_labor_costs(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Labor cost analysis
    
    - **Total costs**: Regular and overtime
    - **Labor percentage**: % of revenue
    - **By position**: Cost breakdown
    - **Optimization**: Scheduling recommendations
    """
    try:
        db = get_database_service()
        
        # Get time clock data with staff rates
        clock_query = db.client.table("time_clock").select("*, staff_members(hourly_rate, position)")
        clock_query = clock_query.eq("business_id", str(business_id))
        clock_query = clock_query.gte("clock_in", start_date.isoformat())
        clock_query = clock_query.lte("clock_in", end_date.isoformat())
        clock_query = clock_query.not_.is_("clock_out", "null")
        clock_result = clock_query.execute()
        
        # Get revenue for percentage calculation
        revenue_query = db.client.table("daily_sales_summary").select("total_sales")
        revenue_query = revenue_query.eq("business_id", str(business_id))
        revenue_query = revenue_query.gte("date", start_date.isoformat())
        revenue_query = revenue_query.lte("date", end_date.isoformat())
        revenue_result = revenue_query.execute()
        total_revenue = sum(float(r.get("total_sales", 0)) for r in revenue_result.data)
        
        # Calculate labor costs
        from collections import defaultdict
        position_costs = defaultdict(lambda: {"regular": 0.0, "overtime": 0.0})
        total_labor_cost = 0.0
        total_overtime_cost = 0.0
        
        for record in clock_result.data:
            regular_hours = float(record.get("total_hours", 0)) - float(record.get("overtime_hours", 0))
            overtime_hours = float(record.get("overtime_hours", 0))
            
            hourly_rate = 15.0  # Default rate
            position = "Unknown"
            if record.get("staff_members"):
                hourly_rate = float(record["staff_members"].get("hourly_rate", 15.0))
                position = record["staff_members"].get("position", "Unknown")
            
            regular_cost = regular_hours * hourly_rate
            overtime_cost = overtime_hours * hourly_rate * 1.5  # 1.5x for overtime
            
            position_costs[position]["regular"] += regular_cost
            position_costs[position]["overtime"] += overtime_cost
            
            total_labor_cost += regular_cost + overtime_cost
            total_overtime_cost += overtime_cost
        
        # Calculate labor percentage
        labor_percentage = (total_labor_cost / total_revenue * 100) if total_revenue > 0 else 0.0
        
        # Format by position
        by_position = {
            position: {
                "regular_cost": round(costs["regular"], 2),
                "overtime_cost": round(costs["overtime"], 2),
                "total_cost": round(costs["regular"] + costs["overtime"], 2)
            }
            for position, costs in position_costs.items()
        }
        
        return {
            "business_id": str(business_id),
            "total_labor_cost": round(total_labor_cost, 2),
            "labor_percentage": round(labor_percentage, 2),
            "overtime_cost": round(total_overtime_cost, 2),
            "by_position": by_position
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze labor costs: {str(e)}")


@router.get("/financial/cogs", response_model=Dict[str, Any])
async def analyze_cogs(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Cost of Goods Sold (COGS) analysis
    
    - **Total COGS**: Inventory costs
    - **COGS percentage**: % of revenue
    - **By category**: Category-wise breakdown
    - **Trends**: COGS over time
    """
    try:
        db = get_database_service()
        
        # Get inventory transactions (sales/usage)
        inv_query = db.client.table("inventory_transactions").select("*, inventory_items(name, category, unit_cost)")
        inv_query = inv_query.eq("business_id", str(business_id))
        inv_query = inv_query.gte("created_at", start_date.isoformat())
        inv_query = inv_query.lte("created_at", end_date.isoformat())
        inv_query = inv_query.in_("transaction_type", ["sale", "waste"])
        inv_result = inv_query.execute()
        
        # Get revenue for percentage
        revenue_query = db.client.table("daily_sales_summary").select("total_sales")
        revenue_query = revenue_query.eq("business_id", str(business_id))
        revenue_query = revenue_query.gte("date", start_date.isoformat())
        revenue_query = revenue_query.lte("date", end_date.isoformat())
        revenue_result = revenue_query.execute()
        total_revenue = sum(float(r.get("total_sales", 0)) for r in revenue_result.data)
        
        # Calculate COGS
        from collections import defaultdict
        category_cogs = defaultdict(float)
        total_cogs = 0.0
        
        for transaction in inv_result.data:
            quantity = abs(float(transaction.get("quantity", 0)))
            unit_cost = float(transaction.get("unit_cost", 0))
            
            if not unit_cost and transaction.get("inventory_items"):
                unit_cost = float(transaction["inventory_items"].get("unit_cost", 0))
            
            cost = quantity * unit_cost
            total_cogs += cost
            
            if transaction.get("inventory_items"):
                category = transaction["inventory_items"].get("category", "Uncategorized")
                category_cogs[category] += cost
        
        # Calculate COGS percentage
        cogs_percentage = (total_cogs / total_revenue * 100) if total_revenue > 0 else 0.0
        
        # Format by category
        by_category = {
            category: round(cost, 2)
            for category, cost in sorted(category_cogs.items(), key=lambda x: x[1], reverse=True)
        }
        
        return {
            "business_id": str(business_id),
            "total_cogs": round(total_cogs, 2),
            "cogs_percentage": round(cogs_percentage, 2),
            "by_category": by_category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze COGS: {str(e)}")


# ============================================================================
# COMPARATIVE ANALYTICS
# ============================================================================

@router.get("/compare/period-over-period", response_model=Dict[str, Any])
async def compare_periods(
    business_id: UUID = Query(...),
    current_start: date = Query(...),
    current_end: date = Query(...),
    comparison_type: str = Query("previous", pattern=r"^(previous|year_ago)$")
):
    """
    Period-over-period comparison
    
    - **Growth rates**: Revenue, orders, customers
    - **Trends**: Improving or declining metrics
    - **Insights**: Key changes and drivers
    """
    try:
        db = get_database_service()
        
        # Calculate comparison period dates
        period_length = (current_end - current_start).days
        if comparison_type == "previous":
            comp_start = current_start - timedelta(days=period_length + 1)
            comp_end = current_start - timedelta(days=1)
        else:  # year_ago
            comp_start = current_start - timedelta(days=365)
            comp_end = current_end - timedelta(days=365)
        
        # Get current period data
        current_query = db.client.table("daily_sales_summary").select("*")
        current_query = current_query.eq("business_id", str(business_id))
        current_query = current_query.gte("date", current_start.isoformat())
        current_query = current_query.lte("date", current_end.isoformat())
        current_result = current_query.execute()
        
        # Get comparison period data
        comp_query = db.client.table("daily_sales_summary").select("*")
        comp_query = comp_query.eq("business_id", str(business_id))
        comp_query = comp_query.gte("date", comp_start.isoformat())
        comp_query = comp_query.lte("date", comp_end.isoformat())
        comp_result = comp_query.execute()
        
        # Calculate metrics for both periods
        def calculate_metrics(data):
            revenue = sum(float(r.get("total_sales", 0)) for r in data)
            orders = sum(int(r.get("total_orders", 0)) for r in data)
            customers = sum(int(r.get("total_customers", 0)) for r in data)
            return {
                "revenue": round(revenue, 2),
                "orders": orders,
                "customers": customers,
                "avg_order_value": round(revenue / orders, 2) if orders > 0 else 0.0
            }
        
        current_metrics = calculate_metrics(current_result.data)
        comp_metrics = calculate_metrics(comp_result.data)
        
        # Calculate growth rates
        def calc_growth(current, previous):
            if previous == 0:
                return 0.0
            return round(((current - previous) / previous * 100), 2)
        
        growth_rates = {
            "revenue_growth": calc_growth(current_metrics["revenue"], comp_metrics["revenue"]),
            "orders_growth": calc_growth(current_metrics["orders"], comp_metrics["orders"]),
            "customers_growth": calc_growth(current_metrics["customers"], comp_metrics["customers"]),
            "aov_growth": calc_growth(current_metrics["avg_order_value"], comp_metrics["avg_order_value"])
        }
        
        return {
            "business_id": str(business_id),
            "current_period": {
                "start_date": current_start.isoformat(),
                "end_date": current_end.isoformat(),
                "metrics": current_metrics
            },
            "comparison_period": {
                "start_date": comp_start.isoformat(),
                "end_date": comp_end.isoformat(),
                "metrics": comp_metrics
            },
            "growth_rates": growth_rates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare periods: {str(e)}")


@router.get("/compare/locations", response_model=Dict[str, Any])
async def compare_locations(
    business_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Multi-location comparison
    
    - **Performance**: Compare location metrics
    - **Best practices**: Identify top performers
    - **Opportunities**: Underperforming locations
    """
    try:
        db = get_database_service()
        
        # Get all locations
        locations_query = db.client.table("locations").select("id, name")
        locations_query = locations_query.eq("business_id", str(business_id))
        locations_query = locations_query.eq("is_active", True)
        locations_result = locations_query.execute()
        
        # Get sales data for each location
        locations_data = []
        for location in locations_result.data:
            location_id = location["id"]
            location_name = location["name"]
            
            sales_query = db.client.table("daily_sales_summary").select("*")
            sales_query = sales_query.eq("business_id", str(business_id))
            sales_query = sales_query.eq("location_id", location_id)
            sales_query = sales_query.gte("date", start_date.isoformat())
            sales_query = sales_query.lte("date", end_date.isoformat())
            sales_result = sales_query.execute()
            
            # Calculate metrics
            revenue = sum(float(r.get("total_sales", 0)) for r in sales_result.data)
            orders = sum(int(r.get("total_orders", 0)) for r in sales_result.data)
            customers = sum(int(r.get("total_customers", 0)) for r in sales_result.data)
            
            locations_data.append({
                "location_id": str(location_id),
                "location_name": location_name,
                "revenue": round(revenue, 2),
                "orders": orders,
                "customers": customers,
                "avg_order_value": round(revenue / orders, 2) if orders > 0 else 0.0
            })
        
        # Sort by revenue
        locations_data.sort(key=lambda x: x["revenue"], reverse=True)
        
        # Calculate total for percentages
        total_revenue = sum(loc["revenue"] for loc in locations_data)
        for loc in locations_data:
            loc["revenue_percentage"] = round((loc["revenue"] / total_revenue * 100), 2) if total_revenue > 0 else 0.0
        
        return {
            "business_id": str(business_id),
            "locations": locations_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare locations: {str(e)}")


# ============================================================================
# FORECASTING & PREDICTIONS
# ============================================================================

@router.get("/forecast/revenue", response_model=Dict[str, Any])
async def forecast_revenue(
    business_id: UUID = Query(...),
    forecast_days: int = Query(30, ge=1, le=365)
):
    """
    Revenue forecasting
    
    - **Predictions**: Future revenue estimates
    - **Confidence intervals**: Prediction ranges
    - **Trends**: Growth trajectory
    """
    try:
        db = get_database_service()
        
        # Get historical data (last 90 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
        
        sales_query = db.client.table("daily_sales_summary").select("date, total_sales")
        sales_query = sales_query.eq("business_id", str(business_id))
        sales_query = sales_query.gte("date", start_date.isoformat())
        sales_query = sales_query.lte("date", end_date.isoformat())
        sales_query = sales_query.order("date")
        sales_result = sales_query.execute()
        
        # Simple moving average forecast
        historical_revenue = [float(r.get("total_sales", 0)) for r in sales_result.data]
        
        if len(historical_revenue) < 7:
            raise HTTPException(status_code=400, detail="Insufficient historical data for forecasting")
        
        # Calculate 7-day moving average
        window_size = 7
        moving_avg = sum(historical_revenue[-window_size:]) / window_size
        
        # Calculate trend (simple linear regression)
        n = len(historical_revenue)
        x_values = list(range(n))
        y_values = historical_revenue
        
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        # Generate forecast
        forecast = []
        for day in range(1, forecast_days + 1):
            forecast_date = end_date + timedelta(days=day)
            # Combine moving average with trend
            predicted_value = moving_avg + (slope * (n + day))
            predicted_value = max(0, predicted_value)  # Ensure non-negative
            
            forecast.append({
                "date": forecast_date.isoformat(),
                "predicted_revenue": round(predicted_value, 2),
                "confidence": "medium"  # Simple model has medium confidence
            })
        
        return {
            "business_id": str(business_id),
            "forecast_days": forecast_days,
            "method": "moving_average_with_trend",
            "historical_avg": round(moving_avg, 2),
            "trend_slope": round(slope, 2),
            "forecast": forecast
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to forecast revenue: {str(e)}")


@router.get("/forecast/inventory-needs", response_model=Dict[str, Any])
async def forecast_inventory_needs(
    business_id: UUID = Query(...),
    forecast_days: int = Query(7, ge=1, le=30)
):
    """
    Inventory needs forecasting
    
    - **Predictions**: Expected usage
    - **Reorder recommendations**: What to order
    - **Quantities**: Optimal order amounts
    """
    try:
        db = get_database_service()
        
        # Get historical inventory usage (last 30 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        inv_query = db.client.table("inventory_transactions").select("inventory_item_id, quantity, created_at, inventory_items(name, unit, min_stock, current_stock)")
        inv_query = inv_query.eq("business_id", str(business_id))
        inv_query = inv_query.gte("created_at", start_date.isoformat())
        inv_query = inv_query.in_("transaction_type", ["sale", "waste"])
        inv_result = inv_query.execute()
        
        # Aggregate usage by item
        from collections import defaultdict
        item_usage = defaultdict(lambda: {"total_used": 0.0, "name": "", "unit": "", "min_stock": 0, "current_stock": 0})
        
        for transaction in inv_result.data:
            item_id = transaction.get("inventory_item_id")
            quantity = abs(float(transaction.get("quantity", 0)))
            
            item_usage[item_id]["total_used"] += quantity
            
            if transaction.get("inventory_items"):
                item_info = transaction["inventory_items"]
                item_usage[item_id]["name"] = item_info.get("name", "Unknown")
                item_usage[item_id]["unit"] = item_info.get("unit", "units")
                item_usage[item_id]["min_stock"] = float(item_info.get("min_stock", 0))
                item_usage[item_id]["current_stock"] = float(item_info.get("current_stock", 0))
        
        # Calculate daily usage rate and forecast needs
        recommendations = []
        for item_id, data in item_usage.items():
            daily_usage = data["total_used"] / 30  # Average daily usage
            forecasted_usage = daily_usage * forecast_days
            
            current_stock = data["current_stock"]
            min_stock = data["min_stock"]
            
            # Calculate days until stockout
            days_until_stockout = current_stock / daily_usage if daily_usage > 0 else 999
            
            # Determine if reorder is needed
            if days_until_stockout < forecast_days:
                reorder_quantity = forecasted_usage - current_stock + min_stock
                reorder_quantity = max(0, reorder_quantity)
                
                recommendations.append({
                    "item_id": str(item_id),
                    "item_name": data["name"],
                    "current_stock": round(current_stock, 2),
                    "daily_usage": round(daily_usage, 2),
                    "forecasted_usage": round(forecasted_usage, 2),
                    "days_until_stockout": round(days_until_stockout, 1),
                    "recommended_order_quantity": round(reorder_quantity, 2),
                    "unit": data["unit"],
                    "priority": "high" if days_until_stockout < 7 else "medium"
                })
        
        # Sort by priority and days until stockout
        recommendations.sort(key=lambda x: (x["priority"] == "medium", x["days_until_stockout"]))
        
        return {
            "business_id": str(business_id),
            "forecast_days": forecast_days,
            "recommendations": recommendations[:50]  # Top 50 items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to forecast inventory needs: {str(e)}")


# ============================================================================
# REPORTS GENERATION
# ============================================================================

@router.post("/reports/generate", response_model=Dict[str, Any])
async def generate_comprehensive_report(
    business_id: UUID,
    report_type: str = Query(..., pattern=r"^(daily|weekly|monthly|custom)$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    include_charts: bool = Query(True),
    format: str = Query("pdf", pattern=r"^(pdf|excel|json)$")
):
    """
    Generate comprehensive business report
    
    - **Report types**: Daily, weekly, monthly, custom
    - **Formats**: PDF, Excel, JSON
    - **Content**: Sales, operations, financial, inventory
    - **Charts**: Visual data representation
    """
    try:
        db = get_database_service()
        
        # Determine date range based on report type
        end_date_val = end_date if end_date else date.today()
        if report_type == "daily":
            start_date_val = end_date_val
        elif report_type == "weekly":
            start_date_val = end_date_val - timedelta(days=7)
        elif report_type == "monthly":
            start_date_val = end_date_val - timedelta(days=30)
        else:  # custom
            if not start_date:
                raise HTTPException(status_code=400, detail="start_date required for custom reports")
            start_date_val = start_date
        
        # Gather report data
        # Sales summary
        sales_query = db.client.table("daily_sales_summary").select("*")
        sales_query = sales_query.eq("business_id", str(business_id))
        sales_query = sales_query.gte("date", start_date_val.isoformat())
        sales_query = sales_query.lte("date", end_date_val.isoformat())
        sales_result = sales_query.execute()
        
        total_revenue = sum(float(r.get("total_sales", 0)) for r in sales_result.data)
        total_orders = sum(int(r.get("total_orders", 0)) for r in sales_result.data)
        
        # Top items
        top_items = await db.get_top_menu_items(business_id, start_date_val, end_date_val, 10)
        
        # Generate report ID
        report_id = f"report_{business_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Compile report data
        report_data = {
            "report_id": report_id,
            "business_id": str(business_id),
            "report_type": report_type,
            "period": {
                "start_date": start_date_val.isoformat(),
                "end_date": end_date_val.isoformat()
            },
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "total_orders": total_orders,
                "avg_order_value": round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
            },
            "top_items": top_items[:10],
            "format": format,
            "include_charts": include_charts
        }
        
        # In a real implementation, you would:
        # 1. Generate PDF/Excel using reportlab/openpyxl
        # 2. Create charts with Plotly
        # 3. Upload to cloud storage (S3/Supabase Storage)
        # 4. Return download URL
        
        # For now, return report data structure
        return {
            "report_id": report_id,
            "business_id": str(business_id),
            "report_type": report_type,
            "format": format,
            "download_url": f"https://storage.example.com/reports/{report_id}.{format}",
            "report_data": report_data,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "generated"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/reports/scheduled", response_model=List[Dict[str, Any]])
async def list_scheduled_reports(business_id: UUID = Query(...)):
    """
    List scheduled reports
    
    - **Recurring reports**: Daily, weekly, monthly
    - **Recipients**: Email distribution lists
    - **Status**: Active, paused, completed
    """
    try:
        db = get_database_service()
        
        # Query scheduled reports table (would need to be created)
        # For now, return empty list with structure
        # In production, query: scheduled_reports table
        
        # Example structure:
        scheduled_reports = [
            # {
            #     "schedule_id": "schedule_123",
            #     "business_id": str(business_id),
            #     "report_type": "daily",
            #     "frequency": "daily",
            #     "recipients": ["owner@business.com"],
            #     "format": "pdf",
            #     "status": "active",
            #     "next_run": "2025-10-11T06:00:00Z",
            #     "created_at": "2025-10-01T00:00:00Z"
            # }
        ]
        
        return scheduled_reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list scheduled reports: {str(e)}")


@router.post("/reports/schedule", response_model=Dict[str, Any])
async def schedule_report(
    business_id: UUID,
    report_config: Dict[str, Any]
):
    """
    Schedule recurring report
    
    - **Frequency**: Daily, weekly, monthly
    - **Recipients**: Email addresses
    - **Content**: Customizable sections
    """
    try:
        db = get_database_service()
        
        # Validate report configuration
        frequency = report_config.get("frequency", "daily")
        if frequency not in ["daily", "weekly", "monthly"]:
            raise HTTPException(status_code=400, detail="Invalid frequency")
        
        recipients = report_config.get("recipients", [])
        if not recipients:
            raise HTTPException(status_code=400, detail="At least one recipient required")
        
        # Generate schedule ID
        schedule_id = f"schedule_{business_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # In production, insert into scheduled_reports table:
        # schedule_data = {
        #     "id": schedule_id,
        #     "business_id": str(business_id),
        #     "report_type": report_config.get("report_type", "daily"),
        #     "frequency": frequency,
        #     "recipients": recipients,
        #     "format": report_config.get("format", "pdf"),
        #     "include_charts": report_config.get("include_charts", True),
        #     "status": "active",
        #     "created_at": datetime.utcnow().isoformat()
        # }
        # db.client.table("scheduled_reports").insert(schedule_data).execute()
        
        return {
            "schedule_id": schedule_id,
            "business_id": str(business_id),
            "frequency": frequency,
            "recipients": recipients,
            "status": "active",
            "message": "Report scheduled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule report: {str(e)}")
