# Business Dashboard API Documentation

## Overview

The X-sevenAI Business Dashboard is a comprehensive analytics platform that provides real-time business insights, operational management, and data-driven decision making capabilities. It aggregates data from multiple microservices to deliver actionable metrics for business owners.

## Architecture

The dashboard ecosystem consists of 4 interconnected microservices:

1. **analytics-dashboard-service** - Core dashboard functionality and analytics
2. **business-logic-service** - Operational business logic (orders, reservations, inventory)
3. **auth-service** - User and business management, authentication
4. **api-gateway** - Centralized routing, authentication, and rate limiting

All services communicate via REST APIs with JWT authentication, use Supabase for data persistence, and Kafka for event streaming.

## Service Endpoints

### analytics-dashboard-service

**Base URL**: `http://analytics-dashboard-service:8050`  
**Port**: 8050  
**Purpose**: Provides core dashboard analytics, PDF processing, reporting, and data export capabilities.

#### Health & Status Endpoints

##### GET /health
**Description**: Health check endpoint for monitoring service availability.  
**Why needed**: Enables load balancers and monitoring systems to verify service health.  
**How it works**: Returns basic health status with service name and timestamp.  
**Response**:
```json
{
  "status": "healthy",
  "service": "analytics-dashboard-service",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

##### GET /health/live
**Description**: Kubernetes liveness probe.  
**Why needed**: Container orchestration uses this to determine if the service should be restarted.  
**Response**: `{"status": "alive"}`

##### GET /health/ready
**Description**: Kubernetes readiness probe.  
**Why needed**: Ensures service is ready to accept traffic before routing requests.  
**Response**: `{"status": "ready"}`

##### GET /
**Description**: Root endpoint providing basic service information.  
**Why needed**: Service discovery and basic API information.  
**Response**:
```json
{
  "service": "analytics-dashboard-service",
  "version": "0.1.0",
  "status": "running",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Analytics Endpoints

##### GET /api/v1/analytics/dashboard/{business_id}
**Description**: Retrieves comprehensive dashboard analytics for a business.  
**Parameters**:
- `business_id` (path): UUID of the business
- `period` (query, optional): Time period (default: "7d")  
**Why needed**: Provides the main dashboard view with key performance indicators.  
**How it works**: Aggregates data from Supabase, calculates metrics, generates chart data. Currently returns placeholder data.  
**Response**:
```json
{
  "business_id": "uuid",
  "period": "7d",
  "metrics": {
    "total_orders": 0,
    "total_revenue": 0.0,
    "avg_order_value": 0.0,
    "customer_count": 0,
    "top_items": []
  },
  "charts": {
    "revenue_trend": [],
    "order_trend": [],
    "category_distribution": []
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

##### GET /api/v1/analytics/top-categories/{business_id}
**Description**: Analyzes and returns top-performing product/service categories.  
**Parameters**:
- `business_id` (path): Business UUID
- `limit` (query, optional): Number of categories to return (default: 5)  
**Why needed**: Helps businesses identify their best-selling categories for inventory optimization.  
**How it works**: Queries category performance data and ranks by metrics. Currently returns placeholder.  
**Response**:
```json
{
  "business_id": "uuid",
  "categories": [],
  "limit": 5,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

##### GET /api/v1/analytics/customer-insights/{business_id}
**Description**: Provides customer behavior and demographic insights.  
**Parameters**: `business_id` (path): Business UUID  
**Why needed**: Enables customer retention strategies and personalized marketing.  
**How it works**: Analyzes customer transaction patterns, preferences, and engagement data.  
**Response**:
```json
{
  "business_id": "uuid",
  "insights": {
    "total_customers": 0,
    "repeat_rate": 0.0,
    "avg_lifetime_value": 0.0,
    "preferences": [],
    "peak_hours": []
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

##### GET /api/v1/analytics/real-time/{business_id}
**Description**: Delivers real-time business metrics.  
**Parameters**: `business_id` (path): Business UUID  
**Why needed**: Provides live operational visibility for immediate decision making.  
**How it works**: Streams data from Kafka event bus for live orders and sessions. Currently returns placeholder.  
**Response**:
```json
{
  "business_id": "uuid",
  "live_orders": 0,
  "active_sessions": 0,
  "current_revenue": 0.0,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### PDF Processing Endpoints

##### POST /api/v1/pdf/upload
**Description**: Uploads and processes PDF documents (menus, catalogs, business docs).  
**Parameters**:
- `file` (form): PDF file upload
- `business_id` (form, optional): Associated business UUID
- `category` (form, optional): Document category (default: "menu")  
**Why needed**: Automates data ingestion from business documents using AI.  
**How it works**: Uses OCR (Tesseract), image extraction (Pillow), and OpenAI for content categorization. Stores in Supabase with Redis caching.  
**Response**:
```json
{
  "status": "success",
  "file_id": "pdf_1234567890",
  "filename": "menu.pdf",
  "business_id": "uuid",
  "category": "menu",
  "extracted": {
    "text_blocks": 0,
    "images": 0,
    "items": []
  },
  "message": "PDF processed successfully",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

##### GET /api/v1/pdf/extract/{file_id}
**Description**: Retrieves extracted content from processed PDFs.  
**Parameters**: `file_id` (path): PDF processing ID  
**Why needed**: Provides access to structured data extracted from documents.  
**How it works**: Queries Supabase for processed PDF content.  
**Response**:
```json
{
  "file_id": "pdf_1234567890",
  "content": {
    "text": "",
    "images": [],
    "structured_data": {}
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

##### POST /api/v1/pdf/categorize
**Description**: AI-powered content categorization of extracted text.  
**Parameters**: `content` (body): JSON content to categorize  
**Why needed**: Automatically organizes extracted data into meaningful business categories.  
**How it works**: Uses OpenAI to analyze and categorize content based on business rules.  
**Response**:
```json
{
  "status": "success",
  "categories": [],
  "confidence": 0.0,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Reports & Export Endpoints

##### GET /api/v1/reports/generate/{business_id}
**Description**: Generates business reports (summary, detailed, financial, customer).  
**Parameters**:
- `business_id` (path): Business UUID
- `report_type` (query, optional): Type of report (default: "summary")
- `start_date` (query, optional): Report start date
- `end_date` (query, optional): Report end date  
**Why needed**: Provides downloadable business intelligence reports.  
**How it works**: Aggregates data, generates visualizations with Plotly, creates PDF reports. Currently returns placeholder download URL.  
**Response**:
```json
{
  "status": "success",
  "report_id": "report_1234567890",
  "business_id": "uuid",
  "report_type": "summary",
  "download_url": "https://example.com/report.pdf",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

##### GET /api/v1/export/{business_id}
**Description**: Exports business data in various formats.  
**Parameters**:
- `business_id` (path): Business UUID
- `data_type` (query, optional): Data type (default: "orders")
- `format` (query, optional): Export format (default: "csv")  
**Why needed**: Enables data portability and external analysis.  
**How it works**: Queries business data and formats as CSV/JSON/Excel. Currently returns placeholder download URL.  
**Response**:
```json
{
  "status": "success",
  "business_id": "uuid",
  "data_type": "orders",
  "format": "csv",
  "download_url": "https://example.com/export.csv",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### business-logic-service

**Base URL**: `http://business-logic-service:8030`  
**Port**: 8030  
**Purpose**: Handles core business operations and workflows.

#### Health Endpoints (same as analytics-dashboard-service)
- `GET /health`, `GET /health/live`, `GET /health/ready`, `GET /`

#### Order Management

##### POST /api/v1/orders
**Description**: Creates a new order and triggers processing workflow.  
**Parameters**: `order_data` (body): Order details JSON  
**Why needed**: Initiates the order fulfillment process.  
**How it works**: Starts Temporal workflow, publishes Kafka event, stores in Supabase.  
**Response**:
```json
{
  "status": "success",
  "order_id": "ord_1234567890",
  "message": "Order created successfully"
}
```

##### GET /api/v1/orders/{order_id}
**Description**: Retrieves order details by ID.  
**Parameters**: `order_id` (path): Order identifier  
**Why needed**: Order tracking and status monitoring.  
**How it works**: Queries Supabase for order data. Currently returns placeholder.  
**Response**:
```json
{
  "order_id": "ord_1234567890",
  "status": "pending",
  "items": []
}
```

##### PUT /api/v1/orders/{order_id}
**Description**: Updates an existing order.  
**Parameters**:
- `order_id` (path): Order identifier
- `updates` (body): Update data JSON  
**Why needed**: Allows order modifications during fulfillment.  
**How it works**: Updates Supabase record, publishes Kafka event. Currently returns placeholder.  
**Response**:
```json
{
  "order_id": "ord_1234567890",
  "status": "updated"
}
```

#### Reservation Management

##### POST /api/v1/reservations
**Description**: Creates a new reservation and triggers workflow.  
**Parameters**: `reservation_data` (body): Reservation details JSON  
**Why needed**: Manages booking and scheduling systems.  
**How it works**: Starts Temporal workflow, publishes Kafka event. Currently returns placeholder.  
**Response**:
```json
{
  "status": "success",
  "reservation_id": "res_1234567890",
  "message": "Reservation created successfully"
}
```

##### GET /api/v1/reservations/{reservation_id}
**Description**: Retrieves reservation details.  
**Parameters**: `reservation_id` (path): Reservation identifier  
**Why needed**: Reservation tracking and confirmation.  
**How it works**: Queries Supabase for reservation data. Currently returns placeholder.  
**Response**:
```json
{
  "reservation_id": "res_1234567890",
  "status": "confirmed",
  "details": {}
}
```

#### Inventory Management

##### GET /api/v1/inventory
**Description**: Retrieves inventory for a business.  
**Parameters**: `business_id` (query): Business UUID  
**Why needed**: Inventory visibility for operations and ordering.  
**How it works**: Queries Supabase inventory tables. Currently returns placeholder.  
**Response**:
```json
{
  "business_id": "uuid",
  "items": []
}
```

##### POST /api/v1/inventory
**Description**: Updates inventory levels.  
**Parameters**: `inventory_data` (body): Inventory update JSON  
**Why needed**: Maintains accurate stock levels.  
**How it works**: Updates Supabase inventory records. Currently returns placeholder.  
**Response**:
```json
{
  "status": "success",
  "message": "Inventory updated"
}
```

### auth-service

**Base URL**: `http://auth-service:8010`  
**Port**: 8010  
**Purpose**: Manages users, businesses, and access control.

#### Business Management

##### POST /api/v1/business
**Description**: Creates a new business profile.  
**Parameters**: `business_data` (body): Business creation data (includes operating_hours)  
**Why needed**: Registers new businesses in the platform.  
**How it works**: Validates data, creates Supabase record, associates with owner. Requires authentication.  
**Response**: Business object with UUID and metadata

##### GET /api/v1/business
**Description**: Lists businesses user has access to.  
**Parameters**:
- `skip` (query, optional): Pagination offset (default: 0)
- `limit` (query, optional): Page size (default: 100)  
**Why needed**: Business discovery and management interface.  
**How it works**: Filters businesses based on user roles, paginates results. Admins see all businesses.  

##### GET /api/v1/business/owner/{owner_id}
**Description**: Lists businesses owned by a specific user.  
**Parameters**: `owner_id` (path): Owner UUID  
**Why needed**: Owner-specific business management.  
**How it works**: Filters businesses by owner relationship.

##### GET /api/v1/business/{business_id}
**Description**: Retrieves detailed business information.  
**Parameters**: `business_id` (path): Business UUID  
**Why needed**: Business profile viewing and editing.  
**How it works**: Checks user permissions, returns business data including operating_hours.

##### PUT /api/v1/business/{business_id}
**Description**: Updates business information.  
**Parameters**:
- `business_id` (path): Business UUID
- `business_data` (body): Update data (can include operating_hours)  
**Why needed**: Business profile maintenance.  
**How it works**: Validates permissions (owner/admin), updates Supabase record.

##### DELETE /api/v1/business/{business_id}
**Description**: Deletes a business profile.  
**Parameters**: `business_id` (path): Business UUID  
**Why needed**: Business removal from platform.  
**How it works**: Checks owner permissions, soft-deletes or removes business data.

### api-gateway

**Base URL**: `http://api-gateway:8000`  
**Port**: 8000  
**Purpose**: Centralized API routing and middleware.

The API gateway acts as a proxy and does not expose its own business logic endpoints. It routes requests to the appropriate services with:

- JWT authentication
- Rate limiting
- CORS handling
- Request transformation
- Prometheus metrics

Key routes:
- `/api/v1/analytics/*` → analytics-dashboard-service
- `/api/v1/business` → business-logic-service  
- `/api/v1/auth/*` → auth-service
- `/qr`, `/webhooks/*`, `/ws`, `/voice` → Various entry points

## Authentication & Security

All business logic endpoints require JWT authentication via the `Authorization: Bearer <token>` header. The API gateway validates tokens and enforces role-based access control.

## Data Flow

1. **Dashboard Requests**: API gateway routes to analytics-dashboard-service
2. **Data Aggregation**: Service queries Supabase and processes via business-logic-service APIs
3. **Real-time Updates**: Kafka streams provide live data
4. **Business Operations**: Orders/reservations trigger Temporal workflows
5. **Authentication**: All requests validated through auth-service

## Monitoring & Observability

All services expose:
- Prometheus metrics (`/metrics`)
- Health checks for Kubernetes probes
- Structured logging with service-specific prefixes
- Request duration and error tracking

## Future Enhancements

Current implementation includes TODOs for:
- Kafka consumer integration for real-time analytics
- Supabase client connections
- Redis caching layers
- Full workflow implementations
- Advanced AI processing pipelines
