-- Food QR Database Tables - Simple Version
-- Creates the essential tables for QR code functionality

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- QR Codes table - stores QR code metadata and configuration
CREATE TABLE IF NOT EXISTS qr_codes (
    id TEXT PRIMARY KEY DEFAULT 'qr_' || extract(epoch from now())::text || '_' || substr(md5(random()::text), 1, 8),
    type VARCHAR(50) NOT NULL CHECK (type IN ('menu_item', 'table', 'order', 'menu_category', 'business')),
    target_id UUID NOT NULL,
    business_id UUID NOT NULL,
    qr_data TEXT NOT NULL,
    size INTEGER DEFAULT 200 CHECK (size >= 100 AND size <= 1000),
    format VARCHAR(10) DEFAULT 'png' CHECK (format IN ('png', 'svg', 'base64')),
    include_logo BOOLEAN DEFAULT FALSE,
    custom_data JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    scan_count INTEGER DEFAULT 0 CHECK (scan_count >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- QR Scans table - tracks QR code scan events for analytics
CREATE TABLE IF NOT EXISTS qr_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qr_id TEXT NOT NULL REFERENCES qr_codes(id) ON DELETE CASCADE,
    qr_type VARCHAR(50) NOT NULL CHECK (qr_type IN ('menu_item', 'table', 'order', 'menu_category', 'business')),
    target_id UUID NOT NULL,
    business_id UUID NOT NULL,
    scanner_location TEXT,
    scanner_id TEXT,
    user_agent TEXT,
    ip_address INET,
    scanned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tables table - manages restaurant tables with QR codes
CREATE TABLE IF NOT EXISTS tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_number VARCHAR(50) NOT NULL,
    business_id UUID NOT NULL,
    location_id UUID,
    capacity INTEGER CHECK (capacity >= 1 AND capacity <= 20),
    qr_code_id TEXT REFERENCES qr_codes(id),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(business_id, table_number)
);

-- Business Locations table - stores business location information
CREATE TABLE IF NOT EXISTS business_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'USA',
    phone VARCHAR(20),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_qr_codes_business_id ON qr_codes(business_id);
CREATE INDEX IF NOT EXISTS idx_qr_codes_type ON qr_codes(type);
CREATE INDEX IF NOT EXISTS idx_qr_codes_target_id ON qr_codes(target_id);
CREATE INDEX IF NOT EXISTS idx_qr_codes_active ON qr_codes(is_active);

CREATE INDEX IF NOT EXISTS idx_qr_scans_qr_id ON qr_scans(qr_id);
CREATE INDEX IF NOT EXISTS idx_qr_scans_business_id ON qr_scans(business_id);
CREATE INDEX IF NOT EXISTS idx_qr_scans_scanned_at ON qr_scans(scanned_at);
CREATE INDEX IF NOT EXISTS idx_qr_scans_qr_type ON qr_scans(qr_type);

CREATE INDEX IF NOT EXISTS idx_tables_business_id ON tables(business_id);
CREATE INDEX IF NOT EXISTS idx_tables_active ON tables(is_active);

CREATE INDEX IF NOT EXISTS idx_business_locations_business_id ON business_locations(business_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_qr_codes_updated_at BEFORE UPDATE ON qr_codes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tables_updated_at BEFORE UPDATE ON tables FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_business_locations_updated_at BEFORE UPDATE ON business_locations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to increment scan count
CREATE OR REPLACE FUNCTION increment_qr_scan_count(qr_code_id TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE qr_codes 
    SET scan_count = scan_count + 1, updated_at = NOW()
    WHERE id = qr_code_id;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-increment scan count when a scan is logged
CREATE OR REPLACE FUNCTION trigger_increment_scan_count()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM increment_qr_scan_count(NEW.qr_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER increment_scan_count_trigger
    AFTER INSERT ON qr_scans
    FOR EACH ROW
    EXECUTE FUNCTION trigger_increment_scan_count();
