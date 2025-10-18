-- Purchase Orders Table Creation
-- Creates the purchase_orders table for inventory management

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Purchase Orders table - manages purchase orders and supplier relationships
CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL,
    supplier_id UUID NOT NULL,
    order_number VARCHAR(100) NOT NULL UNIQUE,
    order_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expected_delivery_date TIMESTAMP WITH TIME ZONE,
    actual_delivery_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'ordered', 'shipped', 'delivered', 'cancelled')),
    items JSONB NOT NULL DEFAULT '[]',
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    notes TEXT,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Suppliers table - manages supplier information
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'USA',
    payment_terms VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(business_id, name)
);

-- Inventory Items table - manages inventory items
CREATE TABLE IF NOT EXISTS inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sku VARCHAR(100),
    category VARCHAR(100),
    unit_of_measure VARCHAR(50) DEFAULT 'each',
    current_stock DECIMAL(10,2) DEFAULT 0.00,
    min_stock_level DECIMAL(10,2) DEFAULT 0.00,
    max_stock_level DECIMAL(10,2),
    cost_per_unit DECIMAL(10,2) DEFAULT 0.00,
    selling_price DECIMAL(10,2),
    supplier_id UUID REFERENCES suppliers(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(business_id, sku)
);

-- Inventory Transactions table - tracks stock movements
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL,
    inventory_item_id UUID NOT NULL REFERENCES inventory_items(id),
    transaction_type VARCHAR(50) NOT NULL CHECK (transaction_type IN ('purchase', 'sale', 'adjustment', 'waste', 'transfer')),
    quantity DECIMAL(10,2) NOT NULL,
    unit_cost DECIMAL(10,2),
    total_cost DECIMAL(10,2),
    reference_id UUID, -- Links to purchase orders, sales, etc.
    reference_type VARCHAR(50), -- 'purchase_order', 'sale', 'adjustment', etc.
    notes TEXT,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Stock Alerts table - manages low stock alerts
CREATE TABLE IF NOT EXISTS stock_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL,
    inventory_item_id UUID NOT NULL REFERENCES inventory_items(id),
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('low_stock', 'out_of_stock', 'overstock')),
    current_stock DECIMAL(10,2) NOT NULL,
    threshold_level DECIMAL(10,2) NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_purchase_orders_business_id ON purchase_orders(business_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier_id ON purchase_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_order_date ON purchase_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_order_number ON purchase_orders(order_number);

CREATE INDEX IF NOT EXISTS idx_suppliers_business_id ON suppliers(business_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_active ON suppliers(is_active);

CREATE INDEX IF NOT EXISTS idx_inventory_items_business_id ON inventory_items(business_id);
CREATE INDEX IF NOT EXISTS idx_inventory_items_supplier_id ON inventory_items(supplier_id);
CREATE INDEX IF NOT EXISTS idx_inventory_items_active ON inventory_items(is_active);
CREATE INDEX IF NOT EXISTS idx_inventory_items_sku ON inventory_items(sku);

CREATE INDEX IF NOT EXISTS idx_inventory_transactions_business_id ON inventory_transactions(business_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_item_id ON inventory_transactions(inventory_item_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_type ON inventory_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_created_at ON inventory_transactions(created_at);

CREATE INDEX IF NOT EXISTS idx_stock_alerts_business_id ON stock_alerts(business_id);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_item_id ON stock_alerts(inventory_item_id);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_resolved ON stock_alerts(is_resolved);

-- Create updated_at trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_purchase_orders_updated_at BEFORE UPDATE ON purchase_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_inventory_items_updated_at BEFORE UPDATE ON inventory_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to update stock levels when transactions occur
CREATE OR REPLACE FUNCTION update_inventory_stock()
RETURNS TRIGGER AS $$
BEGIN
    -- Update current stock based on transaction type
    IF NEW.transaction_type = 'purchase' OR NEW.transaction_type = 'adjustment' THEN
        -- Add to stock
        UPDATE inventory_items 
        SET current_stock = current_stock + NEW.quantity,
            updated_at = NOW()
        WHERE id = NEW.inventory_item_id;
    ELSIF NEW.transaction_type = 'sale' OR NEW.transaction_type = 'waste' THEN
        -- Subtract from stock
        UPDATE inventory_items 
        SET current_stock = current_stock - NEW.quantity,
            updated_at = NOW()
        WHERE id = NEW.inventory_item_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update stock levels
CREATE TRIGGER update_stock_on_transaction
    AFTER INSERT ON inventory_transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_inventory_stock();

-- Create function to check for low stock alerts
CREATE OR REPLACE FUNCTION check_low_stock()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if stock is below minimum level
    IF NEW.current_stock <= NEW.min_stock_level THEN
        -- Create low stock alert if not already exists
        INSERT INTO stock_alerts (business_id, inventory_item_id, alert_type, current_stock, threshold_level)
        SELECT NEW.business_id, NEW.id, 'low_stock', NEW.current_stock, NEW.min_stock_level
        WHERE NOT EXISTS (
            SELECT 1 FROM stock_alerts 
            WHERE inventory_item_id = NEW.id 
            AND alert_type = 'low_stock' 
            AND is_resolved = FALSE
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to check for low stock
CREATE TRIGGER check_low_stock_trigger
    AFTER UPDATE ON inventory_items
    FOR EACH ROW
    EXECUTE FUNCTION check_low_stock();
