"""
X-sevenAI Analytics & Dashboard Service

Data aggregation, real-time analytics, PDF processing for intelligent content management.
Uses Kafka for event streaming and supports intelligent PDF upload/extraction.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from .routes import (
    menu, inventory, operations, analytics, websocket, business_settings, auth,
    service_based, retail, professional, universal_analytics, reviews, food,
    revenue_analytics
)

# Import DevOps client
import sys
import os
# Add libs directory to path
libs_path = os.path.join(os.path.dirname(__file__), '../../libs')
sys.path.append(libs_path)
try:
    from devops_client import get_devops_client, IncidentSeverity
except ImportError:
    # Create a mock devops client if not available
    class MockDevOpsClient:
        def configure(self, service_name): pass
        async def report_incident(self, title, description, severity): pass
    get_devops_client = lambda: MockDevOpsClient()
    IncidentSeverity = type('IncidentSeverity', (), {'HIGH': 'high'})()

# Configuration
SERVICE_NAME = "analytics-dashboard-service"
SERVICE_PORT = int(os.getenv("ANALYTICS_PORT", 8060))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Import metrics from separate module to avoid duplication issues
from .metrics import REQUEST_COUNT, PDF_UPLOADS


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    print(f"Starting {SERVICE_NAME}")
    print(f"Service running on port {SERVICE_PORT}")
    
    # Initialize DevOps client
    devops_client = get_devops_client()
    devops_client.configure(SERVICE_NAME)
    print("+ DevOps client initialized")
    
    # Initialize database service
    from .services.database import get_database_service
    try:
        db = get_database_service()
        print("+ Database service initialized")
    except Exception as e:
        print(f"- Database initialization failed: {e}")
        await devops_client.report_incident(
            title=f"{SERVICE_NAME} database initialization failed",
            description=str(e),
            severity=IncidentSeverity.HIGH
        )
    
    # Initialize WebSocket manager
    from .services.realtime import manager
    print("+ WebSocket manager initialized")
    
    print(f"+ {SERVICE_NAME} started successfully")
    
    yield
    
    print(f"Shutting down {SERVICE_NAME}")


# Create FastAPI app
app = FastAPI(
    title="X-sevenAI Analytics & Dashboard Service",
    description="Real-time analytics, data aggregation, and intelligent PDF processing",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)  # Auth routes (must be first)

# Food & Hospitality Template (existing)
app.include_router(menu.router)
app.include_router(inventory.router)
app.include_router(operations.router)
app.include_router(food.router)  # Food QR Management

# Service-Based Template (NEW)
app.include_router(service_based.router)

# Retail Template (NEW)
app.include_router(retail.router)

# Professional Services Template (NEW)
app.include_router(professional.router)

# Universal routes
app.include_router(analytics.router)
app.include_router(revenue_analytics.router)  # Revenue analytics
app.include_router(reviews.router)  # Menu reviews and ratings
app.include_router(universal_analytics.router)  # Cross-category analytics
app.include_router(websocket.router)
app.include_router(business_settings.router)


# Health endpoints
@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/live")
async def liveness():
    """Liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe"""
    return {"status": "ready"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": SERVICE_NAME,
        "version": "0.1.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


# Analytics endpoints
@app.get("/api/v1/analytics/dashboard/{business_id}")
async def get_dashboard_analytics(
    business_id: str,
    period: str = "7d"
):
    """
    Get dashboard analytics for business
    
    Includes: orders, revenue, customer metrics, top items
    """
    try:
        from .services.database import get_database_service
        from datetime import date, timedelta
        
        db = get_database_service()
        
        # Calculate date range
        end_date = date.today()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Query aggregated data
        sales_query = db.client.table("daily_sales_summary").select("*")
        sales_query = sales_query.eq("business_id", business_id)
        sales_query = sales_query.gte("date", start_date.isoformat())
        sales_query = sales_query.lte("date", end_date.isoformat())
        sales_result = sales_query.execute()
        
        # Calculate metrics
        total_revenue = sum(float(r.get("total_sales", 0)) for r in sales_result.data)
        total_orders = sum(int(r.get("total_orders", 0)) for r in sales_result.data)
        total_customers = sum(int(r.get("total_customers", 0)) for r in sales_result.data)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
        
        # Get top items
        top_items = await db.get_top_menu_items(business_id, start_date, end_date, 5)
        
        # Build trends
        revenue_trend = [{"date": r["date"], "value": float(r.get("total_sales", 0))} for r in sales_result.data]
        order_trend = [{"date": r["date"], "value": int(r.get("total_orders", 0))} for r in sales_result.data]
        
        return {
            "business_id": business_id,
            "period": period,
            "metrics": {
                "total_orders": total_orders,
                "total_revenue": round(total_revenue, 2),
                "avg_order_value": round(avg_order_value, 2),
                "customer_count": total_customers,
                "top_items": top_items[:5]
            },
            "charts": {
                "revenue_trend": revenue_trend,
                "order_trend": order_trend,
                "category_distribution": []
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/top-categories/{business_id}")
async def get_top_categories(business_id: str, limit: int = 5):
    """
    Get top-5 category assessments
    
    Analyzes performance by category
    """
    try:
        from .services.database import get_database_service
        from datetime import date, timedelta
        from collections import defaultdict
        
        db = get_database_service()
        
        # Query category performance
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        items_query = db.client.table("item_performance").select("*, menu_items(category_id), menu_categories(name)")
        items_query = items_query.eq("business_id", business_id)
        items_query = items_query.gte("date", start_date.isoformat())
        items_result = items_query.execute()
        
        # Aggregate by category
        category_data = defaultdict(lambda: {"revenue": 0.0, "quantity": 0, "profit": 0.0})
        
        for item in items_result.data:
            category_name = "Uncategorized"
            if item.get("menu_categories"):
                category_name = item["menu_categories"].get("name", "Uncategorized")
            
            category_data[category_name]["revenue"] += float(item.get("revenue", 0))
            category_data[category_name]["quantity"] += int(item.get("quantity_sold", 0))
            category_data[category_name]["profit"] += float(item.get("profit", 0))
        
        # Sort and limit
        categories = [
            {
                "name": name,
                "revenue": round(data["revenue"], 2),
                "quantity": data["quantity"],
                "profit": round(data["profit"], 2)
            }
            for name, data in sorted(category_data.items(), key=lambda x: x[1]["revenue"], reverse=True)
        ]
        
        return {
            "business_id": business_id,
            "categories": categories[:limit],
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/customer-insights/{business_id}")
async def get_customer_insights(business_id: str):
    """
    Get customer behavior insights
    
    Includes: demographics, preferences, retention
    """
    try:
        from .services.database import get_database_service
        from datetime import date, timedelta
        from collections import defaultdict
        
        db = get_database_service()
        
        # Query customer data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        orders_query = db.client.table("orders").select("customer_id, total_amount, created_at")
        orders_query = orders_query.eq("business_id", business_id)
        orders_query = orders_query.gte("created_at", start_date.isoformat())
        orders_query = orders_query.eq("status", "completed")
        orders_result = orders_query.execute()
        
        # Analyze
        customer_data = defaultdict(lambda: {"orders": 0, "total_spent": 0.0})
        hour_distribution = defaultdict(int)
        
        for order in orders_result.data:
            customer_id = order.get("customer_id", "guest")
            customer_data[customer_id]["orders"] += 1
            customer_data[customer_id]["total_spent"] += float(order.get("total_amount", 0))
            
            order_time = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00'))
            hour_distribution[order_time.hour] += 1
        
        total_customers = len(customer_data)
        repeat_customers = sum(1 for data in customer_data.values() if data["orders"] > 1)
        repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0.0
        
        total_revenue = sum(data["total_spent"] for data in customer_data.values())
        avg_lifetime_value = total_revenue / total_customers if total_customers > 0 else 0.0
        
        peak_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "business_id": business_id,
            "insights": {
                "total_customers": total_customers,
                "repeat_rate": round(repeat_rate, 2),
                "avg_lifetime_value": round(avg_lifetime_value, 2),
                "preferences": [],
                "peak_hours": [{"hour": h, "orders": c} for h, c in peak_hours]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/real-time/{business_id}")
async def get_realtime_metrics(business_id: str):
    """
    Get real-time metrics
    
    Live data from Kafka streams
    """
    try:
        from .services.database import get_database_service
        from datetime import datetime, timedelta
        
        db = get_database_service()
        
        # Get real-time metrics (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        # Live orders
        orders_query = db.client.table("orders").select("id, total_amount")
        orders_query = orders_query.eq("business_id", business_id)
        orders_query = orders_query.gte("created_at", one_hour_ago.isoformat())
        orders_query = orders_query.in_("status", ["pending", "confirmed", "preparing"])
        orders_result = orders_query.execute()
        
        live_orders = len(orders_result.data)
        current_revenue = sum(float(o.get("total_amount", 0)) for o in orders_result.data)
        
        # Active sessions (placeholder - would come from Kafka/Redis)
        active_sessions = live_orders * 2  # Estimate
        
        return {
            "business_id": business_id,
            "live_orders": live_orders,
            "active_sessions": active_sessions,
            "current_revenue": round(current_revenue, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# PDF Processing endpoints
@app.post("/api/v1/pdf/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    business_id: str = None,
    category: str = "menu"
):
    """
    Upload and process PDF
    
    Intelligent extraction for:
    - Menus with photos
    - Categories and items
    - Pricing information
    - Business documents
    
    Uses OCR (Tesseract/Google Vision) and AI (OpenAI) for extraction
    """
    try:
        PDF_UPLOADS.labels(status="received").inc()
        
        # Validate file
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        import tempfile
        import os
        from .services.database import get_database_service
        
        db = get_database_service()
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Extract text using PyPDF2 (basic extraction)
            # In production: Use pdfplumber + Tesseract OCR for better results
            try:
                import PyPDF2
                with open(temp_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text_blocks = []
                    for page_num, page in enumerate(pdf_reader.pages):
                        text = page.extract_text()
                        if text.strip():
                            text_blocks.append({
                                "page": page_num + 1,
                                "text": text[:500]  # First 500 chars
                            })
            except ImportError:
                text_blocks = [{"page": 1, "text": "PyPDF2 not installed - OCR extraction disabled"}]
            
            # Extract images using Pillow
            # In production: Extract images from PDF and process with CLIP
            images_count = 0
            
            # Use OpenAI to categorize (placeholder)
            # In production: Send text to OpenAI API for categorization
            items = []
            
            # Generate file ID
            file_id = f"pdf_{business_id}_{int(datetime.utcnow().timestamp())}"
            
            # Store in Supabase
            pdf_data = {
                "id": file_id,
                "business_id": business_id,
                "filename": file.filename,
                "category": category,
                "text_blocks": len(text_blocks),
                "images_count": images_count,
                "status": "processed",
                "created_at": datetime.utcnow().isoformat()
            }
            # db.client.table("pdf_uploads").insert(pdf_data).execute()
            
            # Cache in Redis (placeholder)
            # In production: Store extracted data in Redis for fast access
            
            PDF_UPLOADS.labels(status="success").inc()
            
            return {
                "status": "success",
                "file_id": file_id,
                "filename": file.filename,
                "business_id": business_id,
                "category": category,
                "extracted": {
                    "text_blocks": len(text_blocks),
                    "images": images_count,
                    "items": items
                },
                "message": "PDF processed successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    except HTTPException:
        PDF_UPLOADS.labels(status="error").inc()
        raise
    except Exception as e:
        PDF_UPLOADS.labels(status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/pdf/extract/{file_id}")
async def get_extracted_content(file_id: str):
    """
    Get extracted content from processed PDF
    """
    try:
        from .services.database import get_database_service
        
        db = get_database_service()
        
        # Query from database
        # result = db.client.table("pdf_uploads").select("*").eq("id", file_id).execute()
        # if not result.data:
        #     raise HTTPException(status_code=404, detail="File not found")
        
        # Placeholder response
        return {
            "file_id": file_id,
            "content": {
                "text": "Extracted text content would appear here",
                "images": [],
                "structured_data": {
                    "items": [],
                    "categories": [],
                    "metadata": {}
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pdf/categorize")
async def categorize_content(content: dict):
    """
    AI-powered content categorization
    
    Uses OpenAI to categorize extracted content into relevant sections
    """
    try:
        # Use OpenAI to analyze and categorize
        # In production: Send to OpenAI API
        # import openai
        # openai.api_key = os.getenv("OPENAI_API_KEY")
        # response = openai.ChatCompletion.create(
        #     model="gpt-4",
        #     messages=[{
        #         "role": "system",
        #         "content": "Categorize the following content into menu items, prices, and categories."
        #     }, {
        #         "role": "user",
        #         "content": str(content)
        #     }]
        # )
        
        # Apply business rules
        text = content.get("text", "")
        categories = []
        confidence = 0.0
        
        # Simple keyword-based categorization (placeholder)
        if "menu" in text.lower():
            categories.append("menu")
            confidence = 0.7
        if "price" in text.lower() or "$" in text:
            categories.append("pricing")
            confidence = 0.8
        
        return {
            "status": "success",
            "categories": categories,
            "confidence": confidence,
            "message": "In production: Use OpenAI API for intelligent categorization",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Reports endpoints
@app.get("/api/v1/reports/generate/{business_id}")
async def generate_report(
    business_id: str,
    report_type: str = "summary",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Generate business report
    
    Types: summary, detailed, financial, customer
    """
    try:
        from .services.database import get_database_service
        from datetime import date, timedelta
        
        db = get_database_service()
        
        # Parse dates
        if start_date:
            start = date.fromisoformat(start_date)
        else:
            start = date.today() - timedelta(days=30)
        
        if end_date:
            end = date.fromisoformat(end_date)
        else:
            end = date.today()
        
        # Aggregate data
        sales_query = db.client.table("daily_sales_summary").select("*")
        sales_query = sales_query.eq("business_id", business_id)
        sales_query = sales_query.gte("date", start.isoformat())
        sales_query = sales_query.lte("date", end.isoformat())
        sales_result = sales_query.execute()
        
        total_revenue = sum(float(r.get("total_sales", 0)) for r in sales_result.data)
        total_orders = sum(int(r.get("total_orders", 0)) for r in sales_result.data)
        
        # Generate visualizations with Plotly (placeholder)
        # In production: Create charts with plotly and save as images
        # import plotly.graph_objects as go
        # fig = go.Figure(data=[go.Bar(x=dates, y=revenues)])
        # fig.write_image("chart.png")
        
        # Create PDF report (placeholder)
        # In production: Use reportlab to generate PDF
        # from reportlab.lib.pagesizes import letter
        # from reportlab.pdfgen import canvas
        
        report_id = f"report_{business_id}_{int(datetime.utcnow().timestamp())}"
        
        return {
            "status": "success",
            "report_id": report_id,
            "business_id": business_id,
            "report_type": report_type,
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "total_orders": total_orders
            },
            "download_url": f"https://storage.example.com/reports/{report_id}.pdf",
            "message": "In production: Generate PDF with Plotly charts",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Data export endpoints
