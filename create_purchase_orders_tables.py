#!/usr/bin/env python3
"""
Create Purchase Orders Tables Script
Uses the same database connection as the running application
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.database import DatabaseService

def create_purchase_orders_tables():
    """Create the purchase orders tables using the application's database service"""
    print("🚀 Creating Purchase Orders Tables...")
    
    try:
        # Initialize database service (this will use the same connection as the app)
        db = DatabaseService()
        print("✅ Connected to database using application's database service")
        
        # Read the SQL file
        sql_file_path = "database_migrations/create_purchase_orders_table.sql"
        
        if not Path(sql_file_path).exists():
            print(f"❌ SQL file not found: {sql_file_path}")
            return False
        
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("📄 Executing SQL migration...")
        
        # Split SQL into individual statements
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements):
            if not statement:
                continue
                
            try:
                # Execute statement using the database client
                result = db.client.rpc('exec_sql', {'sql': statement}).execute()
                success_count += 1
                print(f"✅ Statement {i+1}/{len(statements)} executed successfully")
                
            except Exception as e:
                error_count += 1
                print(f"❌ Statement {i+1}/{len(statements)} failed: {str(e)}")
                # Continue with other statements
                continue
        
        print(f"\n📊 Migration Results:")
        print(f"  ✅ Successful: {success_count}")
        print(f"  ❌ Failed: {error_count}")
        
        if error_count == 0:
            print("\n🎉 Purchase Orders tables created successfully!")
            print("\n📋 Created tables:")
            print("  - purchase_orders (manages purchase orders)")
            print("  - suppliers (manages supplier information)")
            print("  - inventory_items (manages inventory items)")
            print("  - inventory_transactions (tracks stock movements)")
            print("  - stock_alerts (manages low stock alerts)")
            print("\n🚀 Ready to use Purchase Orders functionality!")
            return True
        else:
            print(f"\n⚠️  Setup completed with {error_count} errors")
            print("Some features may not work correctly.")
            return False
            
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False

def verify_tables():
    """Verify that the tables were created successfully"""
    print("\n🔍 Verifying tables...")
    
    try:
        db = DatabaseService()
        
        # Check if tables exist by trying to query them
        tables_to_check = [
            "purchase_orders",
            "suppliers", 
            "inventory_items",
            "inventory_transactions",
            "stock_alerts"
        ]
        
        verified_tables = []
        
        for table in tables_to_check:
            try:
                # Try to query the table (limit 0 to just check structure)
                result = db.client.table(table).select("*").limit(0).execute()
                verified_tables.append(table)
                print(f"✅ Table '{table}' exists and is accessible")
            except Exception as e:
                print(f"❌ Table '{table}' not found or not accessible: {str(e)}")
        
        print(f"\n📊 Verification Results:")
        print(f"  ✅ Verified tables: {len(verified_tables)}/{len(tables_to_check)}")
        
        if len(verified_tables) == len(tables_to_check):
            print("🎉 All purchase orders tables are ready!")
            return True
        else:
            print("⚠️  Some tables are missing. Check the migration errors above.")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("📦 PURCHASE ORDERS & INVENTORY SETUP")
    print("=" * 60)
    
    # Create tables
    setup_success = create_purchase_orders_tables()
    
    if setup_success:
        # Verify setup
        verify_success = verify_tables()
        
        if verify_success:
            print("\n" + "=" * 60)
            print("🎉 PURCHASE ORDERS SETUP COMPLETE!")
            print("=" * 60)
            print("Your Purchase Orders and Inventory management is ready!")
            print("\nThe 500 error should now be resolved!")
        else:
            print("\n⚠️  Setup completed but verification failed")
    else:
        print("\n❌ Setup failed")
