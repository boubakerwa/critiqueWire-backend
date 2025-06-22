#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.rss_collection_service import RSSCollectionService

async def test_image_extraction():
    print("🧪 Testing image extraction fix...")
    
    # Create RSS service instance
    rss_service = RSSCollectionService()
    
    # Test just Mosaique FM (which we know has images)
    test_feeds = {
        "Mosaique FM": "https://www.mosaiquefm.net/rss"
    }
    
    # Temporarily override the sources to just test Mosaique FM
    original_sources = rss_service.sources
    rss_service.sources = test_feeds
    
    try:
        print("🔄 Collecting articles from Mosaique FM...")
        result = await rss_service.collect_all_feeds()
        
        print(f"📊 Collection results:")
        print(f"   - Feeds processed: {result['feeds_processed']}")
        print(f"   - Articles found: {result['total_articles_found']}")
        print(f"   - New articles stored: {result['new_articles_stored']}")
        print(f"   - Processing time: {result['processing_time']}s")
        
        if result['errors']:
            print(f"❌ Errors: {result['errors']}")
        
        # Now check if we have images in the database
        print("\n🔍 Checking for images in newly collected articles...")
        
        from app.services.database_service import database_service
        
        # Get the most recent Mosaique FM articles
        recent_articles = database_service.supabase.table("articles").select(
            "id, title, images, thumbnail_url, source_name, collected_at"
        ).eq("source_name", "Mosaique FM").order("collected_at", desc=True).limit(5).execute()
        
        if recent_articles.data:
            print(f"📰 Found {len(recent_articles.data)} recent Mosaique FM articles:")
            
            for i, article in enumerate(recent_articles.data):
                print(f"\n  {i+1}. {article['title'][:50]}...")
                print(f"     Images: {len(article.get('images', []))} images")
                if article.get('images'):
                    for j, img in enumerate(article['images'][:3]):
                        print(f"       - Image {j+1}: {img}")
                print(f"     Thumbnail: {article.get('thumbnail_url', 'None')}")
        else:
            print("❌ No recent Mosaique FM articles found")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original sources
        rss_service.sources = original_sources

if __name__ == "__main__":
    asyncio.run(test_image_extraction()) 