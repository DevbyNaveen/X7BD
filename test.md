# Analytics API Test Results

**Business ID:** fd8a3d59-4a06-43c2-9820-0e3222867117
**Test Date:** 2025-10-18 12:07:54
**Server:** http://localhost:8060

## /api/v1/analytics/menu/overview/fd8a3d59-4a06-43c2-9820-0e3222867117

**Status:** ✅ SUCCESS
**Status Code:** 200

**Response Data:**
```json
{
  "business_id": "fd8a3d59-4a06-43c2-9820-0e3222867117",
  "period": "7d",
  "total_menu_items": 16,
  "popular_items": 0,
  "average_rating": 4.2,
  "total_categories": 11,
  "items_growth": 15.2,
  "rating_growth": 2.1,
  "categories_growth": 8.7,
  "popularity_growth": 12.3,
  "performance_score": 33.3,
  "last_updated": "2025-10-18T06:37:17.055654",
  "trends_included": true
}
```

## /api/v1/analytics/menu/top-items/fd8a3d59-4a06-43c2-9820-0e3222867117

**Status:** ❌ FAILED
**Status Code:** ERROR

**Error:** HTTPConnectionPool(host='localhost', port=8060): Read timed out. (read timeout=10)

## /api/v1/analytics/menu/category-performance/fd8a3d59-4a06-43c2-9820-0e3222867117

**Status:** ❌ FAILED
**Status Code:** ERROR

**Error:** HTTPConnectionPool(host='localhost', port=8060): Read timed out. (read timeout=10)

## /api/v1/analytics/menu/profit-margins/fd8a3d59-4a06-43c2-9820-0e3222867117

**Status:** ✅ SUCCESS
**Status Code:** 200

**Response Data:**
```json
{
  "business_id": "fd8a3d59-4a06-43c2-9820-0e3222867117",
  "total_items": 16,
  "items_with_cost": 10,
  "items_without_cost": 6,
  "overall_analysis": {
    "total_revenue": 209.9,
    "total_cost": 68.5,
    "overall_profit_margin": 141.4,
    "overall_margin_percentage": 67.4
  },
  "high_margin_items": [],
  "low_margin_items": [],
  "medium_margin_items": [
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440030",
      "name": "Buffalo Wings",
      "price": 12.99,
      "cost": 6.5,
      "profit_margin": 6.49,
      "margin_percentage": 50.0,
      "category_id": "550e8400-e29b-41d4-a716-446655440020",
      "is_available": true
    },
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440031",
      "name": "Mozzarella Sticks",
      "price": 8.99,
      "cost": 4.0,
      "profit_margin": 4.99,
      "margin_percentage": 55.5,
      "category_id": "550e8400-e29b-41d4-a716-446655440020",
      "is_available": true
    },
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440032",
      "name": "Grilled Salmon",
      "price": 24.99,
      "cost": 12.0,
      "profit_margin": 12.989999999999998,
      "margin_percentage": 52.0,
      "category_id": "550e8400-e29b-41d4-a716-446655440021",
      "is_available": true
    },
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440033",
      "name": "Ribeye Steak",
      "price": 32.99,
      "cost": 18.0,
      "profit_margin": 14.990000000000002,
      "margin_percentage": 45.4,
      "category_id": "550e8400-e29b-41d4-a716-446655440021",
      "is_available": true
    },
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440034",
      "name": "Chocolate Cake",
      "price": 7.99,
      "cost": 3.5,
      "profit_margin": 4.49,
      "margin_percentage": 56.2,
      "category_id": "550e8400-e29b-41d4-a716-446655440022",
      "is_available": true
    },
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440035",
      "name": "Craft Beer",
      "price": 6.99,
      "cost": 2.5,
      "profit_margin": 4.49,
      "margin_percentage": 64.2,
      "category_id": "550e8400-e29b-41d4-a716-446655440023",
      "is_available": true
    },
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440036",
      "name": "Caesar Salad",
      "price": 11.99,
      "cost": 5.0,
      "profit_margin": 6.99,
      "margin_percentage": 58.3,
      "category_id": "550e8400-e29b-41d4-a716-446655440024",
      "is_available": true
    },
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440037",
      "name": "Tomato Soup",
      "price": 6.99,
      "cost": 2.5,
      "profit_margin": 4.49,
      "margin_percentage": 64.2,
      "category_id": "550e8400-e29b-41d4-a716-446655440025",
      "is_available": true
    },
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440038",
      "name": "Club Sandwich",
      "price": 13.99,
      "cost": 6.5,
      "profit_margin": 7.49,
      "margin_percentage": 53.5,
      "category_id": "550e8400-e29b-41d4-a716-446655440026",
      "is_available": true
    },
    {
      "item_id": "550e8400-e29b-41d4-a716-446655440039",
      "name": "Spaghetti Carbonara",
      "price": 16.99,
      "cost": 8.0,
      "profit_margin": 8.989999999999998,
      "margin_percentage": 52.9,
      "category_id": "550e8400-e29b-41d4-a716-446655440027",
      "is_available": true
    }
  ],
  "margin_distribution": [
    {
      "range": "High (>70.0%)",
      "count": 0,
      "percentage": 0.0
    },
    {
      "range": "Medium (30.0-70.0%)",
      "count": 10,
      "percentage": 62.5
    },
    {
      "range": "Low (<30.0%)",
      "count": 0,
      "percentage": 0.0
    },
    {
      "range": "No Cost Data",
      "count": 6,
      "percentage": 37.5
    }
  ],
  "recommendations": [
    {
      "type": "cost_tracking",
      "priority": "medium",
      "title": "Add Cost Information",
      "message": "6 items don't have cost data. Adding cost information will improve profit analysis.",
      "affected_items": [
        "Black",
        "Choclate Juice (Copy)",
        "whuyecjgvj",
        "Strawberry (Copy)",
        "Choclate Juice"
      ],
      "action": "Add cost data to improve margin analysis"
    }
  ],
  "analysis_date": "2025-10-18T06:37:46.814020"
}
```

