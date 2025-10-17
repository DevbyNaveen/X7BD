# Food QR Code Backend

A comprehensive QR code management system for food businesses, providing enterprise-grade functionality for menu items, table ordering, and food tracking.

## Features

### 🎯 QR Code Generation
- **Menu Items**: Generate QR codes for individual food items
- **Tables**: Create QR codes for table ordering systems
- **Orders**: Generate QR codes for order tracking
- **Categories**: QR codes for menu categories
- **Business**: Overall business QR codes

### 📱 QR Code Formats
- **PNG**: High-quality raster images
- **SVG**: Scalable vector graphics
- **Base64**: Encoded data for API responses
- **Customizable sizes**: 100x100 to 1000x1000 pixels

### 🔍 QR Code Scanning & Validation
- **Real-time scanning**: Validate QR codes instantly
- **Data extraction**: Parse QR code content
- **Action routing**: Determine next steps based on QR type
- **Analytics tracking**: Monitor scan events

### 📊 Analytics & Tracking
- **Scan metrics**: Total scans, unique scans, frequency
- **Popular items**: Most scanned QR codes
- **Time patterns**: Peak scanning hours
- **Conversion tracking**: Scans to actions

### 🍽️ Food Item Management
- **Auto QR generation**: Automatically create QR codes for new items
- **Integration**: Seamless integration with existing menu system
- **Tracking**: Enable QR-based food tracking from creation

### 🪑 Table Management
- **Table QR codes**: Unique QR codes per table
- **Ordering interface**: Direct link to menu
- **Location tracking**: Track table locations
- **Capacity management**: Manage table seating

## API Endpoints

### QR Code Generation
```
POST /api/v1/food/qr/generate
POST /api/v1/food/qr/bulk-generate
GET  /api/v1/food/qr/image/{qr_id}
```

### QR Code Scanning
```
POST /api/v1/food/qr/scan
```

### Analytics
```
GET /api/v1/food/qr/analytics/{business_id}
GET /api/v1/food/qr/popular/{business_id}
```

### Food Items
```
POST /api/v1/food/items
GET  /api/v1/food/items/{item_id}/qr
```

### Table Management
```
POST /api/v1/food/tables/qr
GET  /api/v1/food/tables/{business_id}/qr-codes
```

### QR Code Management
```
GET    /api/v1/food/qr/list/{business_id}
DELETE /api/v1/food/qr/{qr_id}
PUT    /api/v1/food/qr/{qr_id}/regenerate
```

### Integration & Export
```
POST /api/v1/food/qr/integrate/pos
GET  /api/v1/food/qr/export/{business_id}
```

## Installation

### Dependencies
The following dependencies are required:

```bash
pip install qrcode[pil]==7.4.2
```

### Database Setup
The system integrates with the existing Supabase database. Ensure the following tables exist:

- `menu_items` - For food item data
- `menu_categories` - For category data
- `qr_codes` - For QR code metadata (optional)
- `qr_scans` - For scan event tracking (optional)
- `tables` - For table management (optional)

## Usage Examples

### Generate QR Code for Menu Item
```python
from app.routes.food import QRCodeRequest, generate_qr_code
from uuid import uuid4

# Create QR code request
request = QRCodeRequest(
    type="menu_item",
    target_id=uuid4(),
    business_id=uuid4(),
    size=200,
    format="png"
)

# Generate QR code
qr_response = await generate_qr_code(request)
print(f"QR Code ID: {qr_response.qr_id}")
print(f"QR Data: {qr_response.qr_data}")
```

### Scan QR Code
```python
from app.routes.food import QRScanRequest, scan_qr_code

# Create scan request
scan_request = QRScanRequest(
    qr_data="https://app.example.com/food/menu_item/item-id",
    scanner_location="restaurant_floor",
    scanner_id="scanner_001"
)

# Scan QR code
scan_response = await scan_qr_code(scan_request)
print(f"Valid: {scan_response.valid}")
print(f"Action URL: {scan_response.action_url}")
```

