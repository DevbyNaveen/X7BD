# 📚 API Reference - Analytics Dashboard Service

## Base URL
```
http://localhost:8060
```

---

## 🍽️ Menu Management API

### Categories

#### Create Category
```http
POST /api/v1/menu/categories
Content-Type: application/json

{
  "business_id": "uuid",
  "name": "string",
  "description": "string",
  "parent_id": "uuid",  // optional
  "display_order": 0,
  "icon_url": "string",  // optional
  "is_active": true
}
```

#### List Categories
```http
GET /api/v1/menu/categories?business_id={uuid}&parent_id={uuid}&is_active={bool}
```

#### Get Category
```http
GET /api/v1/menu/categories/{category_id}
```

#### Update Category
```http
PUT /api/v1/menu/categories/{category_id}
Content-Type: application/json

{
  "name": "string",
  "description": "string",
  "is_active": true
}
```

#### Delete Category
```http
DELETE /api/v1/menu/categories/{category_id}
```

### Menu Items

#### Create Item
```http
POST /api/v1/menu/items
Content-Type: application/json

{
  "business_id": "uuid",
  "category_id": "uuid",
  "name": "string",
  "description": "string",
  "price": 12.99,
  "cost": 4.50,
  "image_url": "string",
  "sku": "string",
  "is_available": true,
  "prep_time": 15,
  "calories": 450,
  "allergens": ["gluten", "dairy"],
  "tags": ["popular", "vegetarian"],
  "modifiers": ["uuid1", "uuid2"],
  "locations": ["uuid1"]
}
```

#### List Items
```http
GET /api/v1/menu/items?business_id={uuid}&category_id={uuid}&is_available={bool}&search={string}&limit=50&offset=0
```

#### Get Item Details
```http
GET /api/v1/menu/items/{item_id}?include_modifiers=true
```

#### Update Item
```http
PUT /api/v1/menu/items/{item_id}
Content-Type: application/json

{
  "name": "string",
  "price": 14.99,
  "is_available": false
}
```

#### Delete Item
```http
DELETE /api/v1/menu/items/{item_id}?soft_delete=true
```

#### Bulk Update Items
```http
POST /api/v1/menu/items/bulk-update
Content-Type: application/json

{
  "item_ids": ["uuid1", "uuid2"],
  "updates": {
    "is_available": false
  }
}
```

#### Duplicate Item
```http
POST /api/v1/menu/items/{item_id}/duplicate?new_name=New%20Item%20Name
```

### Modifiers

#### Create Modifier
```http
POST /api/v1/menu/modifiers
Content-Type: application/json

{
  "business_id": "uuid",
  "name": "Size",
  "type": "single",  // or "multiple"
  "required": true,
  "min_selections": 1,
  "max_selections": 1,
  "options": [
    {
      "name": "Small",
      "price": 0.00,
      "is_default": true
    },
    {
      "name": "Large",
      "price": 2.00,
      "is_default": false
    }
  ]
}
```

#### List Modifiers
```http
GET /api/v1/menu/modifiers?business_id={uuid}&modifier_type={string}
```

#### Update Modifier
```http
PUT /api/v1/menu/modifiers/{modifier_id}
```

#### Delete Modifier
```http
DELETE /api/v1/menu/modifiers/{modifier_id}
```

---

## 🏪 Operations API

### Locations

#### Create Location
```http
POST /api/v1/operations/locations
Content-Type: application/json

{
  "business_id": "uuid",
  "name": "Downtown Location",
  "address": "123 Main St",
  "phone": "+1234567890",
  "email": "location@example.com",
  "timezone": "America/New_York",
  "is_active": true
}
```

#### List Locations
```http
GET /api/v1/operations/locations?business_id={uuid}&is_active={bool}
```

### Tables

#### Create Table
```http
POST /api/v1/operations/tables
Content-Type: application/json

{
  "business_id": "uuid",
  "location_id": "uuid",
  "table_number": "T1",
  "capacity": 4,
  "position": {"x": 100, "y": 200},
  "shape": "rectangle",
  "status": "available"
}
```

#### List Tables
```http
GET /api/v1/operations/tables?business_id={uuid}&location_id={uuid}&status={string}
```

#### Update Table
```http
PUT /api/v1/operations/tables/{table_id}
Content-Type: application/json

{
  "status": "occupied",
  "capacity": 6
}
```

#### Assign Table
```http
POST /api/v1/operations/tables/assign
Content-Type: application/json

{
  "table_id": "uuid",
  "order_id": "uuid",
  "party_size": 4
}
```

#### Release Table
```http
POST /api/v1/operations/tables/{table_id}/release
```

#### Check Availability
```http
GET /api/v1/operations/tables/availability?business_id={uuid}&party_size=4&time_slot={datetime}
```

### Kitchen Display System (KDS)

#### Send to Kitchen
```http
POST /api/v1/operations/kds/orders
Content-Type: application/json

{
  "business_id": "uuid",
  "order_id": "uuid",
  "station": "grill",
  "priority": 1,
  "items": [...]
}
```

