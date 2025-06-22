#!/usr/bin/env python3
"""
Test script to debug database insertion issues.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
import json

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_db_insert():
    """Test direct database insertion."""
    try:
        print("🔍 Testing Database Insertion")
        print("=" * 50)
        
        from app.services.database_service import database_service
        
        print("✅ Database service imported")
        
        # Test 1: Check if we can query the articles table
        print("\n📋 Testing articles table query...")
        result = database_service.supabase.table("articles").select("id").limit(1).execute()
        print(f"✅ Articles table accessible, found {len(result.data)} articles")
        
        # Test 2: Try to insert a simple test article
        print("\n📝 Testing article insertion...")
        
        test_article = {
            "title": "Test Article from RSS Collection",
            "content": "This is a test article to verify database insertion.",
            "url": f"https://test.example.com/article-{datetime.now().timestamp()}",
            "source_name": "Test Source",
            "author": "Test Author",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "summary": "A test article summary",
            "source_url": "https://test.example.com/rss",
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": f"test-hash-{datetime.now().timestamp()}",
            "images": ["https://test.example.com/image1.jpg"],
            "thumbnail_url": "https://test.example.com/thumb.jpg",
            "analysis_status": "not_analyzed"
        }
        
        print(f"Inserting test article: {test_article['title']}")
        
        insert_result = database_service.supabase.table("articles").insert(test_article).execute()
        
        if insert_result.data:
            print(f"✅ Successfully inserted article with ID: {insert_result.data[0]['id']}")
            
            # Test 3: Query the article back
            article_id = insert_result.data[0]['id']
            query_result = database_service.supabase.table("articles").select("*").eq("id", article_id).execute()
            
            if query_result.data:
                article = query_result.data[0]
                print(f"✅ Successfully queried back article:")
                print(f"   Title: {article['title']}")
                print(f"   Source: {article['source_name']}")
                print(f"   Images: {article['images']}")
                print(f"   Collected at: {article['collected_at']}")
                
                # Test 4: Clean up - delete the test article
                delete_result = database_service.supabase.table("articles").delete().eq("id", article_id).execute()
                if delete_result.data:
                    print(f"✅ Successfully cleaned up test article")
                
            else:
                print("❌ Could not query back the inserted article")
        else:
            print("❌ Failed to insert test article")
            print(f"Insert result: {insert_result}")
        
        # Test 5: Test the duplicate check query
        print("\n🔍 Testing duplicate check query...")
        
        test_hash = "test-duplicate-hash"
        test_url = "https://test.example.com/duplicate-test"
        
        # This is the query that might be failing
        try:
            existing = database_service.supabase.table("articles").select("id").or_(
                f"content_hash.eq.{test_hash},url.eq.{test_url}"
            ).execute()
            
            print(f"✅ Duplicate check query works, found {len(existing.data)} matches")
            
        except Exception as e:
            print(f"❌ Duplicate check query failed: {e}")
            print("This might be why articles aren't being stored!")
            
            # Try alternative query syntax
            try:
                existing = database_service.supabase.table("articles").select("id").eq("content_hash", test_hash).execute()
                print(f"✅ Alternative query syntax works")
            except Exception as e2:
                print(f"❌ Alternative query also failed: {e2}")
        
        print(f"\n🎉 Database insertion test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_db_insert()) 