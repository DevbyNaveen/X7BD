# Food QR Database Setup Guide

This guide will help you set up the necessary database tables in Supabase for the Food QR backend functionality.

## 🚀 Quick Setup (Recommended)

### Option 1: Automated Setup
```bash
# Run the automated setup script
python setup_food_qr_database.py
```

### Option 2: Manual SQL Execution
1. Open your Supabase dashboard
2. Go to SQL Editor
3. Copy and paste the contents of `database_migrations/create_food_qr_tables_simple.sql`
4. Click "Run" to execute

## 📋 Required Tables

The Food QR backend requires these database tables:

### Core Tables (Essential)
- **`qr_codes`** - Stores QR code metadata and configuration
- **`qr_scans`** - Tracks QR code scan events for analytics
- **`tables`** - Manages restaurant tables with QR codes
- **`business_locations`** - Stores business location information

### Optional Tables (Advanced Features)
- **`food_tracking_events`** - Tracks food item lifecycle events
- **`pos_integrations`** - Manages POS system integrations
- **`qr_code_templates`** - Stores QR code appearance templates
- **`qr_code_exports`** - Tracks QR code export requests

## 🔧 Environment Variables

Make sure these are set in your `.env` file:

```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

## 📊 Table Schemas

### qr_codes
```sql
CREATE TABLE qr_codes (
    id TEXT PRIMARY KEY,
    type VARCHAR(50) NOT NULL, -- menu_item, table, order, menu_category, business
    target_id UUID NOT NULL,
    business_id UUID NOT NULL,
    qr_data TEXT NOT NULL,
    size INTEGER DEFAULT 200,
    format VARCHAR(10) DEFAULT 'png',
    include_logo BOOLEAN DEFAULT FALSE,
    custom_data JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    scan_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);
```

### qr_scans
```sql
CREATE TABLE qr_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qr_id TEXT NOT NULL,
    qr_type VARCHAR(50) NOT NULL,
    target_id UUID NOT NULL,
    business_id UUID NOT NULL,
    scanner_location TEXT,
    scanner_id TEXT,
    user_agent TEXT,
    ip_address TEXT,
    scanned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### tables
```sql
CREATE TABLE tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_number VARCHAR(50) NOT NULL,
    business_id UUID NOT NULL,
    location_id UUID,
    capacity INTEGER CHECK (capacity >= 1 AND capacity <= 20),
    qr_code_id TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(business_id, table_number)
);
```

## 🔍 Verification

After setup, verify the tables exist:

```sql
-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('qr_codes', 'qr_scans', 'tables', 'business_locations');
```

## 🧪 Testing

Test the setup with sample data:

```sql
-- Insert sample business location
INSERT INTO business_locations (business_id, name, address, city, state, zip_code, country, phone, email)
VALUES (
    '123e4567-e89b-12d3-a456-426614174000'::uuid,
    'Test Restaurant',
    '123 Test Street',
    'Test City',
    'TS',
    '12345',
    'USA',
    '+1-555-TEST',
    'test@restaurant.com'
);

-- Insert sample table
INSERT INTO tables (table_number, business_id, capacity)
VALUES ('1', '123e4567-e89b-12d3-a456-426614174000'::uuid, 4);
```

## 🚨 Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure your Supabase key has the correct permissions
   - Check if RLS (Row Level Security) is blocking operations

2. **Table Already Exists**
   - The scripts use `CREATE TABLE IF NOT EXISTS` so this shouldn't be an issue
   - If you get errors, try dropping tables first: `DROP TABLE IF EXISTS qr_codes CASCADE;`

3. **Foreign Key Errors**
   - Make sure referenced tables exist first
   - Check that UUIDs are valid format

4. **RLS Policy Issues**
   - If you enabled RLS, you may need to create policies
   - For testing, you can disable RLS: `ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;`

### Manual Verification

```sql
-- Check table structure
\d qr_codes

-- Check indexes
\di

-- Check constraints
SELECT conname, contype 
FROM pg_constraint 
WHERE conrelid = 'qr_codes'::regclass;
```

## 📈 Next Steps

1. **Start the API server**: `python -m app.main`
2. **Test QR generation**: Use the API endpoints
3. **Create your first QR code**: POST to `/api/v1/food/qr/generate`
4. **Monitor analytics**: Check scan events in `qr_scans` table

## 🔗 Related Files

- `database_migrations/create_food_qr_tables_simple.sql` - Basic setup
- `database_migrations/create_food_qr_tables.sql` - Full setup with advanced features
- `setup_food_qr_database.py` - Automated setup script
- `test_food_qr.py` - Test script for functionality

## 📞 Support

If you encounter issues:
1. Check the Supabase logs in your dashboard
2. Verify environment variables are correct
3. Ensure your Supabase project is active
4. Check the API documentation at `/docs` endpoint

---

**Note**: This setup creates the database structure for the Food QR backend. The actual QR code generation and scanning functionality is handled by the Python API endpoints.
