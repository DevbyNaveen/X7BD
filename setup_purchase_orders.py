#!/usr/bin/env python3
"""
Purchase Orders Table Setup Script
Creates the purchase_orders table and related inventory tables in Supabase
"""

import os
import sys
import asyncio
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """Get Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    
    return create_client(url, key)

def read_sql_file(file_path: str) -> str:
    """Read SQL file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ SQL file not found: {file_path}")
        return None

async def setup_purchase_orders_tables():
    """Set up the purchase orders and inventory tables"""
    print("🚀 Setting up Purchase Orders and Inventory Tables...")
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")
        
        # Read SQL file
        sql_file_path = "database_migrations/create_purchase_orders_table.sql"
        
        if not Path(sql_file_path).exists():
            print(f"❌ SQL file not found: {sql_file_path}")
            return False
        
        sql_content = read_sql_file(sql_file_path)
        if not sql_content:
            return False
        
        print("📄 Reading SQL migration file...")
        
        # Execute SQL
        print("🔄 Executing SQL migration...")
        
        # Split SQL into individual statements
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements):
            if not statement or statement.startswith('--'):
                continue
                
            try:
                # Execute statement
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
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
            print("\n🎉 Purchase Orders tables setup completed successfully!")
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

async def verify_purchase_orders_setup():
    """Verify that the purchase orders tables were created successfully"""
    print("\n🔍 Verifying purchase orders tables setup...")
    
    try:
        supabase = get_supabase_client()
        
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
                result = supabase.table(table).select("*").limit(0).execute()
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

async def main():
    """Main setup function"""
    print("=" * 60)
    print("📦 PURCHASE ORDERS & INVENTORY SETUP")
    print("=" * 60)
    
    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ Missing required environment variables:")
        print("   SUPABASE_URL")
        print("   SUPABASE_KEY")
        print("\nPlease set these in your .env file or environment")
        return
    
    # Setup database
    setup_success = await setup_purchase_orders_tables()
    
    if setup_success:
        # Verify setup
        verify_success = await verify_purchase_orders_setup()
        
        if verify_success:
            print("\n" + "=" * 60)
            print("🎉 PURCHASE ORDERS SETUP COMPLETE!")
            print("=" * 60)
            print("Your Purchase Orders and Inventory management is ready!")
            print("\nNext steps:")
            print("1. Start your FastAPI server: python -m app.main")
            print("2. Test the purchase orders API")
            print("3. Create your first purchase order!")
        else:
            print("\n⚠️  Setup completed but verification failed")
            print("Check the errors above and try running the SQL manually")
    else:
        print("\n❌ Setup failed")
        print("Please check the errors above and try again")

if __name__ == "__main__":
    asyncio.run(main())