## /api/v1/analytics/menu/dashboard/fd8a3d59-4a06-43c2-9820-0e3222867117

**Status:** ✅ SUCCESS
**Status Code:** 200

**Response Data:**
```json
{
  "business_id": "fd8a3d59-4a06-43c2-9820-0e3222867117",
  "period": "7d",
  "overview": {
    "business_id": "fd8a3d59-4a06-43c2-9820-0e3222867117",
    "period": "7d",
    "total_menu_items": 16,
    "popular_items": 0,
    "average_rating": 4.2,
    "total_categories": 11,
    "items_growth": 15.2,
    "rating_growth": 2.1,
    "categories_growth": 8.7,
    "popularity_growth": 12.3,
    "performance_score": 33.3,
    "last_updated": "2025-10-18T06:37:51.863887",
    "trends_included": true
  },
  "top_items": {
    "business_id": "fd8a3d59-4a06-43c2-9820-0e3222867117",
    "period": "7d",
    "sort_by": "revenue",
    "total_items": 10,
    "items": [
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440033",
        "name": "Ribeye Steak",
        "category_name": "Main Courses",
        "price": 32.99,
        "cost": 18.0,
        "sales_count": 35,
        "total_quantity": 35,
        "total_revenue": 1154.65,
        "total_cost": 630.0,
        "profit_margin": 524.6500000000001,
        "margin_percentage": 45.4,
        "image_url": "https://example.com/ribeye.jpg",
        "is_available": true,
        "tags": [
          "premium",
          "beef"
        ]
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440032",
        "name": "Grilled Salmon",
        "category_name": "Main Courses",
        "price": 24.99,
        "cost": 12.0,
        "sales_count": 31,
        "total_quantity": 31,
        "total_revenue": 774.6899999999999,
        "total_cost": 372.0,
        "profit_margin": 402.68999999999994,
        "margin_percentage": 52.0,
        "image_url": "https://example.com/salmon.jpg",
        "is_available": true,
        "tags": [
          "healthy",
          "premium"
        ]
      },
      {
        "item_id": "316c1264-1c99-442a-b59a-49a55ea8845f",
        "name": "Strawberry Bro",
        "category_name": "juice",
        "price": 15.0,
        "cost": 4.5,
        "sales_count": 31,
        "total_quantity": 31,
        "total_revenue": 465.0,
        "total_cost": 139.5,
        "profit_margin": 325.5,
        "margin_percentage": 70.0,
        "image_url": null,
        "is_available": true,
        "tags": []
      },
      {
        "item_id": "8c1fcd79-1c2e-4ba3-9efe-8e75e5e7fc91",
        "name": "Strawberry (Copy)",
        "category_name": "juice",
        "price": 10.0,
        "cost": 3.0,
        "sales_count": 32,
        "total_quantity": 32,
        "total_revenue": 320.0,
        "total_cost": 96.0,
        "profit_margin": 224.0,
        "margin_percentage": 70.0,
        "image_url": null,
        "is_available": true,
        "tags": []
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440031",
        "name": "Mozzarella Sticks",
        "category_name": "Appetizers",
        "price": 8.99,
        "cost": 4.0,
        "sales_count": 35,
        "total_quantity": 35,
        "total_revenue": 314.65000000000003,
        "total_cost": 140.0,
        "profit_margin": 174.65000000000003,
        "margin_percentage": 55.5,
        "image_url": "https://example.com/mozzarella.jpg",
        "is_available": true,
        "tags": [
          "cheesy",
          "crispy"
        ]
      },
      {
        "item_id": "c475e801-1fb8-4ac4-946d-6679e1393c4e",
        "name": "whuyecjgvj",
        "category_name": "juice",
        "price": 10.0,
        "cost": 3.0,
        "sales_count": 26,
        "total_quantity": 26,
        "total_revenue": 260.0,
        "total_cost": 78.0,
        "profit_margin": 182.0,
        "margin_percentage": 70.0,
        "image_url": null,
        "is_available": false,
        "tags": []
      },
      {
        "item_id": "db8c9331-71dd-4d55-a45d-801c7fc02ba5",
        "name": "Choclate Juice",
        "category_name": "Uncategorized",
        "price": 10.0,
        "cost": 3.0,
        "sales_count": 26,
        "total_quantity": 26,
        "total_revenue": 260.0,
        "total_cost": 78.0,
        "profit_margin": 182.0,
        "margin_percentage": 70.0,
        "image_url": "",
        "is_available": false,
        "tags": []
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440030",
        "name": "Buffalo Wings",
        "category_name": "Appetizers",
        "price": 12.99,
        "cost": 6.5,
        "sales_count": 17,
        "total_quantity": 17,
        "total_revenue": 220.83,
        "total_cost": 110.5,
        "profit_margin": 110.33000000000001,
        "margin_percentage": 50.0,
        "image_url": "https://example.com/wings.jpg",
        "is_available": true,
        "tags": [
          "spicy",
          "popular"
        ]
      },
      {
        "item_id": "eaa6d31a-1f79-42b5-b61f-dd17661faa97",
        "name": "Choclate Juice (Copy)",
        "category_name": "Uncategorized",
        "price": 10.0,
        "cost": 3.0,
        "sales_count": 9,
        "total_quantity": 9,
        "total_revenue": 90.0,
        "total_cost": 27.0,
        "profit_margin": 63.0,
        "margin_percentage": 70.0,
        "image_url": "",
        "is_available": false,
        "tags": []
      },
      {
        "item_id": "9a88fc2c-95d0-476d-8c63-99aa1c6d1565",
        "name": "Black",
        "category_name": "juice",
        "price": 10.0,
        "cost": 3.0,
        "sales_count": 5,
        "total_quantity": 5,
        "total_revenue": 50.0,
        "total_cost": 15.0,
        "profit_margin": 35.0,
        "margin_percentage": 70.0,
        "image_url": null,
        "is_available": false,
        "tags": []
      }
    ],
    "generated_at": "2025-10-18T06:37:52.902782"
  },
  "category_performance": {
    "business_id": "fd8a3d59-4a06-43c2-9820-0e3222867117",
    "period": "7d",
    "total_categories": 11,
    "categories": [
      {
        "category_id": "550e8400-e29b-41d4-a716-446655440023",
        "category_name": "Beverages",
        "total_items": 1,
        "available_items": 1,
        "avg_price": 6.99,
        "avg_cost": 2.5,
        "avg_profit_margin": 4.49,
        "profit_margin_percentage": 64.2,
        "total_sales": 0,
        "total_revenue": 0.0,
        "total_profit": 0.0,
        "performance_score": 59.3,
        "growth_percentage": 14.0,
        "description": "Refreshing drinks and specialty beverages",
        "is_active": true
      },
      {
        "category_id": "550e8400-e29b-41d4-a716-446655440025",
        "category_name": "Soups",
        "total_items": 1,
        "available_items": 1,
        "avg_price": 6.99,
        "avg_cost": 2.5,
        "avg_profit_margin": 4.49,
        "profit_margin_percentage": 64.2,
        "total_sales": 0,
        "total_revenue": 0.0,
        "total_profit": 0.0,
        "performance_score": 59.3,
        "growth_percentage": 7.0,
        "description": "Warm and comforting soup selections",
        "is_active": true
      },
      {
        "category_id": "550e8400-e29b-41d4-a716-446655440024",
        "category_name": "Salads",
        "total_items": 1,
        "available_items": 1,
        "avg_price": 11.99,
        "avg_cost": 5.0,
        "avg_profit_margin": 6.99,
        "profit_margin_percentage": 58.3,
        "total_sales": 0,
        "total_revenue": 0.0,
        "total_profit": 0.0,
        "performance_score": 57.5,
        "growth_percentage": 1.0,
        "description": "Fresh and healthy salad options",
        "is_active": true
      },
      {
        "category_id": "550e8400-e29b-41d4-a716-446655440022",
        "category_name": "Desserts",
        "total_items": 1,
        "available_items": 1,
        "avg_price": 7.99,
        "avg_cost": 3.5,
        "avg_profit_margin": 4.49,
        "profit_margin_percentage": 56.2,
        "total_sales": 0,
        "total_revenue": 0.0,
        "total_profit": 0.0,
        "performance_score": 56.9,
        "growth_percentage": 14.0,
        "description": "Sweet endings to perfect your meal",
        "is_active": true
      },
      {
        "category_id": "550e8400-e29b-41d4-a716-446655440026",
        "category_name": "Sandwiches",
        "total_items": 1,
        "available_items": 1,
        "avg_price": 13.99,
        "avg_cost": 6.5,
        "avg_profit_margin": 7.49,
        "profit_margin_percentage": 53.5,
        "total_sales": 0,
        "total_revenue": 0.0,
        "total_profit": 0.0,
        "performance_score": 56.1,
        "growth_percentage": 12.0,
        "description": "Delicious sandwiches and wraps",
        "is_active": true
      },
      {
        "category_id": "550e8400-e29b-41d4-a716-446655440027",
        "category_name": "Pasta",
        "total_items": 1,
        "available_items": 1,
        "avg_price": 16.99,
        "avg_cost": 8.0,
        "avg_profit_margin": 8.99,
        "profit_margin_percentage": 52.9,
        "total_sales": 0,
        "total_revenue": 0.0,
        "total_profit": 0.0,
        "performance_score": 55.9,
        "growth_percentage": 5.0,
        "description": "Authentic Italian pasta dishes",
        "is_active": true
      },
      {
        "category_id": "550e8400-e29b-41d4-a716-446655440020",
        "category_name": "Appetizers",
        "total_items": 2,
        "available_items": 2,
        "avg_price": 10.99,
        "avg_cost": 5.25,
        "avg_profit_margin": 5.74,
        "profit_margin_percentage": 52.2,
        "total_sales": 0,
        "total_revenue": 0.0,
        "total_profit": 0.0,
        "performance_score": 55.7,
        "growth_percentage": 0.0,
        "description": "Start your meal with our delicious appetizers",
        "is_active": true
      },
      {
        "category_id": "550e8400-e29b-41d4-a716-446655440021",
        "category_name": "Main Courses",
        "total_items": 2,
        "available_items": 2,
        "avg_price": 28.99,
        "avg_cost": 15.0,
        "avg_profit_margin": 13.99,
        "profit_margin_percentage": 48.3,
        "total_sales": 0,
        "total_revenue": 0.0,
        "total_profit": 0.0,
        "performance_score": 54.5,
        "growth_percentage": 8.0,
        "description": "Hearty main dishes for every appetite",
        "is_active": true
      },
      {
        "category_id": "c1dd076d-fec7-4a02-9cb2-8739aa79ca0f",
        "category_name": "juice",
        "total_items": 4,
        "available_items": 2,
        "avg_price": 11.25,
        "avg_cost": 0.0,
        "avg_profit_margin": 11.25,
        "profit_margin_percentage": 100.0,
        "total_sales": 0,
        "total_revenue": 0.0,
        "total_profit": 0.0,
        "performance_score": 50.0,
        "growth_percentage": 6.0,
        "description": null,
        "is_active": true
      },
      {
        "category_id": "550e8400-e29b-41d4-a716-446655440028",
        "category_name": "Seafood",
        "total_items": 0,
        "available_items": 0,
        "avg_price": 0.0,
        "avg_cost": 0.0,
        "avg_profit_margin": 0.0,
        "profit_margin_percentage": 0.0,
        "total_sales": 0,
        "total_revenue": 0.0,
        "total_profit": 0.0,
        "performance_score": 0.0,
        "growth_percentage": 0.0,
        "description": "Fresh seafood and fish dishes",
        "is_active": true
      },
      {
        "category_id": "550e8400-e29b-41d4-a716-446655440029",
        "category_name": "Vegetarian",
        "total_items": 0,
        "available_items": 0,
        "avg_price": 0.0,
        "avg_cost": 0.0,
        "avg_profit_margin": 0.0,
        "profit_margin_percentage": 0.0,
        "total_sales": 0,
        "total_revenue": 0.0,
        "total_profit": 0.0,
        "performance_score": 0.0,
        "growth_percentage": 12.0,
        "description": "Plant-based and vegetarian options",
        "is_active": true
      }
    ],
    "include_details": true,
    "generated_at": "2025-10-18T06:37:53.920239"
  },
  "profit_margins": {
    "business_id": "fd8a3d59-4a06-43c2-9820-0e3222867117",
    "total_items": 16,
    "items_with_cost": 10,
    "items_without_cost": 6,
    "overall_analysis": {
      "total_revenue": 209.9,
      "total_cost": 68.5,
      "overall_profit_margin": 141.4,
      "overall_margin_percentage": 67.4
    },
    "high_margin_items": [],
    "low_margin_items": [],
    "medium_margin_items": [
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440030",
        "name": "Buffalo Wings",
        "price": 12.99,
        "cost": 6.5,
        "profit_margin": 6.49,
        "margin_percentage": 50.0,
        "category_id": "550e8400-e29b-41d4-a716-446655440020",
        "is_available": true
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440031",
        "name": "Mozzarella Sticks",
        "price": 8.99,
        "cost": 4.0,
        "profit_margin": 4.99,
        "margin_percentage": 55.5,
        "category_id": "550e8400-e29b-41d4-a716-446655440020",
        "is_available": true
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440032",
        "name": "Grilled Salmon",
        "price": 24.99,
        "cost": 12.0,
        "profit_margin": 12.989999999999998,
        "margin_percentage": 52.0,
        "category_id": "550e8400-e29b-41d4-a716-446655440021",
        "is_available": true
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440033",
        "name": "Ribeye Steak",
        "price": 32.99,
        "cost": 18.0,
        "profit_margin": 14.990000000000002,
        "margin_percentage": 45.4,
        "category_id": "550e8400-e29b-41d4-a716-446655440021",
        "is_available": true
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440034",
        "name": "Chocolate Cake",
        "price": 7.99,
        "cost": 3.5,
        "profit_margin": 4.49,
        "margin_percentage": 56.2,
        "category_id": "550e8400-e29b-41d4-a716-446655440022",
        "is_available": true
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440035",
        "name": "Craft Beer",
        "price": 6.99,
        "cost": 2.5,
        "profit_margin": 4.49,
        "margin_percentage": 64.2,
        "category_id": "550e8400-e29b-41d4-a716-446655440023",
        "is_available": true
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440036",
        "name": "Caesar Salad",
        "price": 11.99,
        "cost": 5.0,
        "profit_margin": 6.99,
        "margin_percentage": 58.3,
        "category_id": "550e8400-e29b-41d4-a716-446655440024",
        "is_available": true
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440037",
        "name": "Tomato Soup",
        "price": 6.99,
        "cost": 2.5,
        "profit_margin": 4.49,
        "margin_percentage": 64.2,
        "category_id": "550e8400-e29b-41d4-a716-446655440025",
        "is_available": true
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440038",
        "name": "Club Sandwich",
        "price": 13.99,
        "cost": 6.5,
        "profit_margin": 7.49,
        "margin_percentage": 53.5,
        "category_id": "550e8400-e29b-41d4-a716-446655440026",
        "is_available": true
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440039",
        "name": "Spaghetti Carbonara",
        "price": 16.99,
        "cost": 8.0,
        "profit_margin": 8.989999999999998,
        "margin_percentage": 52.9,
        "category_id": "550e8400-e29b-41d4-a716-446655440027",
        "is_available": true
      }
    ],
    "margin_distribution": [
      {
        "range": "High (>70.0%)",
        "count": 0,
        "percentage": 0.0
      },
      {
        "range": "Medium (30.0-70.0%)",
        "count": 10,
        "percentage": 62.5
      },
      {
        "range": "Low (<30.0%)",
        "count": 0,
        "percentage": 0.0
      },
      {
        "range": "No Cost Data",
        "count": 6,
        "percentage": 37.5
      }
    ],
    "recommendations": [
      {
        "type": "cost_tracking",
        "priority": "medium",
        "title": "Add Cost Information",
        "message": "6 items don't have cost data. Adding cost information will improve profit analysis.",
        "affected_items": [
          "Black",
          "Choclate Juice (Copy)",
          "whuyecjgvj",
          "Strawberry (Copy)",
          "Choclate Juice"
        ],
        "action": "Add cost data to improve margin analysis"
      }
    ],
    "analysis_date": "2025-10-18T06:37:54.271087"
  },
  "generated_at": "2025-10-18T06:37:54.271087",
  "cache_expires_at": "2025-10-18T06:42:54.271087"
}
```

