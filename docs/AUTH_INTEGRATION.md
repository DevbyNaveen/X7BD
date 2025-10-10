# Authentication Integration - Dashboard Service

## Overview

The Analytics Dashboard Service now has complete authentication integration with two flows:

1. **Business Registration**: Direct Supabase integration for new business signup
2. **Login & Usage**: Backend authentication through Supabase with token validation

## Architecture

```
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │
       ├─── Registration ──────────────────────┐
       │                                       │
       │                                       ▼
       │                          ┌────────────────────────┐
       │                          │  Dashboard Service     │
       │                          │  /api/v1/auth/register │
       │                          └───────────┬────────────┘
       │                                      │
       │                                      ▼
       │                          ┌────────────────────────┐
       │                          │  Supabase (Direct)     │
       │                          │  - Auth                │
       │                          │  - Database            │
       │                          └────────────────────────┘
       │
       ├─── Login ─────────────────────────────┐
       │                                       │
       │                                       ▼
       │                          ┌────────────────────────┐
       │                          │  Dashboard Service     │
       │                          │  /api/v1/auth/login    │
       │                          └───────────┬────────────┘
       │                                      │
       │                                      ▼
       │                          ┌────────────────────────┐
       │                          │  Supabase Auth         │
       │                          │  Token Validation      │
       │                          └────────────────────────┘
       │
       └─── Protected Routes ──────────────────┐
                                               │
                                               ▼
                                  ┌────────────────────────┐
                                  │  Auth Middleware       │
                                  │  - Verify JWT Token    │
                                  │  - Check Business Role │
                                  └────────────────────────┘
```

## API Endpoints

### Authentication Routes

#### 1. Business Registration (Direct Supabase)
```http
POST /api/v1/auth/register/business
Content-Type: application/json

{
  "email": "owner@business.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "business_name": "My Restaurant",
  "business_type": "restaurant",
  "business_email": "contact@restaurant.com",
  "business_phone": "+1234567890",
  "business_address": "123 Main St",
  "timezone": "America/New_York",
  "currency": "USD"
}
```

**Response:**
```json
{
  "message": "Business registered successfully",
  "user": {
    "id": "uuid",
    "email": "owner@business.com",
    "full_name": "John Doe"
  },
  "business": {
    "id": "uuid",
    "name": "My Restaurant",
    "business_type": "restaurant",
    "status": "active"
  },
  "session": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "expires_in": 3600
  }
}
```

**What it creates:**
- User account in Supabase Auth
- User profile in `users` table
- Business profile in `businesses` table
- Owner role in `user_business_roles` table
- Default settings in `business_settings` table

#### 2. Login (Backend Authentication)
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "owner@business.com",
  "password": "SecurePass123!",
  "remember_me": false
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "owner@business.com",
    "full_name": "John Doe",
    "avatar_url": null,
    "phone_number": "+1234567890",
    "email_confirmed": true,
    "businesses": [
      {
        "id": "uuid",
        "name": "My Restaurant",
        "role": "owner",
        "business_type": "restaurant"
      }
    ]
  }
}
```

#### 3. Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}
```

#### 4. Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer eyJhbGc...
```

#### 5. Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGc...
```

#### 6. Password Reset Request
```http
POST /api/v1/auth/password/reset-request
Content-Type: application/json

{
  "email": "owner@business.com"
}
```

#### 7. Update Password
```http
POST /api/v1/auth/password/update
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "new_password": "NewSecurePass123!"
}
```

## Protected Routes

All business-related endpoints now require authentication. The middleware validates:

1. **JWT Token**: Valid and not expired
2. **Business Access**: User has a role in the requested business
3. **Role Permissions**: User has required role (owner/admin/staff)

### Example Protected Endpoints

#### Get Business Settings
```http
GET /api/v1/business-settings/{business_id}
Authorization: Bearer eyJhbGc...
```

**Requires:** Any role (owner, admin, staff)

#### Update Business Settings
```http
PUT /api/v1/business-settings/{business_id}
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "notifications": {
    "email": true,
    "sms": true,
    "push": true
  }
}
```

**Requires:** Owner or Admin role

