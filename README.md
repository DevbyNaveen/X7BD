# 📊 Analytics Dashboard Service

Enterprise-grade analytics platform for food & hospitality businesses with real-time insights, AI-powered analytics, and comprehensive reporting.

## ✨ NEW: Authentication Integration

**Full authentication system now integrated!** 
- Business registration with direct Supabase
- Login/logout with JWT tokens
- Role-based access control (Owner, Admin, Staff)
- Protected routes with middleware
- Multi-category business support

📖 **[Read the Auth Integration Guide](docs/AUTH_INTEGRATION.md)**

## 🚀 Quick Start

### Docker (Recommended)
```bash
docker-compose up -d
```

### Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start service
uvicorn app.main:app --host 0.0.0.0 --port 8060 --reload
```

Service will be available at: http://localhost:8060

## 📚 Documentation

- **API Docs**: http://localhost:8060/docs (when running)
- **Full Reference**: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- **Frontend Guide**: [docs/frontend.md](docs/frontend.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **Cache**: Redis
- **Messaging**: Kafka
- **AI**: OpenAI integration
- **Deployment**: Docker/Kubernetes

## 📊 Features

- Real-time analytics and KPIs
- Multi-business type support (Restaurant, Cafe, Bar)
- PDF processing and AI extraction
- WebSocket real-time updates
- Comprehensive reporting (PDF/Excel)
- Inventory management
- Menu management
- Business intelligence dashboard

## 🔧 Environment Setup

1. Copy `.env.example` to `.env`
2. Configure Supabase credentials
3. Ensure Redis and Kafka are running
4. Start the service

## 📞 API Endpoints

### Authentication (NEW!)
- `POST /api/v1/auth/register/business` - Register new business
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout

### Analytics
- `GET /api/v1/analytics/realtime/{business_id}` - Real-time metrics
- `GET /api/v1/analytics/historical/{business_id}` - Historical data

### Menu Management
- `GET /api/v1/menu/items` - List menu items
- `POST /api/v1/menu/categories` - Create category

### Business Settings (Protected)
- `GET /api/v1/business-settings/{business_id}` - Get settings
- `PUT /api/v1/business-settings/{business_id}` - Update settings
- `GET /api/v1/business-settings/{business_id}/working-hours` - Get hours
- `PUT /api/v1/business-settings/{business_id}/working-hours` - Update hours

### Reports
- `POST /api/v1/reports/generate` - Generate reports

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📋 Testing

```bash
# Run tests
python -m pytest tests/

# Test authentication integration
python test_auth.py

# Import Postman collection
# File: postman_collection.json
```

## 📄 License

Proprietary - All Rights Reserved
