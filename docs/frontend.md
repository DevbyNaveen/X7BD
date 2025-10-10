# 🎯 Frontend Developer Guide - X-sevenAI Analytics Dashboard Service

## 📋 Table of Contents
- [Overview](#overview)
- [Service Architecture](#service-architecture)
- [Getting Started](#getting-started)
- [API Endpoints Guide](#api-endpoints-guide)
  - [Real-Time Analytics](#real-time-analytics)
  - [Dashboard Analytics](#dashboard-analytics)
  - [Sales Analytics](#sales-analytics)
  - [Menu Analytics](#menu-analytics)
  - [Customer Analytics](#customer-analytics)
  - [Financial Analytics](#financial-analytics)
  - [Operational Analytics](#operational-analytics)
  - [Comparative Analytics](#comparative-analytics)
  - [Forecasting Analytics](#forecasting-analytics)
  - [Report Generation](#report-generation)
  - [Menu Management](#menu-management)
  - [Inventory Management](#inventory-management)
  - [Operations Management](#operations-management)
  - [Business Settings](#business-settings)
  - [Data Export & Import](#data-export--import)
- [Business Types & Features](#business-types--features)
- [Authentication & Security](#authentication--security)
- [Data Structures & Examples](#data-structures--examples)
- [Integration Examples](#integration-examples)
- [Error Handling](#error-handling)
- [Performance & Best Practices](#performance--best-practices)
- [Troubleshooting](#troubleshooting)

---

## 📊 Overview

### What is the Analytics Dashboard Service?
The **X-sevenAI Analytics Dashboard Service** is a comprehensive, enterprise-grade analytics platform designed for food & hospitality businesses. It provides real-time insights, data aggregation, and intelligent analytics for restaurants, cafes, bars, and multi-location operations.

### 🎯 Core Purpose
- **Real-time Business Intelligence**: Live metrics and KPIs
- **Data-Driven Decision Making**: Comprehensive analytics and forecasting
- **Operational Excellence**: Performance monitoring and optimization
- **Financial Intelligence**: Revenue analysis and cost management
- **Customer Insights**: Behavior analysis and personalization

### 🚀 Key Features
- **Multi-Business Type Support**: Restaurant, Cafe, Bar, Salon configurations with modular features
- **Real-time Analytics**: Live data streaming and updates
- **Advanced Forecasting**: Predictive revenue and inventory analysis
- **Comprehensive Reporting**: PDF/Excel reports with charts
- **Data Export**: Multiple formats (JSON, CSV, PDF)
- **Menu Management**: Full CRUD operations with categories, modifiers, and pricing
- **Inventory Management**: Stock tracking, supplier management, and automated reordering
- **Operations Management**: Table management, floor plans, staff scheduling, and KDS
- **Business Settings**: Configurable preferences, notifications, and integrations
- **PDF Intelligence**: AI-powered document processing and extraction

---

## 🏗️ Service Architecture

### Technology Stack
```
FastAPI 0.104.1          # Web Framework
Python 3.11.11           # Runtime
Pydantic 2.5.0           # Data Validation
PostgreSQL 17.6.1        # Database
Supabase                 # Backend-as-a-Service
Redis                    # Caching Layer
Kafka                    # Event Streaming
OpenAI                   # AI Processing
Plotly                   # Data Visualization
```

### Service Components
- **Main Application**: FastAPI server with auto-generated OpenAPI docs
- **Analytics Engine**: Real-time data aggregation and processing
- **PDF Processor**: Intelligent document extraction and categorization
- **Report Generator**: Automated business reporting system
- **Export Service**: Multi-format data export capabilities

### Data Flow
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │────│  Analytics API  │────│   Database      │
│   (React/Vue)   │    │   (FastAPI)     │    │  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Real-time     │
                    │   Processing    │
                    │   (Kafka/Redis) │
                    └─────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.11.11** (recommended)
- **PostgreSQL** database (via Supabase)
- **Redis** for caching (optional)
- **Kafka** for event streaming (optional)

### Environment Setup

#### 1. Virtual Environment
```bash
# Create Python 3.11 virtual environment
python3.11 -m venv .venv

# Activate environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### 2. Environment Variables
Create a `.env` file:
```env
# Service Configuration
ANALYTICS_PORT=8060
LOG_LEVEL=INFO

# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Redis (Optional)
REDIS_URL=redis://localhost:6379

# Kafka (Optional)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# OpenAI (Optional - for PDF processing)
OPENAI_API_KEY=your-openai-key
```

#### 3. Start the Service
```bash
# Activate virtual environment
source .venv/bin/activate

# Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8060 --reload

# Or run the main application
python -m app.main
```

#### 4. Verify Installation
```bash
# Health check
curl http://localhost:8060/health

# API documentation
open http://localhost:8060/docs

# Alternative docs
open http://localhost:8060/redoc
```

### Development Tools
- **Swagger UI**: `http://localhost:8060/docs` - Interactive API testing
- **ReDoc**: `http://localhost:8060/redoc` - Alternative documentation
- **OpenAPI Schema**: `http://localhost:8060/openapi.json` - Machine-readable specs

---

## 📡 API Endpoints Guide

### 🔄 Real-Time Analytics

#### **GET /api/v1/analytics/realtime/{business_id}**
**Purpose**: Get live business metrics and KPIs for immediate decision-making.

**Why this endpoint exists**:
- Provides instant visibility into current business operations
- Enables real-time monitoring of key performance indicators
- Supports operational decision-making during business hours
- Critical for managing daily operations and customer service

**Parameters**:
- `business_id` (UUID): Business identifier
- `location_id` (Optional UUID): Filter by specific location

**Response Example**:
```json
{
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "timestamp": "2025-10-05T01:01:37.000Z",
  "orders": {
    "active": 3,
    "completed_today": 7,
    "pending_kitchen": 2,
    "avg_prep_time": 12.5
  },
  "revenue": {
    "today": 232.87,
    "this_hour": 45.50,
    "avg_order_value": 33.27
  },
  "tables": {
    "total": 15,
    "available": 8,
    "occupied": 6,
    "reserved": 1
  },
  "staff": {
    "clocked_in": 4,
    "on_break": 1,
    "total_hours_today": 28.5
  },
  "inventory": {
    "low_stock_items": 2,
    "out_of_stock_items": 0
  }
}
```

---

### 📊 Dashboard Analytics

#### **GET /api/v1/analytics/dashboard/{business_id}**
**Purpose**: Comprehensive business overview with historical trends and comparisons.

**Why this endpoint exists**:
- Provides holistic view of business performance across all metrics
- Enables trend analysis and performance tracking over time
- Supports strategic decision-making with comprehensive data
- Critical for business owners and managers to understand overall health

**Parameters**:
- `business_id` (UUID): Business identifier
- `period` (string): Time period - `"1d"`, `"7d"`, `"30d"`, `"90d"`, `"1y"`
- `location_id` (Optional UUID): Filter by specific location

**Response Example**:
```json
{
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "period": "7d",
  "timestamp": "2025-10-05T01:01:37.000Z",
  "summary": {
    "total_revenue": 1636.09,
    "total_orders": 49,
    "total_customers": 42,
    "avg_order_value": 33.39,
    "growth_rate": 12.5
  },
  "trends": {
    "revenue": [
      {"date": "2025-09-28", "value": 245.67},
      {"date": "2025-09-29", "value": 267.89},
      {"date": "2025-09-30", "value": 289.12}
    ],
    "orders": [
      {"date": "2025-09-28", "value": 7},
      {"date": "2025-09-29", "value": 8},
      {"date": "2025-09-30", "value": 9}
    ],
    "customers": [
      {"date": "2025-09-28", "value": 6},
      {"date": "2025-09-29", "value": 7},
      {"date": "2025-09-30", "value": 8}
    ]
  },
  "top_performers": {
    "items": [
      {"name": "Ribeye Steak", "revenue": 965.00, "orders": 29},
      {"name": "Grilled Salmon", "revenue": 720.00, "orders": 24}
    ],
    "categories": [
      {"name": "Main Courses", "revenue": 1685.00, "percentage": 65.2},
      {"name": "Appetizers", "revenue": 420.00, "percentage": 16.2}
    ],
    "staff": [
      {"name": "Sarah Johnson", "revenue": 890.00, "orders": 27},
      {"name": "Mike Chen", "revenue": 756.00, "orders": 22}
    ]
  },
  "operational": {
    "avg_table_turnover": 45,
    "avg_prep_time": 12,
    "peak_hours": ["12:00-13:00", "19:00-20:00"]
  }
}
```

---

### 💰 Sales Analytics

#### **GET /api/v1/analytics/sales/summary**
**Purpose**: Detailed sales analysis with time-series data and grouping capabilities.

**Why this endpoint exists**:
- Enables detailed sales performance analysis by different time periods
- Supports operational planning and staffing decisions
- Helps identify peak periods and seasonal trends
- Critical for revenue forecasting and budget planning

**Parameters**:
- `business_id` (UUID): Business identifier
- `start_date` (date): Analysis start date
- `end_date` (date): Analysis end date
- `group_by` (string): Grouping - `"hour"`, `"day"`, `"week"`, `"month"`
- `location_id` (Optional UUID): Filter by specific location

**Response Example**:
```json
{
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "start_date": "2025-09-28",
  "end_date": "2025-10-04",
  "group_by": "day",
  "data": [
    {
      "date": "2025-09-28",
      "revenue": 245.67,
      "orders": 7,
      "customers": 6,
      "avg_order_value": 35.10,
      "peak_hour": "19:00"
    },
    {
      "date": "2025-09-29",
      "revenue": 267.89,
      "orders": 8,
      "customers": 7,
      "avg_order_value": 33.49,
      "peak_hour": "20:00"
    }
  ],
  "totals": {
    "revenue": 1636.09,
    "orders": 49,
    "customers": 42,
    "avg_order_value": 33.39
  }
}
```

#### **GET /api/v1/analytics/sales/by-category**
**Purpose**: Sales breakdown by menu category to understand product performance.

**Why this endpoint exists**:
- Identifies which menu categories drive the most revenue
- Helps with menu optimization and pricing strategies
- Supports inventory planning and supplier decisions
- Critical for understanding customer preferences by category

**Parameters**:
- `business_id` (UUID): Business identifier
- `start_date` (date): Analysis start date
- `end_date` (date): Analysis end date

**Response Example**:
```json
[
  {
    "category_id": "cat-002",
    "category_name": "Main Courses",
    "revenue": 1685.00,
    "orders": 32,
    "percentage": 65.2,
    "avg_order_value": 52.66,
    "top_item": "Ribeye Steak"
  },
  {
    "category_id": "cat-001",
    "category_name": "Appetizers",
    "revenue": 420.00,
    "orders": 12,
    "percentage": 16.2,
    "avg_order_value": 35.00,
    "top_item": "Caesar Salad"
  }
]
```

---

### 🍽️ Menu Analytics

#### **GET /api/v1/analytics/menu/top-items**
**Purpose**: Identify best-performing menu items by revenue, quantity, or profit.

**Why this endpoint exists**:
- Enables data-driven menu optimization and pricing
- Helps identify star performers and underperformers
- Supports inventory management and supplier relationships
- Critical for menu engineering and profitability analysis

**Parameters**:
- `business_id` (UUID): Business identifier
- `start_date` (date): Analysis start date
- `end_date` (date): Analysis end date
- `metric` (string): Ranking metric - `"revenue"`, `"quantity"`, `"profit"`
- `limit` (int): Number of items to return (1-50)

**Response Example**:
```json
[
  {
    "item_id": "item-002",
    "item_name": "Ribeye Steak",
    "category_name": "Main Courses",
    "revenue": 965.00,
    "quantity_sold": 29,
    "profit_margin": 35.2,
    "avg_price": 33.28,
    "rank": 1,
    "trend": "up"
  },
  {
    "item_id": "item-003",
    "item_name": "Grilled Salmon",
    "category_name": "Main Courses",
    "revenue": 720.00,
    "quantity_sold": 24,
    "profit_margin": 42.1,
    "avg_price": 30.00,
    "rank": 2,
    "trend": "stable"
  }
]
```

#### **GET /api/v1/analytics/menu/profit-analysis**
**Purpose**: Comprehensive menu profitability analysis with recommendations.

**Why this endpoint exists**:
- Provides detailed profit margin analysis across menu items
- Helps optimize pricing and cost management strategies
- Identifies opportunities for menu improvement and cost reduction
- Critical for maximizing profitability while maintaining quality

**Parameters**:
- `business_id` (UUID): Business identifier
- `start_date` (date): Analysis start date
- `end_date` (date): Analysis end date

**Response Example**:
```json
{
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "overall_margin": 38.7,
  "high_margin_items": [
    {
      "item_name": "Grilled Salmon",
      "margin": 42.1,
      "revenue": 720.00,
      "recommendation": "Maintain pricing"
    }
  ],
  "low_margin_items": [
    {
      "item_name": "Caesar Salad",
      "margin": 25.3,
      "revenue": 420.00,
      "recommendation": "Consider price increase or cost reduction"
    }
  ],
  "recommendations": [
    "Increase prices on low-margin items by 5-10%",
    "Negotiate better supplier terms for high-volume ingredients",
    "Consider removing items with margins below 20%"
  ]
}
```

#### **GET /api/v1/analytics/sales/by-payment-method**
**Purpose**: Analyze sales by payment method to understand customer payment preferences.

**Why this endpoint exists**:
- Tracks payment method adoption and trends
- Helps with payment processing fee optimization
- Supports cash flow analysis by payment type

**Parameters**:
- `business_id` (UUID): Business identifier
- `start_date` (date): Analysis start date
- `end_date` (date): Analysis end date

**Response Example**:
```json
{
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "payment_methods": {
    "card": {
      "amount": 2156.78,
      "percentage": 75.2,
      "transactions": 45
    },
    "cash": {
      "amount": 456.23,
      "percentage": 15.9,
      "transactions": 12
    },
    "digital_wallet": {
      "amount": 234.56,
      "percentage": 8.2,
      "transactions": 6
    }
  }
}
```

---

### 👥 Customer Analytics

#### **GET /api/v1/analytics/customers/insights**
**Purpose**: Comprehensive customer behavior and demographics analysis.

**Why this endpoint exists**:
- Provides deep understanding of customer preferences and patterns
- Enables personalized marketing and service improvements
- Helps with customer retention and loyalty programs
- Critical for understanding customer lifetime value and behavior

**Parameters**:
- `business_id` (UUID): Business identifier
- `start_date` (date): Analysis start date
- `end_date` (date): Analysis end date

**Response Example**:
```json
{
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "total_customers": 42,
  "new_customers": 12,
  "repeat_customers": 30,
  "repeat_rate": 71.4,
  "avg_lifetime_value": 156.89,
  "peak_hours": [
    "12:00-13:00",
    "19:00-20:00",
    "20:00-21:00"
  ],
  "popular_items": [
    "Ribeye Steak",
    "Grilled Salmon",
    "Caesar Salad"
  ],
  "demographics": {
    "avg_party_size": 2.3,
    "preferred_days": ["Friday", "Saturday", "Sunday"],
    "spending_brackets": {
      "$25-50": 45,
      "$50-100": 35,
      "$100+": 20
    }
  }
}
```

#### **GET /api/v1/analytics/customers/cohort-analysis**
**Purpose**: Customer cohort analysis for retention tracking.

**Why this endpoint exists**:
- Measures customer retention over time
- Identifies when customers stop returning
- Helps optimize customer acquisition and retention strategies

**Parameters**:
- `business_id` (UUID): Business identifier
- `cohort_type` (string): "weekly" or "monthly" analysis

**Response Example**:
```json
{
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "cohorts": [
    {
      "cohort": "2025-09",
      "size": 15,
      "retention": {
        "month_1": 80.0,
        "month_2": 65.0,
        "month_3": 55.0
      }
    }
  ]
}
```

---

### 💳 Financial Analytics

#### **GET /api/v1/analytics/financial/summary**
**Purpose**: Complete financial overview including revenue, costs, and profitability.

**Why this endpoint exists**:
- Provides comprehensive financial health assessment
- Enables cost control and profitability optimization
- Supports financial planning and budgeting decisions
- Critical for business owners to understand financial performance

**Parameters**:
- `business_id` (UUID): Business identifier
- `start_date` (date): Analysis start date
- `end_date` (date): Analysis end date

**Response Example**:
```json
{
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "revenue": {
    "total": 2589.00,
    "by_category": {
      "Main Courses": 1685.00,
      "Appetizers": 420.00,
      "Desserts": 324.00,
      "Beverages": 160.00
    }
  },
  "costs": {
    "cogs": 642.25,
    "labor": 387.00,
    "overhead": 195.00
  },
  "profit": {
    "gross": 1926.75,
    "net": 1344.75
  },
  "margins": {
    "gross_margin": 74.4,
    "net_margin": 51.9
  },
  "period_comparison": {
    "previous_period": 2156.00,
    "growth": 20.1
  }
}
```

---

### ⚙️ Operational Analytics

#### **GET /api/v1/analytics/operations/table-turnover**
**Purpose**: Analyze table turnover rates and operational efficiency.

**Why this endpoint exists**:
- Measures operational efficiency and table utilization
- Helps optimize seating capacity and service flow
- Supports staffing and scheduling decisions
- Critical for maximizing revenue per table

**Parameters**:
- `business_id` (UUID): Business identifier
- `start_date` (date): Analysis start date
- `end_date` (date): Analysis end date
- `location_id` (Optional UUID): Filter by specific location

**Response Example**:
```json
{
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "avg_turnover_minutes": 45,
  "by_time_of_day": {
    "lunch": 35,
    "dinner": 55,
    "weekend": 65
  },
  "by_table": [
    {
      "table_number": "T1",
      "turnover_minutes": 42,
      "utilization_rate": 85.7,
      "avg_party_size": 2.1
    }
  ],
  "recommendations": [
    "Increase turnover during peak dinner hours",
    "Consider table sharing for larger parties",
    "Optimize server assignments for faster service"
  ]
}
```

---

### 📊 Comparative Analytics

#### **GET /api/v1/analytics/compare/period-over-period**
**Purpose**: Compare business performance across different time periods.

**Why this endpoint exists**:
- Enables trend analysis and growth measurement
- Helps identify seasonal patterns and anomalies
- Supports performance benchmarking and goal setting
- Critical for understanding business trajectory and planning

**Parameters**:
- `business_id` (UUID): Business identifier
- `current_start` (date): Current period start date
- `current_end` (date): Current period end date
- `comparison_type` (string): Comparison type - `"previous"`, `"year_ago"`

**Response Example**:
```json
{
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "current_period": {
    "start_date": "2025-09-28",
    "end_date": "2025-10-04",
    "revenue": 1636.09,
    "orders": 49,
    "customers": 42
  },
  "comparison_period": {
    "start_date": "2025-09-21",
    "end_date": "2025-09-27",
    "revenue": 1456.00,
    "orders": 43,
    "customers": 38
  },
  "growth_rates": {
    "revenue": 12.4,
    "orders": 14.0,
    "customers": 10.5,
    "avg_order_value": -1.4
  },
  "insights": [
    "Strong revenue growth of 12.4%",
    "Customer acquisition improved by 10.5%",
    "Average order value slightly declined"
  ]
}
```

---

### 🔮 Forecasting Analytics

#### **GET /api/v1/analytics/forecast/revenue**
**Purpose**: Predictive revenue forecasting for planning and budgeting.

**Why this endpoint exists**:
- Enables proactive business planning and resource allocation
- Helps with staffing, inventory, and marketing decisions
- Supports financial forecasting and budget planning
- Critical for anticipating future business needs and opportunities

**Parameters**:
- `business_id` (UUID): Business identifier
- `forecast_days` (int): Number of days to forecast (1-365)

**Response Example**:
```json
{
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "forecast": [
    {
      "date": "2025-10-05",
      "predicted_revenue": 267.89,
      "confidence_interval": {
        "low": 234.56,
        "high": 301.23
      },
      "confidence_level": 85.0,
      "factors": ["Saturday", "Good weather", "Marketing campaign"]
    }
  ],
  "overall_trend": "stable",
  "accuracy_score": 87.5
}
```

#### **GET /api/v1/analytics/forecast/inventory-needs**
**Purpose**: Inventory needs forecasting for optimal stock levels.

**Why this endpoint exists**:
- Predicts future inventory requirements
- Reduces stockouts and overstock situations
- Optimizes inventory carrying costs
- Supports supplier ordering schedules

**Parameters**:
- `business_id` (UUID): Business identifier
- `forecast_days` (int): Number of days to forecast (1-30)

**Response Example**:
```json
{
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "recommendations": [
    {
      "item_name": "Tomatoes",
      "current_stock": 25.5,
      "predicted_usage": 15.2,
      "recommended_order": 20.0,
      "optimal_reorder_date": "2025-10-08"
    }
  ]
}
```

---

### 📋 Report Generation

#### **POST /api/v1/analytics/reports/generate**
**Purpose**: Generate comprehensive business reports with charts and visualizations.

**Why this endpoint exists**:
- Provides professional reporting capabilities for stakeholders
- Enables automated report distribution and scheduling
- Supports compliance and audit requirements
- Critical for communicating business performance to investors and management

**Parameters**:
- `business_id` (UUID): Business identifier
- `report_type` (string): Report type - `"daily"`, `"weekly"`, `"monthly"`, `"custom"`
- `start_date` (Optional date): Custom report start date
- `end_date` (Optional date): Custom report end date
- `include_charts` (bool): Include visualizations in report
- `format` (string): Output format - `"pdf"`, `"excel"`, `"json"`

**Response Example**:
```json
{
  "report_id": "report_1736092896",
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "report_type": "weekly",
  "format": "pdf",
  "status": "generating",
  "estimated_completion": "2025-10-05T01:02:00.000Z",
  "download_url": null,
  "sections": [
    "Executive Summary",
    "Revenue Analysis",
    "Customer Insights",
    "Menu Performance",
    "Operational Metrics",
    "Financial Overview"
  ]
}
```

---

### 📤 Data Export

#### **GET /api/v1/export/{business_id}**
**Purpose**: Export business data in various formats for external analysis.

**Why this endpoint exists**:
- Enables integration with external business intelligence tools
- Supports data backup and compliance requirements
- Allows advanced analysis using specialized tools
- Critical for accounting software integration and financial reporting

**Parameters**:
- `business_id` (UUID): Business identifier
- `data_type` (string): Data to export - `"orders"`, `"customers"`, `"menu"`, `"analytics"`
- `format` (string): Output format - `"json"`, `"csv"`, `"pdf"`
- `start_date` (Optional date): Date range start
- `end_date` (Optional date): Date range end

**Response Example**:
```json
{
  "status": "success",
  "business_id": "6539a901-5bdc-447f-9e43-6fbbc10ce63d",
  "data_type": "orders",
  "format": "json",
  "record_count": 49,
  "file_size": "2.3MB",
  "download_url": "https://api.x-sevenai.com/downloads/export_1736092896.json",
  "expires_at": "2025-10-05T02:01:36.000Z",
  "columns": [
    "order_id",
    "customer_id",
    "order_date",
    "total_amount",
    "items",
    "status"
  ]
}
```

---

### 🍽️ Menu Management

#### **POST /api/v1/menu/categories**
**Purpose**: Create menu categories with hierarchical support.

**Why this endpoint exists**:
- Enables structured menu organization with parent-child relationships
- Supports complex menu hierarchies for different dining experiences
- Allows category-based analytics and reporting

**Request Body**:
```json
{
  "business_id": "uuid",
  "name": "Main Courses",
  "description": "Primary dining options",
  "parent_id": "uuid",  // optional for subcategories
  "display_order": 1,
  "icon_url": "string",  // optional
  "is_active": true
}
```

#### **GET /api/v1/menu/categories**
**Purpose**: List menu categories with filtering.

**Parameters**:
- `business_id` (UUID): Business identifier
- `parent_id` (Optional UUID): Filter by parent category
- `is_active` (Optional bool): Filter by active status

#### **POST /api/v1/menu/items**
**Purpose**: Create menu items with full customization.

**Why this endpoint exists**:
- Supports comprehensive menu item management
- Enables pricing strategies and inventory tracking
- Allows location-specific and time-based availability

**Request Body**:
```json
{
  "business_id": "uuid",
  "category_id": "uuid",
  "name": "Ribeye Steak",
  "description": "Premium cut with garlic butter",
  "price": 45.99,
  "cost": 18.50,
  "modifiers": ["uuid1", "uuid2"],
  "is_available": true,
  "locations": ["uuid1"],
  "tags": ["premium", "beef"]
}
```

#### **GET /api/v1/menu/items**
**Purpose**: List menu items with advanced filtering and search.

**Parameters**:
- `business_id` (UUID): Business identifier
- `category_id` (Optional UUID): Filter by category
- `is_available` (Optional bool): Filter by availability
- `search` (Optional string): Full-text search
- `limit` (int): Pagination limit (1-100)
- `offset` (int): Pagination offset

#### **PUT /api/v1/menu/items/{item_id}**
**Purpose**: Update menu item with partial updates.

**Why this endpoint exists**:
- Allows flexible menu updates without full replacement
- Supports price changes and availability toggling
- Enables real-time menu modifications

#### **POST /api/v1/menu/modifiers**
**Purpose**: Create item modifiers (toppings, sizes, customizations).

**Why this endpoint exists**:
- Supports complex menu customization options
- Enables upselling through modifier pricing
- Allows flexible menu configuration

**Request Body**:
```json
{
  "business_id": "uuid",
  "name": "Cooking Temperature",
  "type": "single",  // "single" or "multiple"
  "required": true,
  "options": [
    {"name": "Rare", "price": 0.0, "is_default": false},
    {"name": "Medium Rare", "price": 0.0, "is_default": true},
    {"name": "Medium", "price": 0.0, "is_default": false}
  ]
}
```

---

### 📦 Inventory Management

#### **POST /api/v1/inventory/items**
**Purpose**: Create inventory items with stock tracking.

**Why this endpoint exists**:
- Enables automated inventory management
- Supports cost tracking and profit margin calculations
- Allows multi-location inventory management

**Request Body**:
```json
{
  "business_id": "uuid",
  "name": "Tomatoes",
  "category": "Produce",
  "unit": "lbs",
  "current_stock": 25.5,
  "min_stock": 10.0,
  "max_stock": 50.0,
  "unit_cost": 2.50,
  "supplier_id": "uuid",
  "location_id": "uuid"
}
```

#### **GET /api/v1/inventory/items**
**Purpose**: List inventory items with metrics and alerts.

**Why this endpoint exists**:
- Provides real-time inventory visibility
- Enables proactive reordering based on stock levels
- Supports multi-location inventory tracking

**Response includes**:
```json
{
  "id": "uuid",
  "name": "Tomatoes",
  "current_stock": 25.5,
  "stock_percentage": 51.0,
  "needs_reorder": false,
  "stock_value": 63.75,
  "days_of_stock": 7
}
```

#### **POST /api/v1/inventory/transactions**
**Purpose**: Record inventory transactions (in/out/adjustments).

**Why this endpoint exists**:
- Maintains accurate inventory audit trails
- Supports cost accounting and waste tracking
- Enables inventory turnover analysis

#### **POST /api/v1/inventory/purchase-orders**
**Purpose**: Create purchase orders for suppliers.

**Why this endpoint exists**:
- Streamlines supplier ordering process
- Reduces stockouts through automated reordering
- Enables supplier performance tracking

---

### 🏢 Operations Management

#### **POST /api/v1/operations/locations**
**Purpose**: Create business locations for multi-location operations.

**Why this endpoint exists**:
- Supports multi-location business management
- Enables location-specific analytics and operations
- Allows centralized control of distributed operations

#### **POST /api/v1/operations/tables**
**Purpose**: Manage table configurations and assignments.

**Why this endpoint exists**:
- Optimizes seating capacity and turnover
- Enables table management and reservations
- Supports operational efficiency metrics

#### **GET /api/v1/operations/kds/orders**
**Purpose**: Kitchen Display System order management.

**Why this endpoint exists**:
- Streamlines kitchen operations and order flow
- Reduces wait times and improves service quality
- Enables real-time kitchen performance monitoring

#### **POST /api/v1/operations/staff**
**Purpose**: Staff member management and scheduling.

**Why this endpoint exists**:
- Supports workforce management and scheduling
- Enables labor cost tracking and optimization
- Allows staff performance analysis

#### **POST /api/v1/operations/time-clock**
**Purpose**: Time clock functionality for staff attendance.

**Why this endpoint exists**:
- Ensures accurate payroll processing
- Supports compliance with labor regulations
- Enables workforce analytics and planning

---

### ⚙️ Business Settings

#### **GET /api/v1/business-settings/{business_id}**
**Purpose**: Retrieve business configuration and preferences.

**Why this endpoint exists**:
- Supports customizable business operations
- Enables location-specific and business-type-specific features
- Allows user preference management

**Response includes**:
```json
{
  "business_id": "uuid",
  "notifications": {
    "email": true,
    "sms": false,
    "push": true
  },
  "preferences": {
    "locale": "en-US",
    "currency": "USD",
    "timezone": "UTC",
    "date_format": "MM/DD/YYYY"
  },
  "business_hours": [...],
  "integrations": {...}
}
```

#### **PUT /api/v1/business-settings/{business_id}**
**Purpose**: Update business settings and preferences.

**Why this endpoint exists**:
- Allows businesses to customize their experience
- Supports integration configuration
- Enables operational preference management

---

### 📤 Data Export & Import

#### **GET /api/v1/export/{business_id}**
**Purpose**: Export business data in multiple formats.

**Why this endpoint exists**:
- Enables data portability and backup
- Supports integration with external systems
- Allows advanced analysis with specialized tools

**Parameters**:
- `business_id` (UUID): Business identifier
- `data_type` (string): "orders", "customers", "menu", "analytics"
- `format` (string): "json", "csv", "pdf"
- `start_date` (Optional date): Date range start
- `end_date` (Optional date): Date range end

#### **POST /api/v1/menu/import**
**Purpose**: Import menu data from external sources.

**Why this endpoint exists**:
- Streamlines menu setup and migration
- Supports integration with menu management software
- Enables bulk menu operations

**Supported sources**: PDF, CSV, JSON, Toast, DoorDash

#### **GET /api/v1/menu/export/{business_id}**
**Purpose**: Export menu data for backup or integration.

**Why this endpoint exists**:
- Supports menu backup and recovery
- Enables integration with POS systems
- Allows menu sharing and replication

---

## 🏢 Business Types & Features

### Modular Feature System
The analytics dashboard supports multiple business types with configurable, modular features. Each business type enables specific functionality based on operational needs.

### Restaurant Configuration
```json
{
  "type": "restaurant",
  "features": [
    "table_management",
    "kitchen_tracking",
    "reservation_system",
    "multi_course_menus",
    "table_turnover_analysis",
    "kds_orders",
    "staff_scheduling",
    "menu_modifiers"
  ],
  "analytics_focus": [
    "dining_experience",
    "service_efficiency",
    "menu_performance",
    "peak_hours_management",
    "table_utilization"
  ]
}
```

### Cafe Configuration
```json
{
  "type": "cafe",
  "features": [
    "quick_service",
    "beverage_focus",
    "pastry_management",
    "takeout_orders",
    "customer_loyalty",
    "inventory_tracking",
    "simple_menu_structure"
  ],
  "analytics_focus": [
    "beverage_performance",
    "customer_frequency",
    "peak_hours",
    "inventory_turnover",
    "takeout_vs_dine_in"
  ]
}
```

### Bar Configuration
```json
{
  "type": "bar",
  "features": [
    "cocktail_menu",
    "happy_hour_management",
    "capacity_tracking",
    "entertainment_events",
    "age_verification",
    "drink_modifiers",
    "bottle_service"
  ],
  "analytics_focus": [
    "drink_preferences",
    "revenue_per_seat",
    "event_performance",
    "customer_demographics",
    "time_based_pricing"
  ]
}
```

### Salon/Spa Configuration
```json
{
  "type": "salon",
  "features": [
    "appointment_booking",
    "service_management",
    "staff_specializations",
    "client_profiles",
    "loyalty_programs",
    "treatment_tracking"
  ],
  "analytics_focus": [
    "service_popularity",
    "staff_performance",
    "client_retention",
    "appointment_utilization",
    "treatment_margins"
  ]
}
```

### Feature Modules
- **Menu Management**: Categories, items, modifiers, pricing
- **Inventory Control**: Stock tracking, reordering, supplier management
- **Operations**: Tables, floor plans, staff scheduling, KDS
- **Customer Management**: Profiles, loyalty, preferences
- **Financial Analytics**: Profit margins, cost analysis, forecasting
- **Reporting**: Custom reports, exports, scheduled delivery

---

## 🔐 Authentication & Security

### API Key Authentication
```javascript
// Include API key in headers
const headers = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type': 'application/json'
};

fetch('/api/v1/analytics/dashboard/business-id', {
  headers: headers
});
```

### Row Level Security (RLS)
- All data access is automatically filtered by business ownership
- Users can only access data for businesses they own/manage
- Automatic tenant isolation prevents data leakage

### Rate Limiting
- **Standard**: 1000 requests/hour per business
- **Premium**: 10,000 requests/hour per business
- **Enterprise**: Unlimited with monitoring

---

## 💻 Integration Examples

### React Dashboard Component
```javascript
import { useState, useEffect } from 'react';

function AnalyticsDashboard({ businessId }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, [businessId]);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(
        `/api/v1/analytics/dashboard/${businessId}?period=7d`
      );
      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      <h2>Revenue: ${dashboardData.summary.total_revenue}</h2>
      <h3>Orders: {dashboardData.summary.total_orders}</h3>
      {/* Render charts and metrics */}
    </div>
  );
}
```

---

## 🚨 Error Handling

### Common HTTP Status Codes

| Status Code | Meaning | Action Required |
|-------------|---------|-----------------|
| **200** | Success | No action needed |
| **400** | Bad Request | Check request parameters |
| **401** | Unauthorized | Verify API key |
| **403** | Forbidden | Check business ownership |
| **404** | Not Found | Verify endpoint/business ID |
| **422** | Validation Error | Check parameter formats |
| **429** | Rate Limited | Implement backoff strategy |
| **500** | Server Error | Contact support |

### Error Response Format
```json
{
  "detail": "Business not found",
  "error_code": "BUSINESS_NOT_FOUND",
  "timestamp": "2025-10-05T01:01:37.000Z",
  "request_id": "req_123456789"
}
```

---

## ⚡ Performance & Best Practices

### Response Time Guidelines
- **Real-time endpoints**: < 50ms (critical for live updates)
- **Dashboard endpoints**: < 200ms (user experience)
- **Analytics queries**: < 500ms (data analysis)
- **Report generation**: < 30 seconds (background processing)

### Caching Strategies
```javascript
// Cache dashboard data for 5 minutes
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

const getCachedDashboard = async (businessId) => {
  const cacheKey = `dashboard_${businessId}`;
  const cached = localStorage.getItem(cacheKey);
  
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp < CACHE_DURATION) {
      return data;
    }
  }
  
  const freshData = await apiCall(`/api/v1/analytics/dashboard/${businessId}`);
  localStorage.setItem(cacheKey, JSON.stringify({
    data: freshData,
    timestamp: Date.now()
  }));
  
  return freshData;
};
```

---

## 🔧 Troubleshooting

### Common Issues

#### **"Business not found" error**
**Cause**: Invalid business ID or access permissions
**Solution**:
```javascript
// Verify business ID format
const isValidUUID = (id) => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(id);
};
```

#### **Rate limiting errors**
**Cause**: Too many requests in short time period
**Solution**:
```javascript
class RateLimiter {
  constructor(requestsPerMinute = 60) {
    this.requests = [];
    this.maxRequests = requestsPerMinute;
  }

  async makeRequest(endpoint, options = {}) {
    const now = Date.now();
    
    // Remove old requests
    this.requests = this.requests.filter(time => 
      now - time < 60000
    );
    
    if (this.requests.length >= this.maxRequests) {
      const waitTime = 60000 - (now - this.requests[0]);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
    
    this.requests.push(now);
    return apiCall(endpoint, options);
  }
}
```

---

## 📞 Support & Resources

### Documentation Links
- **API Reference**: `http://localhost:8060/docs`
- **OpenAPI Spec**: `http://localhost:8060/openapi.json`
- **Health Check**: `http://localhost:8060/health`

### Business Types Guide
- **Restaurant Setup**: Table management, kitchen tracking
- **Cafe Configuration**: Quick service, beverage focus
- **Bar Operations**: Cocktail menus, capacity tracking

---

## 🎯 Next Steps

1. **Start Integration**: Use the provided examples to connect your frontend
2. **Test Endpoints**: Begin with health check and basic dashboard endpoints
3. **Implement Caching**: Add client-side caching for better performance
4. **Add Real-time**: Implement WebSocket connections for live updates
5. **Handle Errors**: Implement comprehensive error handling and retry logic
6. **Optimize Performance**: Use batch calls and smart polling strategies

---

**🚀 Ready to build amazing analytics dashboards with real business intelligence!**

The X-sevenAI Analytics Dashboard Service provides enterprise-grade analytics capabilities with comprehensive real-time insights, predictive forecasting, and intelligent automation. Every endpoint is designed for production use with robust error handling, performance optimization, and business-critical reliability.
