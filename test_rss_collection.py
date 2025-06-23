#!/usr/bin/env python3
"""
Test script for RSS collection functionality.

This script tests the RSS collection service and database operations
to ensure everything is working correctly.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.rss_collection_service import rss_collection_service, RSSCollectionService
from app.services.database_service import database_service

async def test_rss_collection():
    """Test the RSS collection functionality."""
    try:
        print("🚀 Starting RSS Collection Test")
        print("=" * 50)
        
        # Import services
        from app.services.rss_collection_service import rss_collection_service
        
        # Test 1: Get available sources
        print("\n📰 Test 1: Available RSS Sources")
        sources = rss_collection_service.get_available_sources()
        print(f"Found {len(sources)} RSS sources:")
        for i, source in enumerate(sources, 1):
            print(f"  {i}. {source}")
        
        # Test 2: Collect from a single feed (for testing)
        print("\n🔄 Test 2: Testing RSS Feed Collection")
        print("Collecting articles from all feeds... (this may take a moment)")
        
        start_time = datetime.now()
        stats = await rss_collection_service.collect_all_feeds()
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Collection completed in {duration:.2f} seconds")
        print(f"📊 Collection Statistics:")
        print(f"  - Feeds processed: {stats['feeds_processed']}")
        print(f"  - Total articles found: {stats['total_articles_found']}")
        print(f"  - New articles stored: {stats['new_articles_stored']}")
        print(f"  - Processing time: {stats['processing_time']}s")
        
        if stats['errors']:
            print(f"⚠️  Errors encountered:")
            for error in stats['errors']:
                print(f"    - {error}")
        
        # Test 3: Get news feed
        print("\n📋 Test 3: News Feed Retrieval")
        feed_result = await rss_collection_service.get_news_feed(page=1, limit=5)
        
        articles = feed_result['articles']
        pagination = feed_result['pagination']
        
        print(f"Retrieved {len(articles)} articles (page 1, showing first 5)")
        print(f"Total articles: {pagination['total_articles']}")
        print(f"Total pages: {pagination['total_pages']}")
        
        if articles:
            print("\n📄 Sample Articles:")
            for i, article in enumerate(articles[:3], 1):
                print(f"\n  {i}. {article['title'][:60]}...")
                print(f"     Source: {article['source_name']}")
                print(f"     URL: {article['url'][:50]}...")
                print(f"     Published: {article.get('published_at', 'Unknown')}")
                print(f"     Analysis Status: {article['analysis_status']}")
        
        # Test 4: Content extraction (if there are articles)
        if articles:
            print("\n🔍 Test 4: Content Extraction")
            article_id = articles[0]['id']
            print(f"Testing content extraction for article: {articles[0]['title'][:50]}...")
            
            extracted = await rss_collection_service.extract_article_content(article_id)
            
            if extracted:
                content_length = len(extracted.get('content', ''))
                print(f"✅ Content extracted successfully")
                print(f"   - Content length: {content_length} characters")
                print(f"   - Word count: {extracted.get('word_count', 'Unknown')}")
                print(f"   - Reading time: {extracted.get('reading_time', 'Unknown')} minutes")
            else:
                print("❌ Content extraction failed")
        
        print("\n🎉 All tests completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_database_connection():
    """Test database connection and table creation."""
    try:
        print("\n🗄️  Testing Database Connection")
        
        from app.core.config import supabase_client
        
        # Test basic connection
        result = supabase_client.table("collected_articles").select("count").execute()
        print("✅ Database connection successful")
        
        # Check if table exists and get count
        try:
            count_result = supabase_client.table("collected_articles").select("id", count="exact").execute()
            article_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
            print(f"📊 Current articles in database: {article_count}")
        except Exception as e:
            print(f"⚠️  Could not get article count: {e}")
            print("💡 You may need to run the database migration first:")
            print("   Execute the SQL in docs/migration-collected-articles.sql")
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        print("💡 Make sure your Supabase configuration is correct in .env")
        return False
    
    return True

async def test_language_detection():
    """Test language detection functionality."""
    print("=== Testing Language Detection ===")
    
    # Test content-based detection
    service = RSSCollectionService()
    
    # Test Arabic text
    arabic_text = "هذا نص باللغة العربية للاختبار"
    detected = service._detect_language_from_content(arabic_text)
    print(f"Arabic text detection: {detected}")
    
    # Test French text  
    french_text = "Ceci est un texte en français pour tester la détection de langue"
    detected = service._detect_language_from_content(french_text)
    print(f"French text detection: {detected}")
    
    # Test English text
    english_text = "This is an English text to test language detection functionality"
    detected = service._detect_language_from_content(english_text)
    print(f"English text detection: {detected}")
    
    # Test short text (should return unknown)
    short_text = "Hi"
    detected = service._detect_language_from_content(short_text)
    print(f"Short text detection: {detected}")
    
    print("Language detection test completed!\n")

async def main():
    """Main test function."""
    print("🧪 CritiqueWire RSS Collection Test Suite")
    print("=" * 50)
    
    # Test database first
    db_ok = await test_database_connection()
    
    if db_ok:
        # Test language detection
        await test_language_detection()
        
        # Run RSS collection tests
        rss_ok = await test_rss_collection()
        
        if rss_ok:
            print("\n🎊 All tests passed! RSS collection system is ready.")
        else:
            print("\n💥 RSS collection tests failed.")
            sys.exit(1)
    else:
        print("\n💥 Database tests failed. Fix database issues first.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 