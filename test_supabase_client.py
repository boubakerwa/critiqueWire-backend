#!/usr/bin/env python3
"""
Test script to verify Supabase client functionality.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_supabase_client():
    """Test Supabase client directly."""
    try:
        print("🔍 Testing Supabase Client")
        print("=" * 50)
        
        from app.services.database_service import database_service
        
        print("✅ Database service imported")
        
        # Test 1: Simple count query
        print("\n📊 Testing simple count query...")
        try:
            result = database_service.supabase.table("articles").select("*", count="exact").execute()
            print(f"✅ Count query successful")
            print(f"   Total articles: {result.count if hasattr(result, 'count') else 'Unknown'}")
            print(f"   Data length: {len(result.data)}")
        except Exception as e:
            print(f"❌ Count query failed: {e}")
        
        # Test 2: Simple select query
        print("\n📋 Testing simple select query...")
        try:
            result = database_service.supabase.table("articles").select("id, title, source_name").limit(3).execute()
            print(f"✅ Select query successful")
            print(f"   Retrieved {len(result.data)} articles")
            for i, article in enumerate(result.data, 1):
                print(f"   {i}. {article['title'][:50]}... ({article['source_name']})")
        except Exception as e:
            print(f"❌ Select query failed: {e}")
        
        # Test 3: Ordered query
        print("\n🔄 Testing ordered query...")
        try:
            result = database_service.supabase.table("articles").select("id, title, created_at").order("created_at.desc").limit(3).execute()
            print(f"✅ Ordered query successful")
            print(f"   Retrieved {len(result.data)} articles")
            for i, article in enumerate(result.data, 1):
                print(f"   {i}. {article['title'][:50]}... ({article['created_at']})")
        except Exception as e:
            print(f"❌ Ordered query failed: {e}")
        
        # Test 4: The exact query from news feed
        print("\n🎯 Testing exact news feed query...")
        try:
            query = database_service.supabase.table("articles").select(
                "id, title, content, url, source_name, author, published_at, "
                "summary, source_url, collected_at, images, thumbnail_url, "
                "analysis_status, analysis_id, created_at, updated_at"
            )
            
            articles_result = query.order("created_at.desc").range(0, 4).execute()
            print(f"✅ News feed query successful")
            print(f"   Retrieved {len(articles_result.data)} articles")
            for i, article in enumerate(articles_result.data, 1):
                print(f"   {i}. {article['title'][:50]}... ({article['source_name']})")
                
        except Exception as e:
            print(f"❌ News feed query failed: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n🎉 Supabase client test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_supabase_client()) 