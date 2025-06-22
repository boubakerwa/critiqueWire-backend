#!/usr/bin/env python3
"""
Simple test script for RSS collection functionality.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_rss_simple():
    """Simple test of RSS collection."""
    try:
        print("🚀 Testing RSS Collection")
        print("=" * 50)
        
        # Import services
        from app.services.rss_collection_service import rss_collection_service
        
        print("✅ RSS service imported successfully")
        
        # Test 1: Get available sources
        sources = rss_collection_service.get_available_sources()
        print(f"📰 Found {len(sources)} RSS sources:")
        for i, source in enumerate(sources, 1):
            print(f"  {i}. {source}")
        
        # Test 2: Try to collect from one feed manually
        print(f"\n🔄 Testing RSS collection...")
        
        start_time = datetime.now()
        stats = await rss_collection_service.collect_all_feeds()
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Collection completed in {duration:.2f} seconds")
        print(f"📊 Results:")
        print(f"  - Feeds processed: {stats['feeds_processed']}")
        print(f"  - Articles found: {stats['total_articles_found']}")
        print(f"  - New articles stored: {stats['new_articles_stored']}")
        print(f"  - Processing time: {stats['processing_time']}s")
        
        if stats['errors']:
            print(f"⚠️  Errors:")
            for error in stats['errors']:
                print(f"    - {error}")
        
        # Test 3: Try to get news feed
        print(f"\n📋 Testing news feed retrieval...")
        feed_result = await rss_collection_service.get_news_feed(page=1, limit=5)
        
        articles = feed_result['articles']
        pagination = feed_result['pagination']
        
        print(f"Retrieved {len(articles)} articles")
        print(f"Total articles: {pagination['total_articles']}")
        
        if articles:
            print("\n📄 Sample Articles:")
            for i, article in enumerate(articles[:3], 1):
                print(f"\n  {i}. {article['title'][:60]}...")
                print(f"     Source: {article['source_name']}")
                print(f"     Images: {len(article.get('images', []))}")
                print(f"     Thumbnail: {'Yes' if article.get('thumbnail_url') else 'No'}")
        
        print(f"\n🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_rss_simple()) 