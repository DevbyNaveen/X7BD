#!/usr/bin/env python3
"""
Quick Database Setup Script
Sets up the QR code tables in Supabase
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
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) must be set in environment variables")
    
    return create_client(url, key)

async def setup_database():
    """Set up the database with QR code tables"""
    print("🚀 Setting up QR Code Database Tables...")
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")
        
        # Read SQL file
        sql_file = Path("database_migrations/create_food_qr_tables_simple.sql")
        if not sql_file.exists():
            print("❌ SQL migration file not found!")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as f:
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
                # Execute statement using rpc
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                success_count += 1
                print(f"✅ Statement {i+1}/{len(statements)} executed successfully")
                
            except Exception as e:
                # Try direct execution if rpc fails
                try:
                    supabase.postgrest.session.post(
                        f"{supabase.url}/rest/v1/rpc/exec_sql",
                        json={"sql": statement},
                        headers=supabase.postgrest.session.headers
                    )
                    success_count += 1
                    print(f"✅ Statement {i+1}/{len(statements)} executed successfully (direct)")
                except Exception as e2:
                    error_count += 1
                    print(f"❌ Statement {i+1}/{len(statements)} failed: {str(e2)}")
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
            print("\n🚀 Ready to use QR code functionality!")
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

async def main():
    """Main setup function"""
    print("=" * 60)
    print("🍽️  QR CODE DATABASE SETUP")
    print("=" * 60)
    
    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")):
        print("❌ Missing required environment variables:")
        print("   SUPABASE_URL")
        print("   SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY)")
        print("\nPlease set these in your .env file or environment")
        return
    
    # Setup database
    setup_success = await setup_database()
    
    if setup_success:
        # Verify setup
        verify_success = await verify_setup()
        
        if verify_success:
            print("\n" + "=" * 60)
            print("🎉 SETUP COMPLETE!")
            print("=" * 60)
            print("Your QR code backend is ready to use!")
            print("\nNext steps:")
            print("1. Start your FastAPI server: python -m app.main")
            print("2. Test the QR functionality: python test_qr_functionality.py")
            print("3. Visit API docs: http://localhost:8060/docs")
        else:
            print("\n⚠️  Setup completed but verification failed")
            print("Check the errors above and try running the SQL manually")
    else:
        print("\n❌ Setup failed")
        print("Please check the errors above and try again")

if __name__ == "__main__":
    asyncio.run(main())
