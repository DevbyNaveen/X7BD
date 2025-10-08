# 📊 Complete API Reference - Analytics Dashboard Service

**Version:** 2.0.0  
**Base URL:** `http://localhost:8060`  
**All Categories Supported:** Food & Hospitality, Service-Based, Retail, Professional Services

---

## 🔐 Authentication

All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## 🍽️ FOOD & HOSPITALITY TEMPLATE

### Menu Management

#### Create Menu Category
```http
POST /api/v1/menu/categories
Content-Type: application/json

{
  "business_id": "uuid",
  "name": "Appetizers",
  "description": "Starter dishes",
  "display_order": 1
}
```

#### List Menu Items
```http
GET /api/v1/menu/items?business_id=uuid&category_id=uuid&is_available=true
```

#### Update Menu Item
```http
PUT /api/v1/menu/items/{item_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "price": 15.99,
  "is_available": true
}
```

### Operations Management

#### Create Table
```http
POST /api/v1/operations/tables
Content-Type: application/json

{
  "business_id": "uuid",
  "table_number": "T1",
  "capacity": 4,
  "status": "available"
}
```

#### Clock In Staff
```http
POST /api/v1/operations/time-clock/clock-in
Content-Type: application/json

{
  "business_id": "uuid",
  "staff_id": "uuid"
}
```

### Inventory Management

#### Create Inventory Item
```http
POST /api/v1/inventory/items
Content-Type: application/json

{
  "business_id": "uuid",
  "name": "Tomatoes",
  "unit": "kg",
  "current_stock": 50,
  "min_stock": 10
}
```

---

## ✂️ SERVICE-BASED TEMPLATE

### Services Management

#### Create Service
```http
POST /api/v1/services
Content-Type: application/json

{
  "business_id": "uuid",
  "name": "Haircut",
  "description": "Men's haircut",
  "duration_minutes": 30,
  "price": 25.00,
  "category": "Hair Services"
}
```

#### List Services
```http
GET /api/v1/services?business_id=uuid&category=Hair%20Services&is_active=true
```

#### Update Service
```http
PUT /api/v1/services/{service_id}
Content-Type: application/json

{
  "price": 30.00,
  "duration_minutes": 45
}
```

#### Delete Service
```http
DELETE /api/v1/services/{service_id}
```

### Appointments Management

#### Create Appointment
```http
POST /api/v1/appointments
Content-Type: application/json

{
  "business_id": "uuid",
  "service_id": "uuid",
  "client_id": "uuid",
  "staff_id": "uuid",
  "scheduled_time": "2025-10-08T10:00:00Z",
  "end_time": "2025-10-08T10:30:00Z",
  "duration_minutes": 30,
  "status": "scheduled"
}
```

#### List Appointments
```http
GET /api/v1/appointments?business_id=uuid&status=scheduled&start_date=2025-10-08T00:00:00Z
```

#### Update Appointment
```http
PUT /api/v1/appointments/{appointment_id}
Content-Type: application/json

{
  "status": "confirmed",
  "notes": "Client confirmed via phone"
}
```

#### Cancel Appointment
```http
DELETE /api/v1/appointments/{appointment_id}
```

### Clients Management

#### Create Client
```http
POST /api/v1/clients
Content-Type: application/json

{
  "business_id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "preferences": {
    "preferred_stylist": "uuid",
    "allergies": []
  }
}
```

#### List Clients
```http
GET /api/v1/clients?business_id=uuid&is_active=true&limit=50
```

#### Get Client Details
```http
GET /api/v1/clients/{client_id}
```

#### Update Client
```http
PUT /api/v1/clients/{client_id}
Content-Type: application/json

{
  "phone": "+1987654321",
  "notes": "Prefers morning appointments"
}
```

#### Get Client History
```http
GET /api/v1/clients/{client_id}/history
```

---

## 🛍️ RETAIL TEMPLATE

### Products Management

#### Create Product
```http
POST /api/v1/products
Content-Type: application/json

{
  "business_id": "uuid",
  "name": "Wireless Mouse",
  "description": "Ergonomic wireless mouse",
  "sku": "WM-001",
  "barcode": "1234567890123",
  "category": "Electronics",
  "brand": "TechBrand",
  "price": 29.99,
  "cost": 15.00,
  "inventory_quantity": 100,
  "low_stock_threshold": 20,
  "track_inventory": true
}
```

#### List Products
```http
GET /api/v1/products?business_id=uuid&category=Electronics&is_available=true&low_stock=false
```

#### Get Product Details
```http
GET /api/v1/products/{product_id}
```

#### Update Product
```http
PUT /api/v1/products/{product_id}
Content-Type: application/json

{
  "price": 24.99,
  "inventory_quantity": 150
}
```

#### Delete Product
```http
DELETE /api/v1/products/{product_id}
```

