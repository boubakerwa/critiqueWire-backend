#!/usr/bin/env python3
"""
Debug script for RSS collection to see what's happening with article storage.
"""

import asyncio
import sys
import os
from datetime import datetime
import aiohttp

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def debug_rss_collection():
    """Debug RSS collection step by step."""
    try:
        print("🔍 Debugging RSS Collection")
        print("=" * 50)
        
        from app.services.rss_collection_service import rss_collection_service
        from app.services.database_service import database_service
        
        print("✅ Services imported")
        
        # Test with just one working RSS feed
        test_sources = {
            "Webdo": "https://www.webdo.tn/feed"
        }
        
        print(f"\n📰 Testing with {list(test_sources.keys())[0]}...")
        
        async with aiohttp.ClientSession() as session:
            # Fetch from one feed
            articles = await rss_collection_service._fetch_rss_feed(
                "Webdo", 
                "https://www.webdo.tn/feed", 
                session
            )
            
            print(f"✅ Fetched {len(articles)} articles from RSS feed")
            
            if articles:
                # Show details of first article
                first_article = articles[0]
                print(f"\n📄 First article details:")
                print(f"   Title: {first_article['title'][:60]}...")
                print(f"   URL: {first_article['url']}")
                print(f"   Source: {first_article['source_name']}")
                print(f"   Hash: {first_article['content_hash']}")
                print(f"   Published: {first_article.get('published_at')}")
                print(f"   Images: {len(first_article.get('images', []))}")
                print(f"   Thumbnail: {first_article.get('thumbnail_url')}")
                
                # Test duplicate check for this article
                print(f"\n🔍 Testing duplicate check for this article...")
                existing = database_service.supabase.table("articles").select("id").or_(
                    f"content_hash.eq.{first_article['content_hash']},url.eq.{first_article['url']}"
                ).execute()
                
                print(f"   Duplicate check result: {len(existing.data)} matches found")
                
                if existing.data:
                    print(f"   ⚠️  Article already exists in database!")
                    # Show existing article details
                    existing_article = database_service.supabase.table("articles").select("*").eq("id", existing.data[0]['id']).execute()
                    if existing_article.data:
                        existing = existing_article.data[0]
                        print(f"   Existing article: {existing['title'][:60]}...")
                        print(f"   Created: {existing['created_at']}")
                        print(f"   Collected: {existing['collected_at']}")
                else:
                    print(f"   ✅ Article is new, should be stored")
                    
                    # Try to store just this one article
                    print(f"\n💾 Attempting to store this article...")
                    
                    content = f"{first_article['title']}\n\n(Click to read full article)"
                    
                    article_data = {
                        "title": first_article['title'],
                        "content": content,
                        "url": first_article['url'],
                        "source_name": first_article['source_name'],
                        "author": first_article.get('author'),
                        "published_at": first_article.get('published_at').isoformat() if first_article.get('published_at') else None,
                        "summary": first_article.get('summary'),
                        "source_url": first_article['source_url'],
                        "collected_at": first_article['collected_at'].isoformat() if first_article['collected_at'] else None,
                        "content_hash": first_article['content_hash'],
                        "images": first_article.get('images', []),
                        "thumbnail_url": first_article.get('thumbnail_url'),
                        "analysis_status": 'not_analyzed'
                    }
                    
                    print(f"   Article data prepared, inserting...")
                    
                    result = database_service.supabase.table("articles").insert(article_data).execute()
                    
                    if result.data:
                        print(f"   ✅ Successfully stored article with ID: {result.data[0]['id']}")
                    else:
                        print(f"   ❌ Failed to store article")
                        print(f"   Result: {result}")
                
                # Test the full storage method
                print(f"\n🔄 Testing full _store_articles method...")
                stored_count = await rss_collection_service._store_articles(articles[:3])  # Just first 3
                print(f"   Stored {stored_count} out of 3 articles")
                
        print(f"\n🎉 Debug completed!")
        
    except Exception as e:
        print(f"\n❌ Debug failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(debug_rss_collection()) 