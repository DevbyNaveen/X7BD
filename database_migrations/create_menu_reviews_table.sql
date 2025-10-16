-- Create menu item reviews table for customer ratings
CREATE TABLE IF NOT EXISTS menu_item_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    menu_item_id UUID NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    customer_id UUID, -- Optional - can be null for anonymous reviews
    order_id UUID REFERENCES orders(id), -- Optional - link to specific order
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    is_verified BOOLEAN DEFAULT FALSE, -- Verified purchase
    is_public BOOLEAN DEFAULT TRUE, -- Can be hidden by business
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_menu_item_reviews_business_id ON menu_item_reviews(business_id);
CREATE INDEX IF NOT EXISTS idx_menu_item_reviews_menu_item_id ON menu_item_reviews(menu_item_id);
CREATE INDEX IF NOT EXISTS idx_menu_item_reviews_rating ON menu_item_reviews(rating);
CREATE INDEX IF NOT EXISTS idx_menu_item_reviews_created_at ON menu_item_reviews(created_at);

-- Create unique constraint to prevent duplicate reviews from same customer for same item
CREATE UNIQUE INDEX IF NOT EXISTS idx_menu_item_reviews_unique_customer_item 
ON menu_item_reviews(customer_id, menu_item_id) 
WHERE customer_id IS NOT NULL;

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_menu_item_reviews_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_menu_item_reviews_updated_at
    BEFORE UPDATE ON menu_item_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_menu_item_reviews_updated_at();

-- Insert some sample reviews for testing (optional)
INSERT INTO menu_item_reviews (business_id, menu_item_id, rating, review_text, is_verified)
SELECT 
    mi.business_id,
    mi.id,
    (random() * 4 + 1)::INTEGER, -- Random rating between 1-5
    CASE 
        WHEN (random() * 4 + 1)::INTEGER >= 4 THEN 'Great item! Highly recommended.'
        WHEN (random() * 4 + 1)::INTEGER >= 3 THEN 'Good quality, would order again.'
        WHEN (random() * 4 + 1)::INTEGER >= 2 THEN 'Average quality, could be better.'
        ELSE 'Not satisfied with this item.'
    END,
    true
FROM menu_items mi
WHERE mi.is_available = true
LIMIT 50; -- Insert up to 50 sample reviews
