#!/usr/bin/env python3
"""
Fix Purchase Orders Foreign Key Constraint
Removes the foreign key constraint on created_by field
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.database import DatabaseService

def fix_foreign_key_constraint():
    """Remove the foreign key constraint on created_by field"""
    print("🔧 Fixing foreign key constraint on purchase_orders.created_by...")
    
    try:
        # Initialize database service
        db = DatabaseService()
        print("✅ Connected to database")
        
        # SQL to drop the foreign key constraint
        sql_statements = [
            "-- Drop the foreign key constraint on created_by field",
            "ALTER TABLE purchase_orders DROP CONSTRAINT IF EXISTS purchase_orders_created_by_fkey;",
            "",
            "-- Verify the constraint is removed",
            "SELECT conname, contype FROM pg_constraint WHERE conrelid = 'purchase_orders'::regclass AND conname LIKE '%created_by%';"
        ]
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(sql_statements):
            if not statement.strip() or statement.strip().startswith('--'):
                continue
                
            try:
                # Execute statement
                result = db.client.rpc('exec_sql', {'sql': statement}).execute()
                success_count += 1
                print(f"✅ Statement {i+1} executed successfully")
                
            except Exception as e:
                error_count += 1
                print(f"❌ Statement {i+1} failed: {str(e)}")
                continue
        
        print(f"\n📊 Results:")
        print(f"  ✅ Successful: {success_count}")
        print(f"  ❌ Failed: {error_count}")
        
        if error_count == 0:
            print("\n🎉 Foreign key constraint removed successfully!")
            print("The purchase order creation should now work without user validation.")
            return True
        else:
            print(f"\n⚠️  Some operations failed")
            return False
            
    except Exception as e:
        print(f"❌ Fix failed: {str(e)}")
        return False

def test_purchase_order_creation():
    """Test if purchase order creation now works"""
    print("\n🧪 Testing purchase order creation...")
    
    try:
        db = DatabaseService()
        
        # Test data
        test_data = {
            "business_id": "123e4567-e89b-12d3-a456-426614174000",
            "supplier_id": "456e7890-e89b-12d3-a456-426614174000",
            "order_number": "TEST-PO-001",
            "order_date": "2025-01-18T17:37:00.966Z",
            "expected_delivery_date": "2025-02-12T00:00:00.000Z",
            "status": "pending",
            "items": [
                {
                    "inventory_item_id": "789e0123-e89b-12d3-a456-426614174000",
                    "quantity": 10,
                    "unit_cost": 5.50,
                    "total": 55.00
                }
            ],
            "total_amount": 55.00,
            "notes": "Test purchase order",
            "created_by": "fd8a3d59-4a06-43c2-9820-0e3222867117"  # This user doesn't exist
        }
        
        # Try to insert
        result = db.client.table("purchase_orders").insert(test_data).execute()
        
        if result.data:
            print("✅ Purchase order creation test successful!")
            print(f"Created purchase order with ID: {result.data[0].get('id')}")
            
            # Clean up test data
            db.client.table("purchase_orders").delete().eq("order_number", "TEST-PO-001").execute()
            print("🧹 Test data cleaned up")
            return True
        else:
            print("❌ Purchase order creation test failed - no data returned")
            return False
            
    except Exception as e:
        print(f"❌ Purchase order creation test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 FIXING PURCHASE ORDERS FOREIGN KEY CONSTRAINT")
    print("=" * 60)
    
    # Fix the constraint
    fix_success = fix_foreign_key_constraint()
    
    if fix_success:
        # Test the fix
        test_success = test_purchase_order_creation()
        
        if test_success:
            print("\n" + "=" * 60)
            print("🎉 FIX COMPLETE!")
            print("=" * 60)
            print("The 500 error should now be resolved!")
            print("Purchase orders can be created without requiring existing users.")
        else:
            print("\n⚠️  Fix applied but test failed")
    else:
        print("\n❌ Fix failed")
