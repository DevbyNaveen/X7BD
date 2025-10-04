# 🧪 Testing Guide - Analytics Dashboard Service

## 📋 Testing Overview

This guide covers comprehensive testing strategies for the Analytics Dashboard Service, including unit tests, integration tests, API tests, and WebSocket tests.

---

## 🚀 Quick Test

### Start Service & Run Basic Tests

```bash
# Start the service
python -m uvicorn app.main:app --reload --port 8060

# In another terminal, run quick tests
curl http://localhost:8060/health
curl http://localhost:8060/docs
```

---

## 🔍 Manual API Testing

### 1. Health Check Tests

```bash
# General health
curl http://localhost:8060/health

# Expected: {"status":"healthy","service":"analytics-dashboard-service","timestamp":"..."}

# Liveness probe
curl http://localhost:8060/health/live

# Readiness probe
curl http://localhost:8060/health/ready
```

### 2. Menu Management Tests

```bash
# Create menu category
curl -X POST "http://localhost:8060/api/v1/menu/categories" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Appetizers",
    "description": "Delicious starters",
    "display_order": 1,
    "is_active": true
  }'

# List categories
curl "http://localhost:8060/api/v1/menu/categories?business_id=123e4567-e89b-12d3-a456-426614174000"

# Create menu item
curl -X POST "http://localhost:8060/api/v1/menu/items" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Caesar Salad",
    "description": "Fresh romaine with parmesan",
    "price": 12.99,
    "cost": 4.50,
    "is_available": true
  }'

# List menu items
curl "http://localhost:8060/api/v1/menu/items?business_id=123e4567-e89b-12d3-a456-426614174000"

# Get item details
curl "http://localhost:8060/api/v1/menu/items/ITEM_ID"

# Update item
curl -X PUT "http://localhost:8060/api/v1/menu/items/ITEM_ID" \
  -H "Content-Type: application/json" \
  -d '{"price": 14.99}'

# Delete item (soft delete)
curl -X DELETE "http://localhost:8060/api/v1/menu/items/ITEM_ID?soft_delete=true"
```

### 3. Table Management Tests

```bash
# Create table
curl -X POST "http://localhost:8060/api/v1/operations/tables" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "123e4567-e89b-12d3-a456-426614174000",
    "table_number": "T1",
    "capacity": 4,
    "status": "available"
  }'

# List tables
curl "http://localhost:8060/api/v1/operations/tables?business_id=123e4567-e89b-12d3-a456-426614174000"

# Assign table
curl -X POST "http://localhost:8060/api/v1/operations/tables/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "table_id": "TABLE_ID",
    "order_id": "ORDER_ID",
    "party_size": 4
  }'

# Release table
curl -X POST "http://localhost:8060/api/v1/operations/tables/TABLE_ID/release"
```

### 4. Staff & Time Clock Tests

```bash
# Create staff member
curl -X POST "http://localhost:8060/api/v1/operations/staff" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "123e4567-e89b-12d3-a456-426614174000",
    "first_name": "John",
    "last_name": "Doe",
    "position": "server",
    "hourly_rate": 15.00
  }'

# Clock in
curl -X POST "http://localhost:8060/api/v1/operations/time-clock/clock-in" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "123e4567-e89b-12d3-a456-426614174000",
    "staff_id": "STAFF_ID",
    "clock_in": "2025-10-05T08:00:00Z"
  }'

# Get active staff
curl "http://localhost:8060/api/v1/operations/time-clock/active?business_id=123e4567-e89b-12d3-a456-426614174000"

# Clock out
curl -X PUT "http://localhost:8060/api/v1/operations/time-clock/CLOCK_ID/clock-out"
```

### 5. Analytics Tests

```bash
# Real-time analytics
curl "http://localhost:8060/api/v1/analytics/realtime/123e4567-e89b-12d3-a456-426614174000"

# Top menu items
curl "http://localhost:8060/api/v1/analytics/menu/top-items?business_id=123e4567-e89b-12d3-a456-426614174000&start_date=2025-10-01&end_date=2025-10-05&limit=10"

# Financial summary
curl "http://localhost:8060/api/v1/analytics/financial/summary?business_id=123e4567-e89b-12d3-a456-426614174000&start_date=2025-10-01&end_date=2025-10-05"
```

### 6. Business Settings Tests