#### List KDS Orders
```http
GET /api/v1/operations/kds/orders?business_id={uuid}&station={string}&status={string}&active_only=true
```

#### Update Order Status
```http
PUT /api/v1/operations/kds/orders/{order_id}
Content-Type: application/json

{
  "status": "preparing"  // pending, preparing, ready, served
}
```

#### Kitchen Performance
```http
GET /api/v1/operations/kds/performance?business_id={uuid}&start_date={date}&end_date={date}
```

### Staff Management

#### Create Staff Member
```http
POST /api/v1/operations/staff
Content-Type: application/json

{
  "business_id": "uuid",
  "user_id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "position": "server",
  "hourly_rate": 15.00,
  "status": "active"
}
```

#### List Staff
```http
GET /api/v1/operations/staff?business_id={uuid}&status={string}&position={string}
```

### Time Clock

#### Clock In
```http
POST /api/v1/operations/time-clock/clock-in
Content-Type: application/json

{
  "business_id": "uuid",
  "staff_id": "uuid",
  "location_id": "uuid",
  "clock_in": "2025-10-05T08:00:00Z"
}
```

#### Clock Out
```http
PUT /api/v1/operations/time-clock/{clock_id}/clock-out?clock_out_time={datetime}
```

#### Get Active Staff
```http
GET /api/v1/operations/time-clock/active?business_id={uuid}
```

#### List Time Entries
```http
GET /api/v1/operations/time-clock?business_id={uuid}&staff_id={uuid}&start_date={date}&end_date={date}
```

### Schedules

#### Create Schedule
```http
POST /api/v1/operations/schedules
Content-Type: application/json

{
  "business_id": "uuid",
  "staff_id": "uuid",
  "location_id": "uuid",
  "shift_date": "2025-10-05",
  "start_time": "09:00",
  "end_time": "17:00",
  "position": "server"
}
```

#### List Schedules
```http
GET /api/v1/operations/schedules?business_id={uuid}&staff_id={uuid}&start_date={date}&end_date={date}
```

---

## 📊 Analytics API

### Real-time Analytics

#### Get Real-time Metrics
```http
GET /api/v1/analytics/realtime/{business_id}?location_id={uuid}
```

**Response:**
```json
{
  "business_id": "uuid",
  "timestamp": "2025-10-05T01:25:42Z",
  "orders": {
    "active": 5,
    "completed_today": 42,
    "pending_kitchen": 3,
    "avg_prep_time": 12
  },
  "revenue": {
    "today": 1250.50,
    "this_hour": 180.00,
    "avg_order_value": 29.77
  },
  "tables": {
    "total": 20,
    "available": 8,
    "occupied": 10,
    "reserved": 2
  },
  "staff": {
    "clocked_in": 8,
    "on_break": 1,
    "total_hours_today": 64.5
  },
  "inventory": {
    "low_stock_items": 3,
    "out_of_stock_items": 0
  }
}
```

#### Comprehensive Dashboard
```http
GET /api/v1/analytics/dashboard/{business_id}?period=7d&location_id={uuid}
```

### Sales Analytics

#### Sales Summary
```http
GET /api/v1/analytics/sales/summary?business_id={uuid}&start_date={date}&end_date={date}&group_by=day
```

#### Sales by Category
```http
GET /api/v1/analytics/sales/by-category?business_id={uuid}&start_date={date}&end_date={date}
```

#### Sales by Payment Method
```http
GET /api/v1/analytics/sales/by-payment-method?business_id={uuid}&start_date={date}&end_date={date}
```

### Menu Analytics

#### Top Menu Items
```http
GET /api/v1/analytics/menu/top-items?business_id={uuid}&start_date={date}&end_date={date}&metric=revenue&limit=10
```

#### Item Performance
```http
GET /api/v1/analytics/menu/item-performance/{item_id}?start_date={date}&end_date={date}
```

#### Profit Analysis
```http
GET /api/v1/analytics/menu/profit-analysis?business_id={uuid}&start_date={date}&end_date={date}
```

### Financial Analytics

#### Financial Summary
```http
GET /api/v1/analytics/financial/summary?business_id={uuid}&start_date={date}&end_date={date}
```

**Response:**
```json
{
  "business_id": "uuid",
  "revenue": {
    "total": 50000.00,
    "by_category": {}
  },
  "costs": {
    "cogs": 15000.00,
    "labor": 12500.00,
    "overhead": 7500.00
  },
  "profit": {
    "gross": 35000.00,
    "net": 15000.00
  },
  "margins": {
    "gross_margin": 70.00,
    "net_margin": 30.00
  }
}
```

#### Labor Costs
```http
GET /api/v1/analytics/financial/labor-costs?business_id={uuid}&start_date={date}&end_date={date}
```

