# 🚀 Quick Start Guide - Analytics Dashboard Service

## Prerequisites

- Python 3.9+
- Supabase account with project configured
- Environment variables configured

## Installation

### 1. Install Dependencies

```bash
cd /Users/naveen/Desktop/x7AI/services/analytics-dashboard-service
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file is already configured with Supabase credentials:

```env
SUPABASE_URL=https://ydlmkvkfmmnitfhjqakt.supabase.co
SUPABASE_SERVICE_KEY=***
ANALYTICS_PORT=8060
```

### 3. Start the Service

```bash
# Development mode with auto-reload
python -m uvicorn app.main:app --reload --port 8060

# Or using the main module
python -m app.main
```

## 🎯 Testing the API

### Access API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8060/docs
- **ReDoc**: http://localhost:8060/redoc
- **Health Check**: http://localhost:8060/health

### Example API Calls

#### 1. Create Menu Category

```bash
curl -X POST "http://localhost:8060/api/v1/menu/categories" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "YOUR_BUSINESS_ID",
    "name": "Appetizers",
    "description": "Delicious starters",
    "display_order": 1,
    "is_active": true
  }'
```

#### 2. Create Menu Item

```bash
curl -X POST "http://localhost:8060/api/v1/menu/items" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "YOUR_BUSINESS_ID",
    "category_id": "CATEGORY_ID",
    "name": "Caesar Salad",
    "description": "Fresh romaine with parmesan",
    "price": 12.99,
    "cost": 4.50,
    "is_available": true
  }'
```

#### 3. Get Real-time Analytics

```bash
curl "http://localhost:8060/api/v1/analytics/realtime/YOUR_BUSINESS_ID"
```

#### 4. Create Table

```bash
curl -X POST "http://localhost:8060/api/v1/operations/tables" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "YOUR_BUSINESS_ID",
    "table_number": "T1",
    "capacity": 4,
    "status": "available"
  }'
```

#### 5. Clock In Staff

```bash
curl -X POST "http://localhost:8060/api/v1/operations/time-clock/clock-in" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "YOUR_BUSINESS_ID",
    "staff_id": "STAFF_ID",
    "clock_in": "2025-10-05T08:00:00Z"
  }'
```

## 🔌 WebSocket Testing

### Connect to Dashboard WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8060/api/v1/ws/dashboard/YOUR_BUSINESS_ID');

ws.onopen = () => {
  console.log('Connected to dashboard');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Send ping to keep alive
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);
```

### Kitchen Display WebSocket

```javascript
const kdsWs = new WebSocket('ws://localhost:8060/api/v1/ws/kds/YOUR_BUSINESS_ID');

kdsWs.onmessage = (event) => {
  const order = JSON.parse(event.data);
  // Update kitchen display
  console.log('New order:', order);
};
```

## 📊 Key Endpoints

### Menu Management
- `GET /api/v1/menu/categories` - List categories
- `POST /api/v1/menu/items` - Create menu item
- `GET /api/v1/menu/items?business_id=XXX` - List items
- `PUT /api/v1/menu/items/{id}` - Update item

### Operations
- `GET /api/v1/operations/tables?business_id=XXX` - List tables
- `POST /api/v1/operations/tables/assign` - Assign table
- `POST /api/v1/operations/kds/orders` - Send to kitchen
- `GET /api/v1/operations/time-clock/active?business_id=XXX` - Active staff

### Analytics
- `GET /api/v1/analytics/realtime/{business_id}` - Live metrics
- `GET /api/v1/analytics/menu/top-items` - Top items
- `GET /api/v1/analytics/financial/summary` - Financial report

### Business Settings
- `GET /api/v1/business-settings/{business_id}` - Get settings
- `PUT /api/v1/business-settings/{business_id}/working-hours` - Update hours

## 🧪 Testing with Python