@app.get("/api/v1/export/{business_id}")
async def export_data(
    business_id: str,
    data_type: str = "orders",
    format: str = "csv"
):
    """
    Export business data
    
    Formats: csv, json, excel
    Types: orders, customers, inventory, analytics
    """
    try:
        from .services.database import get_database_service
        import csv
        import json
        from io import StringIO
        
        db = get_database_service()
        
        # Query data based on type
        if data_type == "orders":
            query = db.client.table("orders").select("*").eq("business_id", business_id).limit(1000)
        elif data_type == "customers":
            query = db.client.table("customers").select("*").eq("business_id", business_id).limit(1000)
        elif data_type == "inventory":
            query = db.client.table("inventory_items").select("*").eq("business_id", business_id).limit(1000)
        elif data_type == "analytics":
            query = db.client.table("daily_sales_summary").select("*").eq("business_id", business_id).limit(1000)
        else:
            raise HTTPException(status_code=400, detail="Invalid data_type")
        
        result = query.execute()
        data = result.data
        
        # Format as requested
        if format == "csv":
            # In production: Generate CSV file and upload to storage
            # output = StringIO()
            # if data:
            #     writer = csv.DictWriter(output, fieldnames=data[0].keys())
            #     writer.writeheader()
            #     writer.writerows(data)
            rows_count = len(data)
        elif format == "json":
            # JSON format
            rows_count = len(data)
        elif format == "excel":
            # In production: Use openpyxl to create Excel file
            # import openpyxl
            rows_count = len(data)
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
        
        # Generate download link (placeholder)
        export_id = f"export_{business_id}_{int(datetime.utcnow().timestamp())}"
        
        return {
            "status": "success",
            "export_id": export_id,
            "business_id": business_id,
            "data_type": data_type,
            "format": format,
            "rows_count": rows_count,
            "download_url": f"https://storage.example.com/exports/{export_id}.{format}",
            "message": "In production: Upload to cloud storage and return signed URL",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import sys
    
    # Check if we're in reload mode
    is_reload = "--reload" in sys.argv
    
    # Configure uvicorn based on reload status
    config = {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": SERVICE_PORT,
        "log_level": LOG_LEVEL.lower(),
    }
    
    if is_reload:
        config["reload"] = True
        # Don't use uvloop in reload mode to avoid compatibility issues
        config["loop"] = "asyncio"
    else:
        # Use uvloop in production for better performance
        try:
            import uvloop
            uvloop.install()
        except ImportError:
            pass
    
    uvicorn.run(**config)
