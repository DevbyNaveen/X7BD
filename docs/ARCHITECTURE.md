# 🏗️ System Architecture - Analytics Dashboard Service

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND CLIENTS                          │
│  (Web Dashboard, Mobile App, Kitchen Display, POS Terminal)      │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ REST API                           │ WebSocket
             │                                    │
┌────────────▼────────────────────────────────────▼───────────────┐
│                  ANALYTICS DASHBOARD SERVICE                     │
│                     (FastAPI - Port 8060)                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API LAYER                              │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │  │
│  │  │  Menu   │ │Operations│ │Analytics │ │   Settings   │ │  │
│  │  │  Routes │ │  Routes  │ │  Routes  │ │    Routes    │ │  │
│  │  └─────────┘ └──────────┘ └──────────┘ └──────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  SERVICE LAYER                            │  │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐  │  │
│  │  │  Database   │ │   Real-time  │ │   PDF Processor  │  │  │
│  │  │   Service   │ │   WebSocket  │ │                  │  │  │
│  │  └─────────────┘ └──────────────┘ └──────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  DATA MODELS                              │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │  │
│  │  │  Menu   │ │Operations│ │Inventory │ │   Analytics  │ │  │
│  │  │ Models  │ │  Models  │ │  Models  │ │    Models    │ │  │
│  │  └─────────┘ └──────────┘ └──────────┘ └──────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ Supabase Client                    │ Event Publishing
             │                                    │
┌────────────▼────────────────────────────────────▼───────────────┐
│                      SUPABASE PLATFORM                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  PostgreSQL Database                      │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │  │
│  │  │ Menus  │ │ Tables │ │ Staff  │ │ Orders │ │Analytics│ │  │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Real-time Subscriptions                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow

### REST API Request Flow

```
Client Request
    │
    ▼
┌─────────────────┐
│  FastAPI Router │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Pydantic Model  │ ◄── Input Validation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Route Handler   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Database Service│ ◄── Business Logic
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Supabase Client │ ◄── Database Query
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PostgreSQL DB   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Response Model  │ ◄── Output Formatting
└────────┬────────┘
         │
         ▼
    JSON Response
```

### WebSocket Event Flow

```
Database Change
    │
    ▼
┌─────────────────────┐
│  Event Publisher    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Connection Manager  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Broadcast to Clients│
└──────────┬──────────┘
           │
           ▼
    ┌──────┴──────┐
    │             │
    ▼             ▼
Dashboard      Kitchen
 Client        Display
```

---

## 📊 Data Flow Diagram

### Menu Management Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Create  │────▶│ Validate │────▶│  Insert  │────▶│ Publish  │
│   Item   │     │   Data   │     │    DB    │     │  Event   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                          │
                                                          ▼
                                                   ┌──────────┐
                                                   │WebSocket │
                                                   │Broadcast │
                                                   └──────────┘
```

### Order Processing Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Order   │────▶│  Table   │────▶│   KDS    │────▶│ Kitchen  │
│ Created  │     │ Assigned │     │  Order   │     │ Display  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                 │                 │
     ▼                ▼                 ▼                 ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│Dashboard │     │  Table   │     │  Staff   │     │  Timer   │
│  Update  │     │  Status  │     │  Alert   │     │  Start   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

### Analytics Pipeline

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   Raw    │────▶│Aggregate │────▶│  Cache   │────▶│  Serve   │
│  Events  │     │   Data   │     │ Metrics  │     │  Client  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │
     ▼
┌──────────┐
│  Daily   │
│ Summary  │
└──────────┘
```

---

## 🔌 API Architecture

### Endpoint Organization

```
/api/v1/
├── menu/
│   ├── categories/          # Menu categories
│   ├── items/              # Menu items
│   └── modifiers/          # Item modifiers
│
├── operations/
│   ├── locations/          # Business locations
│   ├── tables/             # Table management
│   ├── floor-plans/        # Floor layouts
│   ├── kds/                # Kitchen display
│   ├── staff/              # Staff management
│   ├── schedules/          # Staff scheduling
│   └── time-clock/         # Time tracking
│
├── analytics/
│   ├── realtime/           # Live metrics
│   ├── dashboard/          # Comprehensive dashboard
│   ├── sales/              # Sales analytics
│   ├── menu/               # Menu analytics
│   ├── financial/          # Financial reports
│   ├── operations/         # Operational metrics
│   └── reports/            # Report generation
│
├── business-settings/
│   ├── settings/           # General settings
│   ├── working-hours/      # Business hours
│   └── integrations/       # Third-party integrations
│
└── ws/
    ├── dashboard/          # Dashboard WebSocket
    ├── kds/                # Kitchen WebSocket
    └── tables/             # Tables WebSocket
```

---

## 🗄️ Database Schema

### Core Tables

```
businesses
├── id (uuid)
├── business_id (text)
├── name
├── slug
├── category_id
└── status

business_settings
├── business_id (uuid) [FK]
├── notifications (jsonb)
├── preferences (jsonb)
├── business_hours (jsonb)
└── integrations (jsonb)

locations
├── id (uuid)
├── business_id (uuid) [FK]
├── name
├── address
├── timezone
└── is_active
```

### Menu Tables

```
menu_categories
├── id (uuid)
├── business_id (uuid) [FK]
├── name
├── parent_id (uuid) [FK]
├── display_order
└── is_active

menu_items
├── id (uuid)
├── business_id (uuid) [FK]
├── category_id (uuid) [FK]
├── name
├── price
├── cost
├── modifiers (jsonb)
└── is_available

item_modifiers
├── id (uuid)
├── business_id (uuid) [FK]
├── name
├── type
└── options (jsonb)
```

