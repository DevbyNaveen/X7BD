#!/usr/bin/env python3
"""
Debug script to check what's actually in the database
"""

import asyncio
import httpx
from datetime import datetime, timedelta

async def debug_database_queries():
    BASE_URL = 'http://localhost:8060'
    BUSINESS_ID = 'fd8a3d59-4a06-43c2-9820-0e3222867117'
    
    async with httpx.AsyncClient() as client:
        print('🔍 Debugging database queries...')
        
        # Calculate the same date range that both endpoints should use
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        print(f'Date range: {start_date.isoformat()} to {end_date.isoformat()}')
        
        # Test Revenue by Channel (working)
        try:
            response = await client.get(f'{BASE_URL}/api/v1/analytics/revenue/by-channel/{BUSINESS_ID}?period=7d')
            if response.status_code == 200:
                data = response.json()
                print('✅ Revenue by Channel:')
                print(f'   Total Revenue: ${data.get("total_revenue", 0):.2f}')
                print(f'   Channels: {len(data.get("channel_data", []))}')
        except Exception as e:
            print(f'❌ Revenue by Channel error: {e}')
        
        # Test Revenue Overview (not working)
        try:
            response = await client.get(f'{BASE_URL}/api/v1/analytics/revenue/overview/{BUSINESS_ID}?period=7d')
            if response.status_code == 200:
                data = response.json()
                print('❌ Revenue Overview:')
                print(f'   Total Revenue: ${data.get("total_revenue", 0):.2f}')
                print(f'   Total Orders: {data.get("total_orders", 0)}')
        except Exception as e:
            print(f'❌ Revenue Overview error: {e}')
        
        # Test with different periods
        print('\n🔍 Testing different periods...')
        for period in ['1d', '30d', '90d', '1y']:
            try:
                response = await client.get(f'{BASE_URL}/api/v1/analytics/revenue/overview/{BUSINESS_ID}?period={period}')
                if response.status_code == 200:
                    data = response.json()
                    print(f'   {period}: ${data.get("total_revenue", 0):.2f} ({data.get("total_orders", 0)} orders)')
            except Exception as e:
                print(f'   {period}: Error - {e}')

if __name__ == "__main__":
    asyncio.run(debug_database_queries())