#### COGS Analysis
```http
GET /api/v1/analytics/financial/cogs?business_id={uuid}&start_date={date}&end_date={date}
```

### Operational Analytics

#### Table Turnover
```http
GET /api/v1/analytics/operations/table-turnover?business_id={uuid}&start_date={date}&end_date={date}
```

#### Kitchen Performance
```http
GET /api/v1/analytics/operations/kitchen-performance?business_id={uuid}&start_date={date}&end_date={date}&station={string}
```

#### Staff Performance
```http
GET /api/v1/analytics/operations/staff-performance?business_id={uuid}&start_date={date}&end_date={date}
```

### Reports

#### Generate Report
```http
POST /api/v1/analytics/reports/generate?business_id={uuid}&report_type=daily&format=pdf&include_charts=true
```

#### List Scheduled Reports
```http
GET /api/v1/analytics/reports/scheduled?business_id={uuid}
```

#### Schedule Report
```http
POST /api/v1/analytics/reports/schedule
Content-Type: application/json

{
  "business_id": "uuid",
  "frequency": "daily",
  "recipients": ["email@example.com"],
  "report_type": "summary"
}
```

---

## ⚙️ Business Settings API

### Settings

#### Get Settings
```http
GET /api/v1/business-settings/{business_id}
```

#### Update Settings
```http
PUT /api/v1/business-settings/{business_id}
Content-Type: application/json

{
  "notifications": {
    "email": true,
    "sms": false,
    "push": true
  },
  "preferences": {
    "locale": "en-US",
    "currency": "USD",
    "timezone": "America/New_York"
  }
}
```

### Working Hours

#### Get Working Hours
```http
GET /api/v1/business-settings/{business_id}/working-hours
```

#### Update Working Hours
```http
PUT /api/v1/business-settings/{business_id}/working-hours
Content-Type: application/json

[
  {
    "day_of_week": 0,  // Monday
    "is_open": true,
    "open_time": "09:00",
    "close_time": "22:00",
    "breaks": [
      {
        "start": "14:00",
        "end": "15:00"
      }
    ]
  }
]
```

### Integrations

#### Get Integrations
```http
GET /api/v1/business-settings/{business_id}/integrations
```

#### Update Integration
```http
PUT /api/v1/business-settings/{business_id}/integrations/{integration_name}
Content-Type: application/json

{
  "enabled": true,
  "api_key": "xxx",
  "settings": {}
}
```

#### Delete Integration
```http
DELETE /api/v1/business-settings/{business_id}/integrations/{integration_name}
```

---

## 🔌 WebSocket API

### Dashboard WebSocket
```
WS /api/v1/ws/dashboard/{business_id}
```

**Events Received:**
- `connected` - Initial connection with current metrics
- `order_update` - New orders, status changes
- `table_update` - Table status changes
- `revenue_update` - Real-time revenue updates
- `inventory_alert` - Low stock alerts
- `staff_update` - Clock in/out events

**Client Messages:**
```json
// Ping to keep alive
{"type": "ping"}

// Subscribe to specific events
{"type": "subscribe", "events": ["order_update", "table_update"]}
```

### KDS WebSocket
```
WS /api/v1/ws/kds/{business_id}?station={string}
```

**Events Received:**
- `kds_update` - New orders, status changes
- `order_priority` - Priority order alerts
- `order_late` - Late order warnings

### Tables WebSocket
```
WS /api/v1/ws/tables/{business_id}?location_id={uuid}
```

**Events Received:**
- `table_update` - Table status changes
- `reservation_update` - New reservations
- `seating_alert` - Seating recommendations

---

## 🔐 Authentication

All endpoints require authentication via:
- **Service Key**: `SUPABASE_SERVICE_KEY` in headers
- **JWT Token**: For user-specific operations

```http
Authorization: Bearer {token}
X-Service-Key: {service_key}
```

---

## 📝 Common Response Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Success with no response body
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## 🎯 Rate Limiting

- **Default**: 100 requests/minute per business
- **WebSocket**: 1000 concurrent connections
- **Analytics**: 60 requests/minute

---

## 📊 Pagination

List endpoints support pagination:
```http
GET /api/v1/menu/items?limit=50&offset=0
```

---

## 🔍 Filtering

Most list endpoints support filtering:
```http
GET /api/v1/menu/items?business_id={uuid}&category_id={uuid}&is_available=true&search=pizza
```

---

## 📅 Date Formats

- **ISO 8601**: `2025-10-05T01:25:42Z`
- **Date only**: `2025-10-05`
- **Time only**: `14:30`

---

## 💡 Best Practices

1. **Use WebSockets** for real-time updates instead of polling
2. **Batch operations** when updating multiple items
3. **Cache responses** where appropriate (5-minute TTL recommended)
4. **Handle errors** gracefully with retry logic
5. **Validate input** before sending requests
6. **Use pagination** for large datasets
7. **Monitor rate limits** to avoid throttling

---

**For interactive API documentation, visit: http://localhost:8060/docs**
