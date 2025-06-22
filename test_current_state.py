#!/usr/bin/env python3
"""
Test script to understand the current state of the CritiqueWire backend.
This will help us figure out what's working and what's missing.
"""

import asyncio
import sys
import os
from datetime import datetime
import requests

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_api_endpoints():
    """Test if the API server is running and what endpoints are available."""
    print("🌐 Testing API Server")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            print(f"   Health check: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API server not responding: {e}")
        return False
    
    # Test if news feed endpoints exist
    try:
        response = requests.get(f"{base_url}/v1/news-feed", timeout=5)
        print(f"📰 News feed endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data.get('data', {}).get('articles', []))} articles")
        elif response.status_code == 404:
            print("   ❌ News feed endpoint doesn't exist")
        else:
            print(f"   ⚠️  News feed returned: {response.status_code}")
    except Exception as e:
        print(f"   ❌ News feed test failed: {e}")
    
    return True

async def test_database_connection():
    """Test database connection and check current articles."""
    print("\n🗄️  Testing Database")
    print("=" * 50)
    
    try:
        from app.services.database_service import database_service
        
        # Check total articles
        result = await database_service.execute_query(
            "SELECT COUNT(*) as total FROM articles"
        )
        total_articles = result[0]['total'] if result else 0
        print(f"📊 Total articles in database: {total_articles}")
        
        # Check article types (manual vs RSS)
        result = await database_service.execute_query("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN collected_at IS NOT NULL THEN 1 END) as rss_articles,
                COUNT(CASE WHEN collected_at IS NULL THEN 1 END) as manual_articles
            FROM articles
        """)
        
        if result:
            stats = result[0]
            print(f"   Manual articles: {stats['manual_articles']}")
            print(f"   RSS articles: {stats['rss_articles']}")
        
        # Check image data
        result = await database_service.execute_query("""
            SELECT 
                COUNT(CASE WHEN images != '[]' AND images IS NOT NULL THEN 1 END) as with_images,
                COUNT(CASE WHEN thumbnail_url IS NOT NULL THEN 1 END) as with_thumbnails,
                COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) as with_image_url
            FROM articles
        """)
        
        if result:
            img_stats = result[0]
            print(f"📸 Image statistics:")
            print(f"   Articles with images array: {img_stats['with_images']}")
            print(f"   Articles with thumbnail_url: {img_stats['with_thumbnails']}")
            print(f"   Articles with image_url: {img_stats['with_image_url']}")
        
        # Show sample articles
        result = await database_service.execute_query("""
            SELECT id, title, source_name, collected_at, images, thumbnail_url, image_url
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        
        print(f"\n📄 Sample articles:")
        for i, article in enumerate(result, 1):
            print(f"   {i}. {article['title'][:50]}...")
            print(f"      Source: {article['source_name']}")
            print(f"      Type: {'RSS' if article['collected_at'] else 'Manual'}")
            print(f"      Images: {article['images']}")
            print(f"      Thumbnail: {article['thumbnail_url']}")
            print(f"      Image URL: {article['image_url']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_services():
    """Test what services are available."""
    print("\n🔧 Testing Services")
    print("=" * 50)
    
    services_dir = os.path.join(os.path.dirname(__file__), 'app', 'services')
    
    if os.path.exists(services_dir):
        services = [f for f in os.listdir(services_dir) if f.endswith('.py') and f != '__init__.py']
        print(f"📁 Found services: {', '.join(services)}")
        
        # Test importing each service
        for service_file in services:
            service_name = service_file[:-3]  # Remove .py
            try:
                module = __import__(f'app.services.{service_name}', fromlist=[service_name])
                print(f"   ✅ {service_name}: importable")
            except Exception as e:
                print(f"   ❌ {service_name}: {e}")
    else:
        print("❌ Services directory not found")

async def test_content_extraction():
    """Test content extraction service."""
    print("\n🔍 Testing Content Extraction")
    print("=" * 50)
    
    try:
        from app.services.content_extraction_service import ContentExtractionService
        
        extraction_service = ContentExtractionService()
        print("✅ Content extraction service initialized")
        
        # Test with a simple URL
        test_url = "https://example.com"
        print(f"🌐 Testing extraction with: {test_url}")
        
        result = await extraction_service.extract_content(test_url)
        
        if result.get('status') == 'success':
            data = result['data']
            print(f"   ✅ Extraction successful")
            print(f"   Title: {data.get('title', 'N/A')}")
            print(f"   Content length: {len(data.get('content', ''))}")
            print(f"   Images found: {len(data.get('images', []))}")
            print(f"   Strategy used: {data.get('extractionStrategy', 'N/A')}")
        else:
            print(f"   ⚠️  Extraction result: {result.get('status')}")
            if 'error' in result:
                print(f"   Error: {result['error'].get('message', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Content extraction test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 CritiqueWire Backend State Check")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    print()
    
    # Test API server first
    api_ok = test_api_endpoints()
    
    # Test services
    test_services()
    
    # Test database if API is working
    if api_ok:
        db_ok = await test_database_connection()
    else:
        print("\n⏭️  Skipping database tests (API server not running)")
        db_ok = False
    
    # Test content extraction
    extraction_ok = await test_content_extraction()
    
    print("\n📋 Summary")
    print("=" * 50)
    print(f"API Server: {'✅' if api_ok else '❌'}")
    print(f"Database: {'✅' if db_ok else '❌'}")
    print(f"Content Extraction: {'✅' if extraction_ok else '❌'}")
    
    if not any([api_ok, db_ok, extraction_ok]):
        print("\n🚨 Multiple issues detected. Check server and configuration.")
    elif api_ok and db_ok:
        print("\n🎉 Core functionality appears to be working!")
    else:
        print("\n⚠️  Some issues detected. Check the details above.")

if __name__ == "__main__":
    asyncio.run(main()) 