#### Adjust Inventory
```http
POST /api/v1/products/{product_id}/adjust-inventory?adjustment=50
```

### Customers Management

#### Create Customer
```http
POST /api/v1/customers
Content-Type: application/json

{
  "business_id": "uuid",
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com",
  "phone": "+1234567890",
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "customer_type": "regular",
  "marketing_consent": true
}
```

#### List Customers
```http
GET /api/v1/customers?business_id=uuid&customer_type=vip&is_active=true
```

#### Get Customer Details
```http
GET /api/v1/customers/{customer_id}
```

#### Update Customer
```http
PUT /api/v1/customers/{customer_id}
Content-Type: application/json

{
  "customer_type": "vip",
  "notes": "High-value customer"
}
```

#### Get Customer Analytics
```http
GET /api/v1/customers/{customer_id}/analytics
```

#### Adjust Loyalty Points
```http
POST /api/v1/customers/{customer_id}/loyalty-points?points=100
```

---

## 💼 PROFESSIONAL SERVICES TEMPLATE

### Projects Management

#### Create Project
```http
POST /api/v1/projects
Content-Type: application/json

{
  "business_id": "uuid",
  "client_id": "uuid",
  "name": "Website Redesign",
  "description": "Complete website overhaul",
  "status": "active",
  "priority": "high",
  "start_date": "2025-10-08",
  "end_date": "2025-12-31",
  "estimated_hours": 120,
  "hourly_rate": 150.00,
  "budget": 18000.00,
  "assigned_staff": ["uuid1", "uuid2"]
}
```

#### List Projects
```http
GET /api/v1/projects?business_id=uuid&status=active&priority=high
```

#### Get Project Details
```http
GET /api/v1/projects/{project_id}
```

#### Update Project
```http
PUT /api/v1/projects/{project_id}
Content-Type: application/json

{
  "status": "completed",
  "actual_hours": 115
}
```

#### Delete Project
```http
DELETE /api/v1/projects/{project_id}
```

### Time Entries Management

#### Create Time Entry
```http
POST /api/v1/time-entries
Content-Type: application/json

{
  "business_id": "uuid",
  "project_id": "uuid",
  "staff_id": "uuid",
  "start_time": "2025-10-08T09:00:00Z",
  "end_time": "2025-10-08T12:00:00Z",
  "duration_hours": 3.0,
  "description": "Frontend development",
  "billable": true,
  "hourly_rate": 150.00,
  "status": "submitted"
}
```

#### List Time Entries
```http
GET /api/v1/time-entries?business_id=uuid&project_id=uuid&billable=true&status=approved
```

#### Get Time Entry
```http
GET /api/v1/time-entries/{entry_id}
```

#### Update Time Entry
```http
PUT /api/v1/time-entries/{entry_id}
Content-Type: application/json

{
  "status": "approved",
  "duration_hours": 3.5
}
```

### Invoices Management

#### Create Invoice
```http
POST /api/v1/invoices
Content-Type: application/json

{
  "business_id": "uuid",
  "client_id": "uuid",
  "project_id": "uuid",
  "invoice_number": "INV-2025-001",
  "status": "draft",
  "issue_date": "2025-10-08",
  "due_date": "2025-11-08",
  "subtotal": 4500.00,
  "tax_amount": 450.00,
  "total_amount": 4950.00,
  "currency": "USD",
  "line_items": [
    {
      "description": "Frontend Development",
      "quantity": 30,
      "unit_price": 150.00,
      "amount": 4500.00
    }
  ],
  "notes": "Payment due within 30 days"
}
```

#### List Invoices
```http
GET /api/v1/invoices?business_id=uuid&status=sent&client_id=uuid
```

#### Get Invoice
```http
GET /api/v1/invoices/{invoice_id}
```

#### Update Invoice
```http
PUT /api/v1/invoices/{invoice_id}
Content-Type: application/json

{
  "status": "sent"
}
```

#### Mark Invoice as Paid
```http
POST /api/v1/invoices/{invoice_id}/mark-paid?payment_method=bank_transfer
```

### Resources Management

#### Create Resource
```http
POST /api/v1/resources
Content-Type: application/json

{
  "business_id": "uuid",
  "name": "Conference Room A",
  "type": "room",
  "description": "Large conference room with projector",
  "status": "available",
  "location": "2nd Floor",
  "cost_per_hour": 50.00
}
```

#### List Resources
```http
GET /api/v1/resources?business_id=uuid&type=room&status=available
```

#### Update Resource
```http
PUT /api/v1/resources/{resource_id}
Content-Type: application/json

{
  "status": "maintenance"
}
```

#### Create Resource Allocation
```http
POST /api/v1/resource-allocations
Content-Type: application/json

{
  "business_id": "uuid",
  "resource_id": "uuid",
  "project_id": "uuid",
  "start_time": "2025-10-08T14:00:00Z",
  "end_time": "2025-10-08T16:00:00Z",
  "notes": "Client meeting"
}
```