```bash
# Get settings
curl "http://localhost:8060/api/v1/business-settings/123e4567-e89b-12d3-a456-426614174000"

# Update working hours
curl -X PUT "http://localhost:8060/api/v1/business-settings/123e4567-e89b-12d3-a456-426614174000/working-hours" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "day_of_week": 0,
      "is_open": true,
      "open_time": "09:00",
      "close_time": "22:00"
    }
  ]'
```

---

## 🔌 WebSocket Testing

### Using JavaScript/Browser Console

```javascript
// Dashboard WebSocket
const ws = new WebSocket('ws://localhost:8060/api/v1/ws/dashboard/123e4567-e89b-12d3-a456-426614174000');

ws.onopen = () => {
  console.log('✓ Connected to dashboard');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.onerror = (error) => {
  console.error('✗ WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed');
};

// Send ping
ws.send(JSON.stringify({ type: 'ping' }));

// Subscribe to events
ws.send(JSON.stringify({ 
  type: 'subscribe', 
  events: ['order_update', 'table_update'] 
}));
```

### Using wscat (CLI Tool)

```bash
# Install wscat
npm install -g wscat

# Connect to dashboard
wscat -c ws://localhost:8060/api/v1/ws/dashboard/123e4567-e89b-12d3-a456-426614174000

# Send ping
> {"type":"ping"}

# Connect to KDS
wscat -c ws://localhost:8060/api/v1/ws/kds/123e4567-e89b-12d3-a456-426614174000
```

### Using Python

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8060/api/v1/ws/dashboard/123e4567-e89b-12d3-a456-426614174000"
    
    async with websockets.connect(uri) as websocket:
        # Receive initial message
        response = await websocket.recv()
        print(f"Connected: {response}")
        
        # Send ping
        await websocket.send(json.dumps({"type": "ping"}))
        
        # Receive pong
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(test_websocket())
```

---

## 🐍 Python Testing Scripts

### Complete Test Suite

```python
import requests
import json
from uuid import uuid4

BASE_URL = "http://localhost:8060"
BUSINESS_ID = str(uuid4())