### Operations Tables

```
tables
├── id (uuid)
├── business_id (uuid) [FK]
├── location_id (uuid) [FK]
├── table_number
├── capacity
├── status
└── current_order_id (uuid) [FK]

kds_orders
├── id (uuid)
├── business_id (uuid) [FK]
├── order_id (uuid) [FK]
├── station
├── priority
├── status
└── items (jsonb)

staff_members
├── id (uuid)
├── business_id (uuid) [FK]
├── first_name
├── last_name
├── position
└── hourly_rate

time_clock
├── id (uuid)
├── business_id (uuid) [FK]
├── staff_id (uuid) [FK]
├── clock_in
├── clock_out
├── total_hours
└── overtime_hours
```

### Analytics Tables

```
daily_sales_summary
├── id (uuid)
├── business_id (uuid) [FK]
├── date
├── total_revenue
├── total_orders
├── avg_order_value
└── customer_count

item_performance
├── id (uuid)
├── business_id (uuid) [FK]
├── menu_item_id (uuid) [FK]
├── date
├── quantity_sold
├── revenue
└── profit
```

---

## 🔐 Security Architecture

### Authentication Flow

```
Client Request
    │
    ▼
┌─────────────────┐
│ API Gateway     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ JWT Validation  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RLS Check       │ ◄── Row Level Security
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Business Logic  │
└─────────────────┘
```

### Authorization Layers

```
┌─────────────────────────────────────┐
│         Service Key Auth            │ ◄── Admin/Service Access
├─────────────────────────────────────┤
│         JWT Token Auth              │ ◄── User Access
├─────────────────────────────────────┤
│    Row Level Security (RLS)         │ ◄── Data Isolation
├─────────────────────────────────────┤
│      Business ID Filtering          │ ◄── Multi-tenant
└─────────────────────────────────────┘
```

---

## 🚀 Deployment Architecture

### Production Setup

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
└────────────┬────────────────────────────┬───────────────┘
             │                            │
    ┌────────▼────────┐          ┌────────▼────────┐
    │   Instance 1    │          │   Instance 2    │
    │  Analytics API  │          │  Analytics API  │
    └────────┬────────┘          └────────┬────────┘
             │                            │
             └────────────┬───────────────┘
                          │
                ┌─────────▼─────────┐
                │   Supabase DB     │
                │   (PostgreSQL)    │
                └───────────────────┘
```

### Monitoring Stack

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Prometheus     │────▶│    Grafana      │────▶│     Alerts      │
│   (Metrics)     │     │  (Dashboards)   │     │   (PagerDuty)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         ▲
         │
┌─────────────────┐
│  Analytics API  │
│  (Metrics)      │
└─────────────────┘
```

---

## 📈 Scalability Design

### Horizontal Scaling

```
                    ┌─────────────┐
                    │   Client    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │Load Balancer│
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
   │Instance │        │Instance │        │Instance │
   │    1    │        │    2    │        │    N    │
   └────┬────┘        └────┬────┘        └────┬────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Database   │
                    │   Cluster   │
                    └─────────────┘
```

### Caching Strategy

```
┌─────────────────┐
│     Client      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API Service    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│ Redis │ │  DB   │
│ Cache │ │       │
└───────┘ └───────┘
```

---

## 🔄 Event-Driven Architecture

### Event Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Action    │────▶│   Event     │────▶│  Handlers   │
│  (Create)   │     │  Publisher  │     │             │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┘
                    │
        ┌───────────┼───────────┬───────────┐
        │           │           │           │
        ▼           ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
   │WebSocket│ │Database│ │Analytics│ │  Cache │
   │Broadcast│ │  Log   │ │ Update  │ │ Update │
   └────────┘  └────────┘  └────────┘  └────────┘
```

---

## 🎯 Performance Optimization

### Query Optimization

```
┌─────────────────┐
│  Request        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Check Cache    │ ◄── 5-min TTL
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
  Cache     Database
   Hit       Query
    │         │
    └────┬────┘
         │
         ▼
┌─────────────────┐
│  Response       │
└─────────────────┘
```

### Connection Pooling

```
┌─────────────────────────────────────┐
│         Connection Pool             │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐       │
│  │Conn│ │Conn│ │Conn│ │Conn│ ...   │
│  └────┘ └────┘ └────┘ └────┘       │
└────────────────┬────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │   Database    │
         └───────────────┘
```

---

## 🔍 Monitoring & Observability

### Metrics Collection

```
┌─────────────────┐
│  Application    │
│   Metrics       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Prometheus     │
│   Exporter      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Time Series    │
│   Database      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Grafana       │
│  Dashboards     │
└─────────────────┘
```

### Health Checks

```
┌─────────────────┐
│  /health        │ ◄── General Health
├─────────────────┤
│  /health/live   │ ◄── Liveness Probe
├─────────────────┤
│  /health/ready  │ ◄── Readiness Probe
└─────────────────┘
```

---

## 📝 Summary

This architecture provides:

✅ **Scalability** - Horizontal scaling with load balancing
✅ **Reliability** - Connection pooling, error handling
✅ **Performance** - Caching, async operations
✅ **Security** - Multi-layer authentication
✅ **Observability** - Metrics, logs, health checks
✅ **Real-time** - WebSocket event system
✅ **Maintainability** - Clean separation of concerns

The system is designed for **enterprise-grade performance and reliability** while maintaining **developer-friendly architecture**.
