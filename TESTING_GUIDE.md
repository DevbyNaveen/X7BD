# Analytics API Testing Guide

## 🧪 Testing Your Menu Analytics API

This guide provides multiple approaches to test your analytics API comprehensively.

## 📋 Prerequisites

### 1. Environment Setup
```bash
# Copy environment template
cp env_template.txt .env

# Edit .env with your database credentials
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_SERVICE_KEY=your_service_role_key_here
```

### 2. Install Dependencies
```bash
# Activate virtual environment
source .venv/bin/activate

# Install testing dependencies
pip install pytest pytest-asyncio httpx requests
```

## 🚀 Testing Methods

### Method 1: Comprehensive Test Script (Recommended)

Run the comprehensive test script I created:

```bash
# Run all test scenarios
python test_analytics_comprehensive.py
```

This will test:
- ✅ Normal operations
- ✅ Different time periods (1d, 7d, 30d, 90d)
- ✅ Sorting options (sales, revenue, margin)
- ✅ Edge cases and limits
- ✅ Margin thresholds
- ✅ Empty data scenarios
- ✅ Data validation
- ✅ Performance metrics
- ✅ Real-time updates
- ✅ Data consistency
- ✅ Error handling
- ✅ Business logic

### Method 2: Start Server and Test with HTTP Requests

#### Step 1: Start the Server
```bash
# Development mode with auto-reload
./start.sh --reload

# Or production mode
./start.sh
```

#### Step 2: Test with curl
```bash
# Test overview endpoint
curl "http://localhost:8060/api/v1/analytics/menu/overview/YOUR_BUSINESS_ID?period=7d&include_trends=true"

# Test top items endpoint
curl "http://localhost:8060/api/v1/analytics/menu/top-items/YOUR_BUSINESS_ID?period=7d&limit=10&sort_by=revenue"

# Test category performance
curl "http://localhost:8060/api/v1/analytics/menu/category-performance/YOUR_BUSINESS_ID?period=7d&include_details=true"

# Test profit margins
curl "http://localhost:8060/api/v1/analytics/menu/profit-margins/YOUR_BUSINESS_ID?include_recommendations=true"

# Test complete dashboard
curl "http://localhost:8060/api/v1/analytics/menu/dashboard/YOUR_BUSINESS_ID?period=7d&include_trends=true"

# Test refresh endpoint
curl -X POST "http://localhost:8060/api/v1/analytics/menu/refresh/YOUR_BUSINESS_ID?force_refresh=false"
```

### Method 3: Interactive Testing with Python

Create a simple interactive test:

```python
import asyncio
import httpx
from uuid import uuid4

async def test_endpoints():
    base_url = "http://localhost:8060/api/v1/analytics/menu"
    business_id = "YOUR_BUSINESS_ID"  # Replace with actual business ID
    
    async with httpx.AsyncClient() as client:
        # Test overview
        response = await client.get(f"{base_url}/overview/{business_id}?period=7d")
        print(f"Overview: {response.status_code}")
        print(f"Data: {response.json()}")
        
        # Test top items
        response = await client.get(f"{base_url}/top-items/{business_id}?period=7d&limit=5")
        print(f"Top Items: {response.status_code}")
        
        # Test dashboard
        response = await client.get(f"{base_url}/dashboard/{business_id}?period=7d")
        print(f"Dashboard: {response.status_code}")

# Run the test
asyncio.run(test_endpoints())
```

### Method 4: Unit Tests with pytest

Create `test_analytics_unit.py`:

```python
import pytest
import asyncio
from unittest.mock import Mock, patch
from app.routes.analytics import get_menu_analytics_overview

@pytest.mark.asyncio
async def test_overview_endpoint():
    # Mock database service
    mock_db = Mock()
    mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    
    with patch('app.routes.analytics.get_database_service', return_value=mock_db):
        result = await get_menu_analytics_overview(uuid4(), "7d", True)
        assert result.total_menu_items == 0
        assert result.total_categories == 0

# Run with: pytest test_analytics_unit.py -v
```

## 🔍 Testing Scenarios

### 1. Basic Functionality Test
```bash
# Test all endpoints with valid data
python test_analytics_comprehensive.py
```

### 2. Edge Cases Test
```bash
# Test with empty business ID
curl "http://localhost:8060/api/v1/analytics/menu/overview/00000000-0000-0000-0000-000000000000"

# Test with invalid period
curl "http://localhost:8060/api/v1/analytics/menu/overview/YOUR_BUSINESS_ID?period=invalid"

# Test with extreme limits
curl "http://localhost:8060/api/v1/analytics/menu/top-items/YOUR_BUSINESS_ID?limit=100"
```

### 3. Performance Test
```bash
# Test response times
time curl "http://localhost:8060/api/v1/analytics/menu/dashboard/YOUR_BUSINESS_ID"
```

### 4. Data Validation Test
```bash
# Test with invalid UUID
curl "http://localhost:8060/api/v1/analytics/menu/overview/invalid-uuid"

# Test with invalid parameters
curl "http://localhost:8060/api/v1/analytics/menu/top-items/YOUR_BUSINESS_ID?sort_by=invalid"
```

## 📊 Expected Results

### Successful Response Format
```json
{
  "business_id": "uuid",
  "period": "7d",
  "total_menu_items": 45,
  "popular_items": 12,
  "average_rating": 4.6,
  "total_categories": 8,
  "items_growth": 15.2,
  "rating_growth": 2.1,
  "categories_growth": 8.7,
  "popularity_growth": 12.3,
  "performance_score": 87.3,
  "last_updated": "2024-01-01T00:00:00",
  "trends_included": true
}
```

### Error Response Format
```json
{
  "detail": "Failed to get menu analytics overview: Database connection error"
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```
   Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set
   ```
   **Solution**: Set environment variables in `.env` file

2. **Import Error**
   ```
   ModuleNotFoundError: No module named 'app'
   ```
   **Solution**: Run from project root directory

3. **Port Already in Use**
   ```
   Error: Port 8060 already in use
   ```
   **Solution**: Kill existing process or change port

4. **Invalid Business ID**
   ```
   Error: Invalid UUID format
   ```
   **Solution**: Use valid UUID format

### Debug Mode
```bash
# Run with debug logging
LOG_LEVEL=DEBUG ./start.sh --reload
```

## 📈 Performance Benchmarks

### Expected Response Times
- Overview: < 500ms
- Top Items: < 300ms
- Category Performance: < 400ms
- Profit Margins: < 600ms
- Dashboard: < 1000ms

### Memory Usage
- Should stay under 100MB for normal operations
- No memory leaks during extended testing

## ✅ Success Criteria

Your analytics API is working correctly if:

1. ✅ All endpoints return 200 status codes
2. ✅ Response times are under 1 second
3. ✅ Data structure matches frontend expectations
4. ✅ Error handling works for invalid inputs
5. ✅ Real-time updates function properly
6. ✅ Performance is consistent under load

## 🚀 Next Steps After Testing

1. **Fix any failing tests**
2. **Optimize slow endpoints**
3. **Add monitoring and logging**
4. **Deploy to production**
5. **Integrate with frontend**

## 📞 Support

If you encounter issues:
1. Check the logs: `tail -f logs/analytics.log`
2. Verify environment variables
3. Test database connectivity
4. Review error messages carefully