class TestAnalyticsDashboard:
    
    def test_health_check(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health check passed")
    
    def test_create_menu_category(self):
        """Test menu category creation"""
        category = {
            "business_id": BUSINESS_ID,
            "name": "Test Category",
            "description": "Test description",
            "display_order": 1,
            "is_active": True
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/menu/categories",
            json=category
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Category"
        print("✓ Menu category creation passed")
        return data["id"]
    
    def test_create_menu_item(self, category_id):
        """Test menu item creation"""
        item = {
            "business_id": BUSINESS_ID,
            "category_id": category_id,
            "name": "Test Item",
            "price": 12.99,
            "cost": 4.50,
            "is_available": True
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/menu/items",
            json=item
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Item"
        print("✓ Menu item creation passed")
        return data["id"]
    
    def test_list_menu_items(self):
        """Test listing menu items"""
        response = requests.get(
            f"{BASE_URL}/api/v1/menu/items",
            params={"business_id": BUSINESS_ID}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print("✓ Menu items listing passed")
    
    def test_create_table(self):
        """Test table creation"""
        table = {
            "business_id": BUSINESS_ID,
            "table_number": "T1",
            "capacity": 4,
            "status": "available"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/operations/tables",
            json=table
        )
        assert response.status_code == 201
        data = response.json()
        assert data["table_number"] == "T1"
        print("✓ Table creation passed")
        return data["id"]
    
    def test_realtime_analytics(self):
        """Test real-time analytics"""
        response = requests.get(
            f"{BASE_URL}/api/v1/analytics/realtime/{BUSINESS_ID}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "revenue" in data
        assert "tables" in data
        print("✓ Real-time analytics passed")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n🧪 Running Analytics Dashboard Tests...\n")
        
        self.test_health_check()
        category_id = self.test_create_menu_category()
        self.test_create_menu_item(category_id)
        self.test_list_menu_items()
        self.test_create_table()
        self.test_realtime_analytics()
        
        print("\n✅ All tests passed!\n")

# Run tests
if __name__ == "__main__":
    tester = TestAnalyticsDashboard()
    tester.run_all_tests()
```

---

## 📊 Load Testing

### Using Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class AnalyticsDashboardUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup"""
        self.business_id = "123e4567-e89b-12d3-a456-426614174000"
    
    @task(3)
    def get_realtime_analytics(self):
        """Test real-time analytics endpoint"""
        self.client.get(f"/api/v1/analytics/realtime/{self.business_id}")
    
    @task(2)
    def list_menu_items(self):
        """Test menu items listing"""
        self.client.get(
            "/api/v1/menu/items",
            params={"business_id": self.business_id}
        )
    
    @task(1)
    def list_tables(self):
        """Test tables listing"""
        self.client.get(
            "/api/v1/operations/tables",
            params={"business_id": self.business_id}
        )

# Run: locust -f locustfile.py --host=http://localhost:8060
```

### Using Apache Bench

```bash
# Test real-time analytics endpoint
ab -n 1000 -c 10 http://localhost:8060/api/v1/analytics/realtime/123e4567-e89b-12d3-a456-426614174000

# Test menu items endpoint
ab -n 1000 -c 10 "http://localhost:8060/api/v1/menu/items?business_id=123e4567-e89b-12d3-a456-426614174000"
```

---

## 🔒 Security Testing

### 1. Input Validation Tests

```bash
# Test invalid UUID
curl "http://localhost:8060/api/v1/analytics/realtime/invalid-uuid"
# Expected: 422 Unprocessable Entity

# Test missing required fields
curl -X POST "http://localhost:8060/api/v1/menu/items" \
  -H "Content-Type: application/json" \
  -d '{}'
# Expected: 422 Unprocessable Entity

# Test invalid data types
curl -X POST "http://localhost:8060/api/v1/menu/items" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Test",
    "price": "invalid"
  }'
# Expected: 422 Unprocessable Entity
```

### 2. SQL Injection Tests

```bash
# Test SQL injection in search
curl "http://localhost:8060/api/v1/menu/items?business_id=123e4567-e89b-12d3-a456-426614174000&search='; DROP TABLE menu_items; --"
# Expected: Safe handling, no SQL execution
```

### 3. Rate Limiting Tests

```bash
# Send many requests quickly
for i in {1..100}; do
  curl "http://localhost:8060/api/v1/analytics/realtime/123e4567-e89b-12d3-a456-426614174000" &
done
wait
# Expected: Some requests return 429 Too Many Requests
```

---

## 🎯 Integration Testing

### Full Workflow Test

```python
import requests
import time

BASE_URL = "http://localhost:8060"

def test_complete_workflow():
    """Test complete restaurant workflow"""
    
    business_id = "123e4567-e89b-12d3-a456-426614174000"
    
    # 1. Create menu category
    print("1. Creating menu category...")
    category = requests.post(
        f"{BASE_URL}/api/v1/menu/categories",
        json={
            "business_id": business_id,
            "name": "Main Courses",
            "display_order": 1,
            "is_active": True
        }
    ).json()
    category_id = category["id"]
    print(f"   ✓ Category created: {category_id}")
    
    # 2. Create menu item
    print("2. Creating menu item...")
    item = requests.post(
        f"{BASE_URL}/api/v1/menu/items",
        json={
            "business_id": business_id,
            "category_id": category_id,
            "name": "Grilled Salmon",
            "price": 24.99,
            "cost": 8.50,
            "is_available": True
        }
    ).json()
    item_id = item["id"]
    print(f"   ✓ Item created: {item_id}")
    
    # 3. Create table
    print("3. Creating table...")
    table = requests.post(
        f"{BASE_URL}/api/v1/operations/tables",
        json={
            "business_id": business_id,
            "table_number": "T5",
            "capacity": 4,
            "status": "available"
        }
    ).json()
    table_id = table["id"]
    print(f"   ✓ Table created: {table_id}")
    
    # 4. Create staff member
    print("4. Creating staff member...")
    staff = requests.post(
        f"{BASE_URL}/api/v1/operations/staff",
        json={
            "business_id": business_id,
            "first_name": "Jane",
            "last_name": "Smith",
            "position": "server"
        }
    ).json()
    staff_id = staff["id"]
    print(f"   ✓ Staff created: {staff_id}")
    
    # 5. Clock in staff
    print("5. Clocking in staff...")
    clock_in = requests.post(
        f"{BASE_URL}/api/v1/operations/time-clock/clock-in",
        json={
            "business_id": business_id,
            "staff_id": staff_id,
            "clock_in": "2025-10-05T08:00:00Z"
        }
    ).json()
    print(f"   ✓ Staff clocked in")
    
    # 6. Get real-time analytics
    print("6. Getting real-time analytics...")
    analytics = requests.get(
        f"{BASE_URL}/api/v1/analytics/realtime/{business_id}"
    ).json()
    print(f"   ✓ Analytics retrieved")
    print(f"   - Active orders: {analytics['orders']['active']}")
    print(f"   - Available tables: {analytics['tables']['available']}")
    print(f"   - Clocked in staff: {analytics['staff']['clocked_in']}")
    
    print("\n✅ Complete workflow test passed!")

if __name__ == "__main__":
    test_complete_workflow()
```

---

## 📈 Performance Benchmarks

### Expected Performance Metrics

```
Endpoint                              | Target Response Time | Target RPS
-------------------------------------|---------------------|------------
GET /health                          | < 10ms              | 1000+
GET /api/v1/analytics/realtime       | < 100ms             | 500+
GET /api/v1/menu/items               | < 50ms              | 800+
POST /api/v1/menu/items              | < 100ms             | 300+
WebSocket connection                 | < 50ms              | 1000+
```

### Benchmark Script

```python
import time
import requests
import statistics

def benchmark_endpoint(url, iterations=100):
    """Benchmark an endpoint"""
    times = []
    
    for _ in range(iterations):
        start = time.time()
        response = requests.get(url)
        end = time.time()
        
        if response.status_code == 200:
            times.append((end - start) * 1000)  # Convert to ms
    
    return {
        "avg": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "p95": statistics.quantiles(times, n=20)[18]  # 95th percentile
    }

# Run benchmarks
print("Running benchmarks...\n")

endpoints = {
    "Health Check": "http://localhost:8060/health",
    "Real-time Analytics": "http://localhost:8060/api/v1/analytics/realtime/123e4567-e89b-12d3-a456-426614174000",
    "Menu Items": "http://localhost:8060/api/v1/menu/items?business_id=123e4567-e89b-12d3-a456-426614174000"
}

for name, url in endpoints.items():
    results = benchmark_endpoint(url)
    print(f"{name}:")
    print(f"  Average: {results['avg']:.2f}ms")
    print(f"  Median: {results['median']:.2f}ms")
    print(f"  P95: {results['p95']:.2f}ms")
    print(f"  Min: {results['min']:.2f}ms")
    print(f"  Max: {results['max']:.2f}ms")
    print()
```

---

## ✅ Test Checklist

### Pre-Deployment Testing

- [ ] All health checks pass
- [ ] All CRUD operations work
- [ ] WebSocket connections stable
- [ ] Real-time events publishing
- [ ] Analytics calculations correct
- [ ] Error handling works
- [ ] Input validation effective
- [ ] Rate limiting active
- [ ] Load tests pass
- [ ] Security tests pass

### Regression Testing

- [ ] Existing features still work
- [ ] No performance degradation
- [ ] Database queries optimized
- [ ] WebSocket connections stable
- [ ] Error messages clear

---

## 🐛 Debugging Tips

### Enable Debug Logging

```bash
# Set log level to debug
export LOG_LEVEL=debug
python -m uvicorn app.main:app --reload --port 8060
```

### Check Database Queries

```python
# Add to database.py for debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# Log all queries
def execute_query(self, query):
    logging.debug(f"Executing query: {query}")
    return self.client.execute(query)
```

### Monitor WebSocket Connections

```python
# Add to realtime.py
def connect(self, websocket, business_id):
    print(f"WebSocket connected: {business_id}")
    print(f"Total connections: {len(self.active_connections)}")
```

---

## 📝 Test Report Template

```markdown
# Test Report - Analytics Dashboard Service

**Date**: 2025-10-05
**Tester**: Your Name
**Version**: 1.0.0

## Summary
- Total Tests: 50
- Passed: 48
- Failed: 2
- Skipped: 0

## Test Results

### API Tests
✅ Health checks - PASS
✅ Menu CRUD - PASS
✅ Table management - PASS
⚠️ Staff scheduling - FAIL (timeout issue)
✅ Analytics - PASS

### WebSocket Tests
✅ Dashboard connection - PASS
✅ KDS connection - PASS
✅ Event publishing - PASS

### Performance Tests
✅ Load test (1000 req/s) - PASS
⚠️ Stress test (5000 req/s) - FAIL (rate limit)

## Issues Found
1. Staff scheduling endpoint timeout under load
2. Rate limiting too aggressive for analytics

## Recommendations
1. Optimize staff scheduling query
2. Adjust rate limits for analytics endpoints
```

---

**🎉 Your testing suite is complete! Run these tests before each deployment.**
