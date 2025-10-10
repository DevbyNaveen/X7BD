# API Restructuring Plan - Enterprise-Grade Architecture

## Analysis Date: 2025-10-08

## Executive Summary

This document outlines the comprehensive API restructuring plan for the analytics-dashboard-service to achieve enterprise-grade consistency, eliminate duplications, and establish clear separation between common and category-specific endpoints.

---

## 1. Current State Analysis

### Templates Analyzed:
1. **Food & Hospitality** (menu.py, inventory.py, operations.py)
2. **Service-Based** (service_based.py) - Salons, Spas, Gyms
3. **Retail** (retail.py) - Stores, Boutiques, Pharmacies
4. **Professional Services** (professional.py) - Law Firms, Consulting, Agencies

### Critical Issues Identified:

#### A. Naming Inconsistencies
- **Customer Management:** `clients` (Service-Based) vs `customers` (Retail)
- **Items:** `menu_items` (Food) vs `products` (Retail) vs `services` (Service-Based)
- **Staff:** `staff_members` (Operations) vs `resources` (Professional)

#### B. Duplicate CRUD Patterns
Every template repeats the same CRUD pattern:
```
POST   /{entity}              - Create
GET    /{entity}              - List
GET    /{entity}/{id}         - Get by ID
PUT    /{entity}/{id}         - Update
DELETE /{entity}/{id}         - Delete
```

#### C. Overlapping Functionality
- Customer/Client management duplicated across Service-Based and Retail
- Analytics endpoints scattered across multiple files
- Inventory tracking in both Menu and Retail templates

---

## 2. Enterprise-Grade Structure

### A. Common Endpoints (Work Across ALL Templates)

These endpoints should be standardized and available for all business types:

#### **Customer Management** (Unified)
```
POST   /api/v1/customers                    - Create customer
GET    /api/v1/customers                    - List customers
GET    /api/v1/customers/{id}               - Get customer
PUT    /api/v1/customers/{id}               - Update customer
DELETE /api/v1/customers/{id}               - Delete customer
GET    /api/v1/customers/{id}/history       - Customer history
GET    /api/v1/customers/{id}/analytics     - Customer analytics
```

**Applies to:** All templates (clients, customers, patients, etc.)

#### **Staff Management** (Unified)
```
POST   /api/v1/staff                        - Create staff member
GET    /api/v1/staff                        - List staff
GET    /api/v1/staff/{id}                   - Get staff member
PUT    /api/v1/staff/{id}                   - Update staff member
DELETE /api/v1/staff/{id}                   - Delete staff member
GET    /api/v1/staff/active                 - Currently active staff
```

**Applies to:** All templates

#### **Time Tracking** (Unified)
```
POST   /api/v1/time-clock/clock-in          - Clock in
PUT    /api/v1/time-clock/{id}/clock-out    - Clock out
GET    /api/v1/time-clock                   - List time entries
GET    /api/v1/time-clock/active            - Currently clocked in
```

**Applies to:** All templates

#### **Analytics** (Unified)
```
GET    /api/v1/analytics/dashboard/{business_id}     - Main dashboard
GET    /api/v1/analytics/realtime/{business_id}      - Real-time metrics
GET    /api/v1/analytics/sales/summary               - Sales summary
GET    /api/v1/analytics/financial/summary           - Financial summary
GET    /api/v1/analytics/customers/insights          - Customer insights
```

**Applies to:** All templates

#### **Business Settings** (Unified)
```
GET    /api/v1/business/{id}                - Get business details
PUT    /api/v1/business/{id}                - Update business
GET    /api/v1/business/{id}/settings       - Get settings
PUT    /api/v1/business/{id}/settings       - Update settings
```

**Applies to:** All templates

---

### B. Category-Specific Endpoints

#### **Food & Hospitality Template**

**Menu Management:**
```
POST   /api/v1/food/menu/categories         - Create category
GET    /api/v1/food/menu/categories         - List categories
POST   /api/v1/food/menu/items              - Create menu item
GET    /api/v1/food/menu/items              - List menu items
GET    /api/v1/food/menu/items/{id}         - Get menu item
PUT    /api/v1/food/menu/items/{id}         - Update menu item
DELETE /api/v1/food/menu/items/{id}         - Delete menu item
POST   /api/v1/food/menu/items/bulk-update  - Bulk update items
```

**Table Management:**
```
POST   /api/v1/food/tables                  - Create table
GET    /api/v1/food/tables                  - List tables
PUT    /api/v1/food/tables/{id}             - Update table
POST   /api/v1/food/tables/assign           - Assign table to order
POST   /api/v1/food/tables/{id}/release     - Release table
```

**Kitchen Display System:**
```
POST   /api/v1/food/kds/orders              - Send order to kitchen
GET    /api/v1/food/kds/orders              - List kitchen orders
PUT    /api/v1/food/kds/orders/{id}         - Update order status
GET    /api/v1/food/kds/performance         - Kitchen performance
```

**Inventory (Food-specific):**
```
POST   /api/v1/food/inventory/items         - Create inventory item
GET    /api/v1/food/inventory/items         - List inventory items
PUT    /api/v1/food/inventory/items/{id}    - Update inventory item
POST   /api/v1/food/inventory/adjustments   - Adjust stock
GET    /api/v1/food/inventory/alerts/active - Active stock alerts
```

---

#### **Service-Based Template**

**Service Management:**
```
POST   /api/v1/services/offerings           - Create service offering
GET    /api/v1/services/offerings           - List services
GET    /api/v1/services/offerings/{id}      - Get service
PUT    /api/v1/services/offerings/{id}      - Update service
DELETE /api/v1/services/offerings/{id}      - Delete service
```