## Authentication Middleware

### Usage in Routes

```python
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from ..middleware.auth import get_auth_middleware, security

@router.get("/{business_id}")
async def get_business_data(
    business_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify authentication
    auth_middleware = get_auth_middleware()
    user = await auth_middleware.get_current_user(credentials)
    
    # Check business access
    await auth_middleware.require_business_access(user, str(business_id))
    
    # Your logic here
    return {"data": "..."}
```

### Role-Based Access

```python
# Require owner or admin role
await auth_middleware.require_business_access(
    user, 
    str(business_id), 
    required_roles=["owner", "admin"]
)
```

## Business Types Support

The registration endpoint supports multiple business types:

- `restaurant` - Full-service restaurants
- `cafe` - Coffee shops, cafes
- `salon` - Hair salons, beauty services
- `retail` - Retail stores
- `gym` - Fitness centers
- `spa` - Spa and wellness
- `clinic` - Medical clinics
- `hotel` - Hotels and hospitality

Each business type can have customized features and modules.

## Environment Variables

Required in `.env`:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Service Configuration
ANALYTICS_PORT=8060
ANALYTICS_HOST=0.0.0.0
```

## Database Schema

### Tables Used

1. **auth.users** (Supabase Auth)
   - Managed by Supabase
   - Stores authentication credentials

2. **public.users**
   - User profiles
   - Extended user information

3. **public.businesses**
   - Business profiles
   - Business type, settings, metadata

4. **public.user_business_roles**
   - User-to-business relationships
   - Role assignments (owner, admin, staff)

5. **public.business_settings**
   - Business configuration
   - Notifications, preferences, integrations

## Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

#### 403 Forbidden
```json
{
  "detail": "You don't have access to this business"
}
```

or

```json
{
  "detail": "Requires one of these roles: owner, admin"
}
```

#### 400 Bad Request
```json
{
  "detail": "Failed to create user account"
}
```

## Testing

### Register a Business
```bash
curl -X POST http://localhost:8060/api/v1/auth/register/business \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456!",
    "full_name": "Test User",
    "business_name": "Test Restaurant",
    "business_type": "restaurant"
  }'
```

### Login
```bash
curl -X POST http://localhost:8060/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456!"
  }'
```

### Access Protected Route
```bash
curl -X GET http://localhost:8060/api/v1/business-settings/{business_id} \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Security Best Practices

1. **Token Storage**: Store tokens securely in httpOnly cookies or secure storage
2. **HTTPS Only**: Always use HTTPS in production
3. **Token Expiry**: Implement automatic token refresh
4. **Rate Limiting**: Implement rate limiting on auth endpoints
5. **Password Policy**: Enforce strong passwords (min 8 chars)
6. **Email Verification**: Verify email addresses before full access

## Integration with Frontend

### React Example

```javascript
// Register Business
const registerBusiness = async (data) => {
  const response = await fetch('http://localhost:8060/api/v1/auth/register/business', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  
  const result = await response.json();
  
  // Store tokens
  localStorage.setItem('access_token', result.session.access_token);
  localStorage.setItem('refresh_token', result.session.refresh_token);
  
  return result;
};

// Login
const login = async (email, password) => {
  const response = await fetch('http://localhost:8060/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const result = await response.json();
  
  // Store tokens
  localStorage.setItem('access_token', result.access_token);
  localStorage.setItem('refresh_token', result.refresh_token);
  
  return result;
};

// Make Authenticated Request
const getBusinessSettings = async (businessId) => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(`http://localhost:8060/api/v1/business-settings/${businessId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};
```

## Next Steps

1. **Frontend Integration**: Connect your frontend to these endpoints
2. **Email Verification**: Set up email verification in Supabase
3. **Multi-Factor Auth**: Enable MFA for enhanced security
4. **Social Login**: Add OAuth providers (Google, Facebook, etc.)
5. **Audit Logging**: Track authentication events
6. **Session Management**: Implement session tracking and management

## Support

For issues or questions:
- Check Supabase logs in the dashboard
- Review service logs: `docker logs analytics-dashboard-service`
- Verify environment variables are set correctly
