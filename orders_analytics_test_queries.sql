-- Orders Analytics Test Queries for Supabase
-- Business ID: fd8a3d59-4a06-43c2-9820-0e3222867117

-- ============================================================================
-- 1. BASIC ORDERS OVERVIEW QUERY
-- ============================================================================
-- This query shows the basic metrics that the orders overview endpoint calculates

SELECT 
    COUNT(*) as total_orders,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
    COUNT(CASE WHEN status IN ('pending', 'active', 'preparing') THEN 1 END) as pending_orders,
    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_orders,
    SUM(COALESCE(total_amount, 0)) as total_revenue,
    AVG(COALESCE(total_amount, 0)) as average_order_value,
    ROUND(
        (COUNT(CASE WHEN status = 'completed' THEN 1 END)::float / COUNT(*) * 100), 1
    ) as completion_rate,
    ROUND(
        (COUNT(CASE WHEN status = 'cancelled' THEN 1 END)::float / COUNT(*) * 100), 1
    ) as cancellation_rate
FROM orders 
WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
    AND created_at >= NOW() - INTERVAL '7 days';

-- ============================================================================
-- 2. ORDERS TREND BY DAY QUERY
-- ============================================================================
-- This query shows daily order volume and revenue for the last 7 days

SELECT 
    DATE(created_at) as order_date,
    TO_CHAR(created_at, 'Dy') as day_name,
    COUNT(*) as orders_count,
    SUM(COALESCE(total_amount, 0)) as daily_revenue
FROM orders 
WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
    AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at), TO_CHAR(created_at, 'Dy')
ORDER BY order_date;

-- ============================================================================
-- 3. ORDERS BY HOUR QUERY
-- ============================================================================
-- This query shows hourly distribution of orders

SELECT 
    EXTRACT(HOUR FROM created_at) as hour,
    COUNT(*) as orders_count
FROM orders 
WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
    AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY EXTRACT(HOUR FROM created_at)
ORDER BY hour;

-- ============================================================================
-- 4. ORDER STATUS DISTRIBUTION QUERY
-- ============================================================================
-- This query shows the breakdown of orders by status

SELECT 
    CASE 
        WHEN status = 'completed' THEN 'Completed'
        WHEN status IN ('pending', 'active', 'preparing') THEN 'Pending'
        WHEN status = 'cancelled' THEN 'Cancelled'
        ELSE status
    END as status_display,
    COUNT(*) as count,
    ROUND(COUNT(*)::float / (SELECT COUNT(*) FROM orders WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117' AND created_at >= NOW() - INTERVAL '7 days') * 100, 1) as percentage
FROM orders 
WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
    AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY 
    CASE 
        WHEN status = 'completed' THEN 'Completed'
        WHEN status IN ('pending', 'active', 'preparing') THEN 'Pending'
        WHEN status = 'cancelled' THEN 'Cancelled'
        ELSE status
    END
ORDER BY count DESC;

-- ============================================================================
-- 5. ORDER TYPES DISTRIBUTION QUERY
-- ============================================================================
-- This query shows dine-in vs takeout vs delivery distribution

SELECT 
    CASE 
        WHEN table_id IS NOT NULL THEN 'Dine-in'
        WHEN delivery_address IS NOT NULL OR order_type = 'delivery' THEN 'Delivery'
        ELSE 'Takeout'
    END as order_type,
    COUNT(*) as count,
    ROUND(COUNT(*)::float / (SELECT COUNT(*) FROM orders WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117' AND created_at >= NOW() - INTERVAL '7 days') * 100, 1) as percentage
FROM orders 
WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
    AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY 
    CASE 
        WHEN table_id IS NOT NULL THEN 'Dine-in'
        WHEN delivery_address IS NOT NULL OR order_type = 'delivery' THEN 'Delivery'
        ELSE 'Takeout'
    END
ORDER BY count DESC;

-- ============================================================================
-- 6. TOP SELLING ITEMS QUERY
-- ============================================================================
-- This query shows the most popular menu items by quantity sold

WITH order_items AS (
    SELECT 
        jsonb_array_elements(items) as item_data
    FROM orders 
    WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
        AND created_at >= NOW() - INTERVAL '7 days'
),
item_sales AS (
    SELECT 
        COALESCE(item_data->>'menu_item_id', item_data->>'id') as item_id,
        COALESCE((item_data->>'quantity')::int, 0) as quantity,
        COALESCE((item_data->>'price')::numeric, 0) as price
    FROM order_items
    WHERE item_data->>'menu_item_id' IS NOT NULL OR item_data->>'id' IS NOT NULL
),
item_totals AS (
    SELECT 
        item_id,
        SUM(quantity) as total_quantity,
        SUM(quantity * price) as total_revenue
    FROM item_sales
    GROUP BY item_id
)
SELECT 
    mi.name as item_name,
    it.total_quantity,
    it.total_revenue
FROM item_totals it
LEFT JOIN menu_items mi ON mi.id::text = it.item_id
WHERE mi.business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
ORDER BY it.total_quantity DESC
LIMIT 10;

-- ============================================================================
-- 7. GROWTH COMPARISON QUERY
-- ============================================================================
-- This query compares current period vs previous period for growth calculations

WITH current_period AS (
    SELECT 
        COUNT(*) as orders_count,
        SUM(COALESCE(total_amount, 0)) as revenue
    FROM orders 
    WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
        AND created_at >= NOW() - INTERVAL '7 days'
),
previous_period AS (
    SELECT 
        COUNT(*) as orders_count,
        SUM(COALESCE(total_amount, 0)) as revenue
    FROM orders 
    WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
        AND created_at >= NOW() - INTERVAL '14 days'
        AND created_at < NOW() - INTERVAL '7 days'
)
SELECT 
    cp.orders_count as current_orders,
    pp.orders_count as previous_orders,
    cp.revenue as current_revenue,
    pp.revenue as previous_revenue,
    CASE 
        WHEN pp.orders_count > 0 THEN 
            ROUND(((cp.orders_count - pp.orders_count)::float / pp.orders_count * 100), 1)
        ELSE 100.0
    END as orders_growth_percentage,
    CASE 
        WHEN pp.revenue > 0 THEN 
            ROUND(((cp.revenue - pp.revenue)::float / pp.revenue * 100), 1)
        ELSE 100.0
    END as revenue_growth_percentage
FROM current_period cp, previous_period pp;

-- ============================================================================
-- 8. SAMPLE ORDERS DATA QUERY
-- ============================================================================
-- This query shows sample order data to verify the structure

SELECT 
    id,
    business_id,
    status,
    total_amount,
    created_at,
    table_id,
    delivery_address,
    order_type,
    items
FROM orders 
WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
    AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 5;

-- ============================================================================
-- 9. DATETIME FORMAT TEST QUERY
-- ============================================================================
-- This query shows the datetime formats in your orders table

SELECT 
    id,
    created_at,
    EXTRACT(MICROSECOND FROM created_at) as microseconds,
    LENGTH(SPLIT_PART(created_at::text, '.', 2)) as microsecond_digits
FROM orders 
WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
    AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 10;

-- ============================================================================
-- 10. MENU ITEMS REFERENCE QUERY
-- ============================================================================
-- This query shows available menu items for the business

SELECT 
    id,
    name,
    price,
    cost,
    is_available,
    category_id
FROM menu_items 
WHERE business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
ORDER BY name
LIMIT 10;
