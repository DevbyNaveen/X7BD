"""
Universal Analytics Endpoints for All Business Categories
Provides comprehensive analytics across all templates
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from ..services.database import get_database_service

router = APIRouter(prefix="/api/v1/analytics", tags=["Universal Analytics"])


# ============================================================================
# DASHBOARD ANALYTICS (All Categories)
# ============================================================================

@router.get("/dashboard/{business_id}")
async def get_universal_dashboard(
    business_id: UUID,
    period: str = Query("7d", description="Time period: 1d, 7d, 30d, 90d, 1y")
):
    """
    Get universal dashboard analytics for any business type
    Adapts based on business category
    """
    db = get_database_service()
    
    try:
        # Get business info to determine category
        business_result = await db.supabase.table("businesses").select("*, business_categories(name)").eq("id", str(business_id)).execute()
        
        if not business_result.data:
            raise HTTPException(status_code=404, detail="Business not found")
        
        business = business_result.data[0]
        category_name = business.get("business_categories", {}).get("name", "").lower()
        
        # Calculate date range
        days_map = {"1d": 1, "7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(period, 7)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Base metrics (common to all)
        base_metrics = {
            "business_id": str(business_id),
            "business_name": business.get("name"),
            "category": category_name,
            "period": period,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Category-specific metrics
        if any(cat in category_name for cat in ["restaurant", "cafe", "bar", "food"]):
            # Food & Hospitality metrics
            orders_result = await db.supabase.table("orders").select("*").eq("business_id", str(business_id)).gte("created_at", start_date.isoformat()).execute()
            orders = orders_result.data if orders_result.data else []
            
            menu_items_result = await db.supabase.table("menu_items").select("*").eq("business_id", str(business_id)).execute()
            menu_items = menu_items_result.data if menu_items_result.data else []
            
            tables_result = await db.supabase.table("tables").select("*").eq("business_id", str(business_id)).execute()
            tables = tables_result.data if tables_result.data else []
            
            return {
                **base_metrics,
                "metrics": {
                    "total_orders": len(orders),
                    "total_revenue": sum(o.get("total_amount", 0) for o in orders),
                    "avg_order_value": sum(o.get("total_amount", 0) for o in orders) / len(orders) if orders else 0,
                    "menu_items_count": len(menu_items),
                    "tables_count": len(tables),
                    "active_tables": len([t for t in tables if t.get("status") == "occupied"])
                },
                "template": "food_hospitality"
            }
        
        elif any(cat in category_name for cat in ["salon", "spa", "barbershop", "gym", "fitness"]):
            # Service-Based metrics
            appointments_result = await db.supabase.table("appointments").select("*").eq("business_id", str(business_id)).gte("scheduled_time", start_date.isoformat()).execute()
            appointments = appointments_result.data if appointments_result.data else []
            
            services_result = await db.supabase.table("services").select("*").eq("business_id", str(business_id)).execute()
            services = services_result.data if services_result.data else []
            
            clients_result = await db.supabase.table("clients").select("*").eq("business_id", str(business_id)).execute()
            clients = clients_result.data if clients_result.data else []
            
            completed = [a for a in appointments if a.get("status") == "completed"]
            
            return {
                **base_metrics,
                "metrics": {
                    "total_appointments": len(appointments),
                    "completed_appointments": len(completed),
                    "total_revenue": sum(c.get("total_spent", 0) for c in clients),
                    "services_count": len(services),
                    "clients_count": len(clients),
                    "avg_appointment_value": sum(c.get("total_spent", 0) for c in clients) / len(completed) if completed else 0
                },
                "template": "service_based"
            }
        
        elif any(cat in category_name for cat in ["retail", "store", "boutique", "shop", "pharmacy"]):
            # Retail metrics
            products_result = await db.supabase.table("products").select("*").eq("business_id", str(business_id)).execute()
            products = products_result.data if products_result.data else []
            
            customers_result = await db.supabase.table("customers").select("*").eq("business_id", str(business_id)).execute()
            customers = customers_result.data if customers_result.data else []
            
            orders_result = await db.supabase.table("orders").select("*").eq("business_id", str(business_id)).gte("created_at", start_date.isoformat()).execute()
            orders = orders_result.data if orders_result.data else []
            
            low_stock = [p for p in products if p.get("inventory_quantity", 0) <= p.get("low_stock_threshold", 10)]
            
            return {
                **base_metrics,
                "metrics": {
                    "total_products": len(products),
                    "total_customers": len(customers),
                    "total_orders": len(orders),
                    "total_revenue": sum(o.get("total_amount", 0) for o in orders),
                    "low_stock_items": len(low_stock),
                    "avg_order_value": sum(o.get("total_amount", 0) for o in orders) / len(orders) if orders else 0
                },
                "template": "retail"
            }
        
        elif any(cat in category_name for cat in ["law", "accounting", "consulting", "agency", "professional"]):
            # Professional Services metrics
            projects_result = await db.supabase.table("projects").select("*").eq("business_id", str(business_id)).execute()
            projects = projects_result.data if projects_result.data else []
            
            time_entries_result = await db.supabase.table("time_entries").select("*").eq("business_id", str(business_id)).gte("start_time", start_date.isoformat()).execute()
            time_entries = time_entries_result.data if time_entries_result.data else []
            
            invoices_result = await db.supabase.table("invoices").select("*").eq("business_id", str(business_id)).execute()
            invoices = invoices_result.data if invoices_result.data else []
            
            clients_result = await db.supabase.table("clients").select("*").eq("business_id", str(business_id)).execute()
            clients = clients_result.data if clients_result.data else []
            
            active_projects = [p for p in projects if p.get("status") == "active"]
            billable_hours = sum(te.get("duration_hours", 0) for te in time_entries if te.get("billable"))
            
            return {
                **base_metrics,
                "metrics": {
                    "total_projects": len(projects),
                    "active_projects": len(active_projects),
                    "total_clients": len(clients),
                    "billable_hours": billable_hours,
                    "total_invoices": len(invoices),
                    "total_revenue": sum(i.get("total_amount", 0) for i in invoices if i.get("status") == "paid")
                },
                "template": "professional_services"
            }
        
        else:
            # Generic metrics for unknown categories
            return {
                **base_metrics,
                "metrics": {
                    "message": "Category-specific metrics not available"
                },
                "template": "generic"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FINANCIAL ANALYTICS
# ============================================================================

@router.get("/financial/summary")
async def get_financial_summary(
    business_id: UUID = Query(..., description="Business ID"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date")
):
    """Get financial summary across all revenue sources"""
    db = get_database_service()
    
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get orders (for food & retail)
        orders_result = await db.supabase.table("orders").select("*").eq("business_id", str(business_id)).gte("created_at", start_date.isoformat()).lte("created_at", end_date.isoformat()).execute()
        orders = orders_result.data if orders_result.data else []
        
        # Get invoices (for professional services)
        invoices_result = await db.supabase.table("invoices").select("*").eq("business_id", str(business_id)).gte("issue_date", start_date.date().isoformat()).lte("issue_date", end_date.date().isoformat()).execute()
        invoices = invoices_result.data if invoices_result.data else []
        
        # Get payments
        payments_result = await db.supabase.table("payments").select("*").eq("business_id", str(business_id)).gte("created_at", start_date.isoformat()).lte("created_at", end_date.isoformat()).execute()
        payments = payments_result.data if payments_result.data else []
        
        total_revenue = sum(o.get("total_amount", 0) for o in orders) + sum(i.get("total_amount", 0) for i in invoices if i.get("status") == "paid")
        total_payments = sum(p.get("amount", 0) for p in payments if p.get("status") == "completed")
        
        return {
            "business_id": str(business_id),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_revenue": total_revenue,
                "total_payments": total_payments,
                "total_orders": len(orders),
                "total_invoices": len(invoices),
                "avg_transaction_value": total_revenue / (len(orders) + len(invoices)) if (orders or invoices) else 0
            },
            "breakdown": {
                "orders_revenue": sum(o.get("total_amount", 0) for o in orders),
                "invoices_revenue": sum(i.get("total_amount", 0) for i in invoices if i.get("status") == "paid"),
                "pending_invoices": sum(i.get("amount_due", 0) for i in invoices if i.get("status") in ["sent", "overdue"])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CUSTOMER/CLIENT ANALYTICS
# ============================================================================

@router.get("/customers/insights")
async def get_customer_insights(
    business_id: UUID = Query(..., description="Business ID")
):
    """Get customer/client insights across all categories"""
    db = get_database_service()
    
    try:
        # Try clients table (service-based & professional)
        clients_result = await db.supabase.table("clients").select("*").eq("business_id", str(business_id)).execute()
        clients = clients_result.data if clients_result.data else []
        
        # Try customers table (retail)
        customers_result = await db.supabase.table("customers").select("*").eq("business_id", str(business_id)).execute()
        customers = customers_result.data if customers_result.data else []
        
        total_count = len(clients) + len(customers)
        
        # Calculate metrics
        total_spent_clients = sum(c.get("total_spent", 0) for c in clients)
        total_spent_customers = sum(c.get("total_spent", 0) for c in customers)
        total_spent = total_spent_clients + total_spent_customers
        
        avg_lifetime_value = total_spent / total_count if total_count > 0 else 0
        
        # Active vs inactive
        active_clients = len([c for c in clients if c.get("is_active", True)])
        active_customers = len([c for c in customers if c.get("is_active", True)])
        
        return {
            "business_id": str(business_id),
            "total_customers": total_count,
            "active_customers": active_clients + active_customers,
            "inactive_customers": total_count - (active_clients + active_customers),
            "avg_lifetime_value": avg_lifetime_value,
            "total_revenue": total_spent,
            "breakdown": {
                "service_clients": len(clients),
                "retail_customers": len(customers)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PERFORMANCE ANALYTICS
# ============================================================================

@router.get("/performance/trends")
async def get_performance_trends(
    business_id: UUID = Query(..., description="Business ID"),
    metric: str = Query("revenue", description="Metric to track: revenue, orders, appointments, projects"),
    period: str = Query("30d", description="Period: 7d, 30d, 90d")
):
    """Get performance trends over time"""
    db = get_database_service()
    
    try:
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        trends = []
        
        if metric == "revenue":
            # Get orders
            orders_result = await db.supabase.table("orders").select("created_at, total_amount").eq("business_id", str(business_id)).gte("created_at", start_date.isoformat()).execute()
            orders = orders_result.data if orders_result.data else []
            
            # Group by day
            daily_revenue = {}
            for order in orders:
                date = order.get("created_at", "")[:10]
                daily_revenue[date] = daily_revenue.get(date, 0) + order.get("total_amount", 0)
            
            trends = [{"date": date, "value": amount} for date, amount in sorted(daily_revenue.items())]
        
        elif metric == "appointments":
            appointments_result = await db.supabase.table("appointments").select("scheduled_time").eq("business_id", str(business_id)).gte("scheduled_time", start_date.isoformat()).execute()
            appointments = appointments_result.data if appointments_result.data else []
            
            daily_appointments = {}
            for appt in appointments:
                date = appt.get("scheduled_time", "")[:10]
                daily_appointments[date] = daily_appointments.get(date, 0) + 1
            
            trends = [{"date": date, "value": count} for date, count in sorted(daily_appointments.items())]
        
        return {
            "business_id": str(business_id),
            "metric": metric,
            "period": period,
            "trends": trends,
            "summary": {
                "total": sum(t["value"] for t in trends),
                "average": sum(t["value"] for t in trends) / len(trends) if trends else 0,
                "peak": max((t["value"] for t in trends), default=0)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EXPORT & REPORTING
# ============================================================================

@router.post("/reports/generate")
async def generate_report(
    business_id: UUID = Query(..., description="Business ID"),
    report_type: str = Query("summary", description="Report type: summary, detailed, financial"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Generate comprehensive business report"""
    db = get_database_service()
    
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get business info
        business_result = await db.supabase.table("businesses").select("*").eq("id", str(business_id)).execute()
        
        if not business_result.data:
            raise HTTPException(status_code=404, detail="Business not found")
        
        business = business_result.data[0]
        
        report = {
            "report_id": f"report_{int(datetime.utcnow().timestamp())}",
            "business_id": str(business_id),
            "business_name": business.get("name"),
            "report_type": report_type,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat(),
            "sections": []
        }
        
        # Add financial section
        financial = await get_financial_summary(business_id, start_date, end_date)
        report["sections"].append({
            "name": "Financial Summary",
            "data": financial
        })
        
        # Add customer section
        customer_insights = await get_customer_insights(business_id)
        report["sections"].append({
            "name": "Customer Insights",
            "data": customer_insights
        })
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