### Create Food Item with QR Code
```python
from app.models.menu import MenuItemCreate
from app.routes.food import create_food_item_with_qr

# Create menu item
item = MenuItemCreate(
    business_id=uuid4(),
    name="Margherita Pizza",
    description="Classic tomato and mozzarella pizza",
    price=Decimal("12.99"),
    category_id=uuid4()
)

# Create item with QR code
item_with_qr = await create_food_item_with_qr(item, generate_qr=True)
print(f"Item created with QR: {item_with_qr['qr_code']}")
```

## Configuration

### Environment Variables
```bash
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# QR Code Settings
QR_BASE_URL=https://app.example.com/food
QR_DEFAULT_SIZE=200
QR_DEFAULT_FORMAT=png

# Analytics
ANALYTICS_ENABLED=true
SCAN_TRACKING_ENABLED=true
```

### QR Code Templates
Customize QR code appearance with templates:

```python
template = {
    "logo_url": "https://example.com/logo.png",
    "colors": {
        "fill": "#000000",
        "background": "#FFFFFF"
    },
    "border": 4,
    "box_size": 10
}
```

## Integration

### POS System Integration
Integrate with popular POS systems:

- **Square**: Sync menu items and QR codes
- **Toast**: Real-time menu updates
- **Clover**: Order tracking integration
- **Lightspeed**: Inventory synchronization

### Frontend Integration
The QR codes can be integrated with frontend applications:

```javascript
// Scan QR code
const scanQR = async (qrData) => {
  const response = await fetch('/api/v1/food/qr/scan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ qr_data: qrData })
  });
  
  const result = await response.json();
  if (result.valid) {
    window.location.href = result.action_url;
  }
};
```

## Testing

### Run Test Suite
```bash
python test_food_qr.py
```

### Manual Testing
1. Start the FastAPI server:
```bash
python -m app.main
```

2. Test QR generation:
```bash
curl -X POST "http://localhost:8060/api/v1/food/qr/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "menu_item",
    "target_id": "123e4567-e89b-12d3-a456-426614174000",
    "business_id": "123e4567-e89b-12d3-a456-426614174001",
    "size": 200,
    "format": "png"
  }'
```

3. Test QR scanning:
```bash
curl -X POST "http://localhost:8060/api/v1/food/qr/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "qr_data": "https://app.example.com/food/menu_item/test-item",
    "scanner_location": "test_location"
  }'
```

## Analytics Dashboard

### Key Metrics
- **Total Scans**: Overall QR code usage
- **Unique Scans**: Distinct users scanning
- **Scan Frequency**: Average scans per day/hour
- **Popular Items**: Most scanned menu items
- **Peak Hours**: Busiest scanning times
- **Conversion Rate**: Scans leading to orders

### Reports
Generate comprehensive reports:
- Daily/weekly/monthly scan reports
- Item popularity analysis
- Table usage statistics
- Customer behavior insights

## Security

### QR Code Security
- **Validation**: All QR codes are validated before processing
- **Expiration**: QR codes can have expiration dates
- **Rate Limiting**: Prevent abuse with scan rate limits
- **Audit Trail**: Complete scan event logging

### Data Protection
- **Encryption**: Sensitive data encrypted in QR codes
- **Access Control**: Role-based access to QR management
- **Privacy**: Customer scan data anonymized

## Performance

### Optimization
- **Caching**: QR code images cached for fast access
- **CDN**: Static QR images served via CDN
- **Database**: Optimized queries for scan analytics
- **Async Processing**: Background tasks for bulk operations

### Scalability
- **Horizontal Scaling**: Multiple server instances
- **Load Balancing**: Distribute QR generation load
- **Database Sharding**: Partition scan data by business
- **Caching Layer**: Redis for frequently accessed data

## Troubleshooting

### Common Issues

1. **QR Code Generation Fails**
   - Check database connection
   - Verify target item exists
   - Ensure proper permissions

2. **Scan Validation Errors**
   - Verify QR code format
   - Check target item status
   - Validate business permissions

3. **Performance Issues**
   - Monitor database queries
   - Check cache hit rates
   - Review server resources

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m app.main
```

## Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run tests: `python test_food_qr.py`
5. Start development server: `python -m app.main --reload`

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive docstrings
- Include unit tests

## License

This project is part of the X-sevenAI Analytics & Dashboard Service.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation wiki

---

**Note**: This is an enterprise-grade QR code management system designed for food businesses. It provides comprehensive functionality for menu management, table ordering, and customer engagement through QR codes.
