# 🧪 Analytics API Testing Guide

## Quick Start Testing

You now have **4 different ways** to test your analytics API:

### 1. 🚀 **Comprehensive Test Script** (Recommended)
```bash
# Run all scenarios with mock data (no server needed)
python test_analytics_comprehensive.py
```
**Tests**: 12 comprehensive scenarios including edge cases, performance, error handling

### 2. 🌐 **HTTP Client Test** (Real Server)
```bash
# Start server first
./start.sh --reload

# Then test with HTTP requests
python test_analytics_http.py YOUR_BUSINESS_ID
```
**Tests**: Real HTTP requests to running server

### 3. 🔧 **PowerShell Test** (Windows)
```powershell
# Start server first
./start.sh --reload

# Then test with PowerShell
.\test_analytics.ps1 -BusinessId "YOUR_BUSINESS_ID"
```
**Tests**: PowerShell-based HTTP testing

### 4. 📡 **Curl Test** (Linux/Mac)
```bash
# Start server first
./start.sh --reload

# Then test with curl
./test_analytics_curl.sh YOUR_BUSINESS_ID
```
**Tests**: Bash script with curl commands

## 🎯 **Recommended Testing Sequence**

### Step 1: Test Without Server (Mock Data)
```bash
python test_analytics_comprehensive.py
```
This tests all logic and data structures without needing a running server.

### Step 2: Start Your Server
```bash
# Development mode
./start.sh --reload

# Or production mode
./start.sh
```

### Step 3: Test With Real Server
```bash
# Using Python HTTP client
python test_analytics_http.py YOUR_BUSINESS_ID

# Or using PowerShell (Windows)
.\test_analytics.ps1 -BusinessId "YOUR_BUSINESS_ID"

# Or using curl (Linux/Mac)
./test_analytics_curl.sh YOUR_BUSINESS_ID
```

## 📊 **What Each Test Covers**

### Comprehensive Test (`test_analytics_comprehensive.py`)
- ✅ Normal operations with mock data
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

### HTTP Tests (`test_analytics_http.py`, `test_analytics.ps1`, `test_analytics_curl.sh`)
- ✅ Server health check
- ✅ All endpoint functionality
- ✅ Parameter validation
- ✅ Error responses
- ✅ Performance testing
- ✅ Concurrent requests

## 🔍 **Test Scenarios Covered**

### **Basic Functionality**
- Overview analytics with different periods
- Top items with different sorting
- Category performance analysis
- Profit margin analysis
- Complete dashboard
- Real-time refresh

### **Edge Cases**
- Invalid business IDs
- Invalid parameters
- Empty data responses
- Extreme limits
- Invalid UUIDs

### **Error Handling**
- Database connection errors
- Invalid input validation
- Timeout handling
- Malformed requests

### **Performance**
- Response time benchmarks
- Concurrent request handling
- Memory usage
- Load testing

## 📈 **Expected Results**

### **Successful Test Output**
```
🚀 Starting Analytics API Tests
==================================================
✅ Server is healthy
📊 Business ID: your-business-id

🧪 Testing Overview - Default...
   ✅ Overview - Default: 200 (0.234s)

🧪 Testing Top Items - Revenue...
   ✅ Top Items - Revenue: 200 (0.156s)

📊 TEST SUMMARY
==================================================
✅ Successful: 15/15
❌ Failed: 0/15
📈 Success Rate: 100.0%

🎉 All tests passed! Analytics API is working correctly.
```

### **Sample API Response**
```json
{
  "business_id": "your-business-id",
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

## 🐛 **Troubleshooting**

### **Common Issues**

1. **Server Not Running**
   ```
   ❌ Server is not responding
   ```
   **Solution**: Start server with `./start.sh --reload`

2. **Database Connection Error**
   ```
   Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set
   ```
   **Solution**: Set environment variables in `.env` file

3. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'app'
   ```
   **Solution**: Run from project root directory

4. **Port Already in Use**
   ```
   Error: Port 8060 already in use
   ```
   **Solution**: Kill existing process or change port

### **Debug Mode**
```bash
# Run with debug logging
LOG_LEVEL=DEBUG ./start.sh --reload
```

## 🚀 **Next Steps After Testing**

1. **Fix any failing tests**
2. **Optimize slow endpoints**
3. **Add monitoring and logging**
4. **Deploy to production**
5. **Integrate with frontend**

## 📞 **Quick Commands**

```bash
# Quick test without server
python test_analytics_comprehensive.py

# Start server
./start.sh --reload

# Test with real server (Python)
python test_analytics_http.py YOUR_BUSINESS_ID

# Test with real server (PowerShell)
.\test_analytics.ps1 -BusinessId "YOUR_BUSINESS_ID"

# Test with real server (Curl)
./test_analytics_curl.sh YOUR_BUSINESS_ID

# Check server health
curl http://localhost:8060/health
```

## ✅ **Success Criteria**

Your analytics API is working correctly if:

1. ✅ All tests pass (100% success rate)
2. ✅ Response times are under 1 second
3. ✅ Data structure matches frontend expectations
4. ✅ Error handling works for invalid inputs
5. ✅ Real-time updates function properly
6. ✅ Performance is consistent under load

## 🎉 **You're Ready!**

With these comprehensive tests, you can:
- Verify all functionality works correctly
- Catch edge cases and errors
- Ensure performance meets requirements
- Validate data structures for frontend integration
- Test in both development and production environments

**Start with the comprehensive test script for the fastest validation!**