```python
import requests
import json

BASE_URL = "http://localhost:8060"
BUSINESS_ID = "your-business-id"

# Get real-time analytics
response = requests.get(f"{BASE_URL}/api/v1/analytics/realtime/{BUSINESS_ID}")
print(json.dumps(response.json(), indent=2))

# Create menu item
menu_item = {
    "business_id": BUSINESS_ID,
    "name": "Margherita Pizza",
    "price": 14.99,
    "cost": 5.50,
    "is_available": True
}
response = requests.post(f"{BASE_URL}/api/v1/menu/items", json=menu_item)
print(response.json())

# Get tables
response = requests.get(f"{BASE_URL}/api/v1/operations/tables", 
                       params={"business_id": BUSINESS_ID})
print(response.json())
```

## 🔍 Monitoring

### Health Checks

```bash
# Service health
curl http://localhost:8060/health

# Liveness probe
curl http://localhost:8060/health/live

# Readiness probe
curl http://localhost:8060/health/ready
```

### Logs

The service logs all operations to stdout:
```
Starting analytics-dashboard-service
Service running on port 8060
✓ Database service initialized
✓ WebSocket manager initialized
✓ analytics-dashboard-service started successfully
```

## 🐛 Troubleshooting

### Database Connection Issues

If you see database errors:
1. Check `.env` file has correct `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
2. Verify Supabase project is active
3. Check network connectivity

### WebSocket Connection Issues

If WebSocket won't connect:
1. Ensure service is running on correct port
2. Check firewall settings
3. Verify WebSocket URL format: `ws://localhost:8060/api/v1/ws/...`

### Import Errors

If you get import errors:
```bash
# Install missing dependencies
pip install fastapi uvicorn supabase python-dotenv pydantic

# Or install from requirements.txt
pip install -r requirements.txt
```

## 📚 API Documentation

Full interactive API documentation available at:
- **Swagger UI**: http://localhost:8060/docs
- **ReDoc**: http://localhost:8060/redoc

## 🎯 Common Use Cases

### 1. Restaurant Dashboard Setup

```bash
# 1. Create menu categories
curl -X POST "http://localhost:8060/api/v1/menu/categories" -d '{"business_id":"XXX","name":"Appetizers"}'

# 2. Add menu items
curl -X POST "http://localhost:8060/api/v1/menu/items" -d '{"business_id":"XXX","name":"Caesar Salad","price":12.99}'

# 3. Create tables
curl -X POST "http://localhost:8060/api/v1/operations/tables" -d '{"business_id":"XXX","table_number":"T1","capacity":4}'

# 4. Get real-time dashboard
curl "http://localhost:8060/api/v1/analytics/realtime/XXX"
```

### 2. Kitchen Display System

```bash
# 1. Send order to kitchen
curl -X POST "http://localhost:8060/api/v1/operations/kds/orders" -d '{
  "business_id":"XXX",
  "order_id":"ORDER_ID",
  "station":"grill",
  "priority":1
}'

# 2. Update order status
curl -X PUT "http://localhost:8060/api/v1/operations/kds/orders/ORDER_ID" -d '{"status":"preparing"}'

# 3. Get active orders
curl "http://localhost:8060/api/v1/operations/kds/orders?business_id=XXX"
```

### 3. Staff Management

```bash
# 1. Add staff member
curl -X POST "http://localhost:8060/api/v1/operations/staff" -d '{
  "business_id":"XXX",
  "first_name":"John",
  "last_name":"Doe",
  "position":"server"
}'

# 2. Clock in
curl -X POST "http://localhost:8060/api/v1/operations/time-clock/clock-in" -d '{
  "business_id":"XXX",
  "staff_id":"STAFF_ID"
}'

# 3. Get active staff
curl "http://localhost:8060/api/v1/operations/time-clock/active?business_id=XXX"
```

## 🚀 Production Deployment

### Using Docker

```bash
# Build image
docker build -t analytics-dashboard-service .

# Run container
docker run -p 8060:8060 --env-file .env analytics-dashboard-service
```

### Using Systemd

```ini
[Unit]
Description=Analytics Dashboard Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/service
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8060
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📞 Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review logs for error messages
3. Verify environment configuration
4. Check database connectivity

---

**🎉 You're all set! The enterprise-grade analytics dashboard backend is ready to use.**