---

## 📊 UNIVERSAL ANALYTICS (All Categories)

### Dashboard Analytics

#### Get Universal Dashboard
```http
GET /api/v1/analytics/dashboard/{business_id}?period=30d
```

**Response adapts based on business category:**
- Food & Hospitality: Orders, revenue, tables, menu items
- Service-Based: Appointments, services, clients
- Retail: Products, customers, orders, inventory
- Professional Services: Projects, time entries, invoices

### Financial Analytics

#### Get Financial Summary
```http
GET /api/v1/analytics/financial/summary?business_id=uuid&start_date=2025-09-01T00:00:00Z&end_date=2025-10-08T00:00:00Z
```

**Response:**
```json
{
  "business_id": "uuid",
  "period": {
    "start": "2025-09-01T00:00:00Z",
    "end": "2025-10-08T00:00:00Z"
  },
  "summary": {
    "total_revenue": 45000.00,
    "total_payments": 42000.00,
    "total_orders": 150,
    "total_invoices": 12,
    "avg_transaction_value": 277.78
  },
  "breakdown": {
    "orders_revenue": 30000.00,
    "invoices_revenue": 15000.00,
    "pending_invoices": 3000.00
  }
}
```

### Customer Insights

#### Get Customer Insights
```http
GET /api/v1/analytics/customers/insights?business_id=uuid
```

**Response:**
```json
{
  "business_id": "uuid",
  "total_customers": 250,
  "active_customers": 200,
  "inactive_customers": 50,
  "avg_lifetime_value": 1200.00,
  "total_revenue": 300000.00,
  "breakdown": {
    "service_clients": 100,
    "retail_customers": 150
  }
}
```

### Performance Trends

#### Get Performance Trends
```http
GET /api/v1/analytics/performance/trends?business_id=uuid&metric=revenue&period=30d
```

**Supported metrics:**
- `revenue` - Revenue trends
- `orders` - Order volume
- `appointments` - Appointment bookings
- `projects` - Project activity

### Report Generation

#### Generate Comprehensive Report
```http
POST /api/v1/analytics/reports/generate?business_id=uuid&report_type=summary&start_date=2025-09-01T00:00:00Z&end_date=2025-10-08T00:00:00Z
```

**Report types:**
- `summary` - High-level overview
- `detailed` - In-depth analysis
- `financial` - Financial focus

---

## 🔧 Business Settings

#### Get Business Settings
```http
GET /api/v1/business-settings/{business_id}
```

#### Update Business Settings
```http
PUT /api/v1/business-settings/{business_id}
Content-Type: application/json

{
  "settings": {
    "timezone": "America/New_York",
    "currency": "USD",
    "tax_rate": 8.5
  }
}
```

#### Get Working Hours
```http
GET /api/v1/business-settings/{business_id}/working-hours
```

#### Update Working Hours
```http
PUT /api/v1/business-settings/{business_id}/working-hours
Content-Type: application/json

{
  "monday": {"open": "09:00", "close": "18:00"},
  "tuesday": {"open": "09:00", "close": "18:00"},
  "wednesday": {"open": "09:00", "close": "18:00"},
  "thursday": {"open": "09:00", "close": "18:00"},
  "friday": {"open": "09:00", "close": "18:00"},
  "saturday": {"open": "10:00", "close": "16:00"},
  "sunday": {"closed": true}
}
```

---

## 📡 WebSocket Real-time Updates

### Connect to WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8060/api/v1/ws/{business_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};
```

**Events:**
- New orders
- Appointment bookings
- Inventory updates
- Payment notifications

---

## 🚀 Response Standards

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2025-10-08T02:55:00Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": "VALIDATION_ERROR",
  "message": "Invalid input data",
  "details": { ... },
  "timestamp": "2025-10-08T02:55:00Z"
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `204` - No Content (Delete success)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

## 📋 Query Parameters

### Common Pagination
- `limit` - Number of results (default: 100, max: 1000)
- `offset` - Skip N results (default: 0)

### Common Filters
- `business_id` - Filter by business (required for most endpoints)
- `is_active` - Filter by active status
- `status` - Filter by status
- `start_date` - Filter from date
- `end_date` - Filter to date

---

## 🔒 Security

- All endpoints require JWT authentication
- Row-level security enforced at database level
- Business owners can only access their own data
- Staff members have limited permissions based on role

---

## 📚 Additional Resources

- **Interactive API Docs:** http://localhost:8060/docs
- **OpenAPI Schema:** http://localhost:8060/openapi.json
- **Health Check:** http://localhost:8060/health

---

**Last Updated:** October 8, 2025  
**API Version:** 2.0.0  
**Service:** Analytics Dashboard Service
