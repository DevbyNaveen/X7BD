#!/usr/bin/env python3
"""
Food QR Database Setup Script
Automatically creates the necessary tables in Supabase for Food QR functionality
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

async def setup_database():
    """Set up the database with Food QR tables"""
    print("🚀 Setting up Food QR Database...")
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")
        
        # Read SQL files
        simple_sql_path = "database_migrations/create_food_qr_tables_simple.sql"
        full_sql_path = "database_migrations/create_food_qr_tables.sql"
        
        # Check which SQL file exists
        sql_content = None
        sql_type = None
        
        if Path(simple_sql_path).exists():
            sql_content = read_sql_file(simple_sql_path)
            sql_type = "simple"
        elif Path(full_sql_path).exists():
            sql_content = read_sql_file(full_sql_path)
            sql_type = "full"
        else:
            print("❌ No SQL migration files found!")
            print("Expected files:")
            print(f"  - {simple_sql_path}")
            print(f"  - {full_sql_path}")
            return False
        
        if not sql_content:
            return False
        
        print(f"📄 Using {sql_type} SQL migration file")
        
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
            print("\n🎉 Database setup completed successfully!")
            print("\n📋 Created tables:")
            print("  - qr_codes (stores QR code metadata)")
            print("  - qr_scans (tracks scan events)")
            print("  - tables (manages restaurant tables)")
            print("  - business_locations (stores location info)")
            
            if sql_type == "full":
                print("  - food_tracking_events (tracks food lifecycle)")
                print("  - pos_integrations (POS system integration)")
                print("  - qr_code_templates (QR appearance templates)")
                print("  - qr_code_exports (export tracking)")
            
            print("\n🚀 Ready to use Food QR backend!")
            return True
        else:
            print(f"\n⚠️  Setup completed with {error_count} errors")
            print("Some features may not work correctly.")
            return False
            
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False

async def verify_setup():
    """Verify that the tables were created successfully"""
    print("\n🔍 Verifying database setup...")
    
    try:
        supabase = get_supabase_client()
        
        # Check if tables exist by trying to query them
        tables_to_check = [
            "qr_codes",
            "qr_scans", 
            "tables",
            "business_locations"
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
            print("🎉 All required tables are ready!")
            return True
        else:
            print("⚠️  Some tables are missing. Check the migration errors above.")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

async def create_sample_data():
    """Create sample data for testing"""
    print("\n📝 Creating sample data...")
    
    try:
        supabase = get_supabase_client()
        
        # Sample business ID (replace with your actual business ID)
        sample_business_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # Create sample location
        location_data = {
            "business_id": sample_business_id,
            "name": "Main Restaurant",
            "address": "123 Main Street",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "USA",
            "phone": "+1-555-0123",
            "email": "info@restaurant.com"
        }
        
        result = supabase.table("business_locations").insert(location_data).execute()
        print("✅ Sample business location created")
        
        # Create sample table
        table_data = {
            "table_number": "1",
            "business_id": sample_business_id,
            "capacity": 4,
            "is_active": True
        }
        
        result = supabase.table("tables").insert(table_data).execute()
        print("✅ Sample table created")
        
        print("📝 Sample data created successfully!")
        print(f"   Business ID: {sample_business_id}")
        print("   Location: Main Restaurant")
        print("   Table: Table 1 (4 seats)")
        
        return True
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {str(e)}")
        return False

async def main():
    """Main setup function"""
    print("=" * 60)
    print("🍽️  FOOD QR CODE DATABASE SETUP")
    print("=" * 60)
    
    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ Missing required environment variables:")
        print("   SUPABASE_URL")
        print("   SUPABASE_KEY")
        print("\nPlease set these in your .env file or environment")
        return
    
    # Setup database
    setup_success = await setup_database()
    
    if setup_success:
        # Verify setup
        verify_success = await verify_setup()
        
        if verify_success:
            # Create sample data
            await create_sample_data()
            
            print("\n" + "=" * 60)
            print("🎉 SETUP COMPLETE!")
            print("=" * 60)
            print("Your Food QR backend is ready to use!")
            print("\nNext steps:")
            print("1. Start your FastAPI server: python -m app.main")
            print("2. Test the API: python test_food_qr.py")
            print("3. Visit API docs: http://localhost:8060/docs")
            print("4. Generate your first QR code!")
        else:
            print("\n⚠️  Setup completed but verification failed")
            print("Check the errors above and try running the SQL manually")
    else:
        print("\n❌ Setup failed")
        print("Please check the errors above and try again")

if __name__ == "__main__":
    asyncio.run(main())