**Appointment Management:**
```
POST   /api/v1/services/appointments        - Create appointment
GET    /api/v1/services/appointments        - List appointments
GET    /api/v1/services/appointments/{id}   - Get appointment
PUT    /api/v1/services/appointments/{id}   - Update appointment
DELETE /api/v1/services/appointments/{id}   - Cancel appointment
```

---

#### **Retail Template**

**Product Management:**
```
POST   /api/v1/retail/products              - Create product
GET    /api/v1/retail/products              - List products
GET    /api/v1/retail/products/{id}         - Get product
PUT    /api/v1/retail/products/{id}         - Update product
DELETE /api/v1/retail/products/{id}         - Delete product
POST   /api/v1/retail/products/{id}/adjust-inventory - Adjust inventory
```

**Loyalty Program:**
```
POST   /api/v1/retail/customers/{id}/loyalty-points - Adjust loyalty points
GET    /api/v1/retail/loyalty/tiers         - Get loyalty tiers
```

---

#### **Professional Services Template**

**Project Management:**
```
POST   /api/v1/professional/projects        - Create project
GET    /api/v1/professional/projects        - List projects
GET    /api/v1/professional/projects/{id}   - Get project
PUT    /api/v1/professional/projects/{id}   - Update project
DELETE /api/v1/professional/projects/{id}   - Delete project
```

**Billable Time:**
```
POST   /api/v1/professional/time-entries    - Create time entry
GET    /api/v1/professional/time-entries    - List time entries
PUT    /api/v1/professional/time-entries/{id} - Update time entry
DELETE /api/v1/professional/time-entries/{id} - Delete time entry
```

**Invoicing:**
```
POST   /api/v1/professional/invoices        - Create invoice
GET    /api/v1/professional/invoices        - List invoices
GET    /api/v1/professional/invoices/{id}   - Get invoice
PUT    /api/v1/professional/invoices/{id}   - Update invoice
POST   /api/v1/professional/invoices/{id}/mark-paid - Mark as paid
```

**Resource Management:**
```
POST   /api/v1/professional/resources       - Create resource
GET    /api/v1/professional/resources       - List resources
POST   /api/v1/professional/resource-allocations - Allocate resource
```

---

## 3. Naming Conventions (Enterprise Standard)

### A. Endpoint Naming Rules

1. **Use plural nouns:** `/customers`, `/products`, `/services`
2. **Use kebab-case:** `/time-entries`, `/loyalty-points`, `/clock-in`
3. **Prefix with template:** `/api/v1/{template}/{resource}`
4. **Common endpoints:** `/api/v1/{resource}` (no template prefix)

### B. Unified Entity Names

| Concept | Standardized Name | Used In |
|---------|------------------|---------|
| Customer/Client/Patient | `customers` | All templates |
| Staff/Employee/Resource | `staff` | All templates |
| Menu Item/Product/Service | Template-specific | Each template |
| Time Tracking | `time-clock` | All templates |
| Business Location | `locations` | All templates |

### C. Query Parameter Standards

**Pagination:**
```
?limit=100&offset=0
```

**Filtering:**
```
?business_id={uuid}
?category={string}
?status={string}
?is_active={boolean}
```

**Date Ranges:**
```
?start_date={YYYY-MM-DD}
?end_date={YYYY-MM-DD}
```

**Search:**
```
?search={string}
```

---

## 4. Implementation Plan

### Phase 1: Standardize Common Endpoints
- [ ] Consolidate customer/client management into unified `/api/v1/customers`
- [ ] Consolidate staff management into unified `/api/v1/staff`
- [ ] Consolidate time tracking into unified `/api/v1/time-clock`
- [ ] Keep analytics in unified `/api/v1/analytics`

### Phase 2: Restructure Category-Specific Endpoints
- [ ] Add template prefix to Food & Hospitality: `/api/v1/food/*`
- [ ] Add template prefix to Service-Based: `/api/v1/services/*`
- [ ] Add template prefix to Retail: `/api/v1/retail/*`
- [ ] Add template prefix to Professional: `/api/v1/professional/*`

### Phase 3: Update Route Files
- [ ] Refactor `service_based.py` - move common to universal, keep specific
- [ ] Refactor `retail.py` - move common to universal, keep specific
- [ ] Refactor `professional.py` - move common to universal, keep specific
- [ ] Refactor `menu.py` - add `/food` prefix, keep structure
- [ ] Refactor `inventory.py` - add `/food` prefix
- [ ] Refactor `operations.py` - split common vs food-specific

### Phase 4: Update Models
- [ ] Rename `ClientCreate/Response` to `CustomerCreate/Response` in service_based
- [ ] Ensure consistent field naming across all customer models
- [ ] Standardize metadata fields

---

## 5. Migration Strategy

### Backward Compatibility
- Keep old endpoints active with deprecation warnings
- Add `X-Deprecated` header to old endpoints
- Provide 3-month migration period

### Documentation
- Update API documentation with new structure
- Provide migration guide for existing integrations
- Add examples for each template

---

## 6. Expected Benefits

1. **Reduced Code Duplication:** ~40% reduction in duplicate code
2. **Improved Maintainability:** Single source of truth for common operations
3. **Better Developer Experience:** Clear separation of concerns
4. **Easier Testing:** Standardized patterns across templates
5. **Scalability:** Easy to add new templates following established patterns

---

## 7. Next Steps

1. Review and approve this restructuring plan
2. Create feature branch for restructuring
3. Implement Phase 1 (Common endpoints)
4. Test thoroughly with existing integrations
5. Roll out incrementally with monitoring
