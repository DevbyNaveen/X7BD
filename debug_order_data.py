#!/usr/bin/env python3
"""
Debug Order Data Structure
Check what data is actually in orders and order_items tables
"""

import requests
import json
from datetime import datetime

def debug_order_data():
    """Debug the actual order data structure"""
    
    business_id = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
    base_url = 'http://localhost:8060'
    
    print("🔍 DEBUGGING ORDER DATA STRUCTURE")
    print("=" * 60)
    print(f"Business ID: {business_id}")
    print(f"Debug Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test a simple endpoint to see what data we can access
        print("\n1️⃣ Testing orders endpoint...")
        
        # Try to get orders data directly
        orders_url = f"{base_url}/api/v1/operations/orders/{business_id}"
        try:
            orders_response = requests.get(orders_url, timeout=10)
            if orders_response.status_code == 200:
                orders_data = orders_response.json()
                print(f"   ✅ Orders endpoint working")
                print(f"   📊 Found {len(orders_data)} orders")
                
                if orders_data:
                    sample_order = orders_data[0]
                    print(f"   📋 Sample order structure:")
                    for key, value in sample_order.items():
                        print(f"      {key}: {value}")
            else:
                print(f"   ❌ Orders endpoint failed: {orders_response.status_code}")
        except Exception as e:
            print(f"   ❌ Orders endpoint error: {str(e)}")
        
        # Test menu items endpoint
        print("\n2️⃣ Testing menu items endpoint...")
        menu_url = f"{base_url}/api/v1/menu/items?business_id={business_id}"
        try:
            menu_response = requests.get(menu_url, timeout=10)
            if menu_response.status_code == 200:
                menu_data = menu_response.json()
                print(f"   ✅ Menu items endpoint working")
                print(f"   📊 Found {len(menu_data)} menu items")
                
                if menu_data:
                    sample_item = menu_data[0]
                    print(f"   📋 Sample menu item structure:")
                    for key, value in sample_item.items():
                        print(f"      {key}: {value}")
            else:
                print(f"   ❌ Menu items endpoint failed: {menu_response.status_code}")
        except Exception as e:
            print(f"   ❌ Menu items endpoint error: {str(e)}")
        
        # Test categories endpoint
        print("\n3️⃣ Testing categories endpoint...")
        categories_url = f"{base_url}/api/v1/menu/categories?business_id={business_id}"
        try:
            categories_response = requests.get(categories_url, timeout=10)
            if categories_response.status_code == 200:
                categories_data = categories_response.json()
                print(f"   ✅ Categories endpoint working")
                print(f"   📊 Found {len(categories_data)} categories")
                
                if categories_data:
                    sample_category = categories_data[0]
                    print(f"   📋 Sample category structure:")
                    for key, value in sample_category.items():
                        print(f"      {key}: {value}")
            else:
                print(f"   ❌ Categories endpoint failed: {categories_response.status_code}")
        except Exception as e:
            print(f"   ❌ Categories endpoint error: {str(e)}")
        
        # Check if there's an order_items endpoint
        print("\n4️⃣ Testing order_items endpoint...")
        order_items_url = f"{base_url}/api/v1/operations/order-items?business_id={business_id}"
        try:
            order_items_response = requests.get(order_items_url, timeout=10)
            if order_items_response.status_code == 200:
                order_items_data = order_items_response.json()
                print(f"   ✅ Order items endpoint working")
                print(f"   📊 Found {len(order_items_data)} order items")
                
                if order_items_data:
                    sample_order_item = order_items_data[0]
                    print(f"   📋 Sample order item structure:")
                    for key, value in sample_order_item.items():
                        print(f"      {key}: {value}")
            else:
                print(f"   ❌ Order items endpoint failed: {order_items_response.status_code}")
        except Exception as e:
            print(f"   ❌ Order items endpoint error: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🔍 DEBUG COMPLETE")
        print("   Check the output above to understand the data structure")
        print("   This will help identify why revenue calculation isn't working")
        
    except Exception as e:
        print(f"❌ Debug Error: {str(e)}")

if __name__ == "__main__":
    debug_order_data()
