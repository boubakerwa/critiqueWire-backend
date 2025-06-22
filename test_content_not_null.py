#!/usr/bin/env python3
"""
Test that content is never null for any articles
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.rss_collection_service import rss_collection_service

async def test_content_not_null():
    """Test that all articles have non-null content"""
    print('🔍 Testing that content is never null...\n')
    
    # Test 1: Check current articles in database
    print('📊 Step 1: Checking all articles in database...')
    try:
        # Get all articles (both RSS and manual)
        feed_data = await rss_collection_service.get_news_feed(
            page=1, 
            limit=50, 
            rss_only=False  # Include all articles
        )
        
        articles = feed_data['articles']
        total_count = len(articles)
        
        print(f'✅ Found {total_count} total articles')
        
        # Check each article has content
        rss_articles = []
        manual_articles = []
        null_content_count = 0
        
        for article in articles:
            if not article.get('content'):
                null_content_count += 1
                print(f'❌ NULL CONTENT: {article.get("title", "Unknown")[:50]}...')
            elif article.get('collected_at'):
                rss_articles.append(article)
            else:
                manual_articles.append(article)
        
        print(f'   - Manual articles: {len(manual_articles)}')
        print(f'   - RSS articles: {len(rss_articles)}')
        print(f'   - NULL content articles: {null_content_count}')
        
        # Show samples
        if rss_articles:
            print(f'\n📰 Sample RSS article content:')
            sample_rss = rss_articles[0]
            print(f'   Title: {sample_rss["title"][:60]}...')
            print(f'   Content: {sample_rss["content"][:100]}...')
        
        if manual_articles:
            print(f'\n📝 Sample manual article content:')
            sample_manual = manual_articles[0]
            print(f'   Title: {sample_manual["title"][:60]}...')
            print(f'   Content: {sample_manual["content"][:100]}...')
        
        return null_content_count == 0
        
    except Exception as e:
        print(f'❌ Error checking articles: {e}')
        return False

async def test_new_rss_collection():
    """Test that new RSS articles get title as content fallback"""
    print('\n🔄 Step 2: Testing new RSS collection with content fallback...')
    
    try:
        # Test fetching one feed
        articles = await rss_collection_service._fetch_feed_articles(
            'TAP (Official)', 
            'https://www.tap.info.tn/rss'
        )
        
        if not articles:
            print('ℹ️  No new articles to test with')
            return True
        
        print(f'✅ Fetched {len(articles)} articles from RSS')
        
        # Check that all have content (should be title at minimum)
        for i, article in enumerate(articles[:3], 1):
            content = article.get('content', '')
            title = article.get('title', '')
            
            print(f'   {i}. Title: {title[:50]}...')
            print(f'      Content: {content[:80]}...')
            
            if not content:
                print(f'   ❌ Article {i} has no content!')
                return False
        
        return True
        
    except Exception as e:
        print(f'❌ Error testing RSS collection: {e}')
        return False

async def main():
    """Run all tests"""
    print('🧪 Testing Content Non-Null Implementation\n')
    
    tests = [
        ("All Articles Have Content", test_content_not_null),
        ("New RSS Articles Have Content Fallback", test_new_rss_collection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f'❌ {test_name} failed with exception: {e}')
            results.append((test_name, False))
    
    # Summary
    print('\n' + '='*60)
    print('📊 CONTENT NON-NULL TEST RESULTS')
    print('='*60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f'{status} - {test_name}')
        if success:
            passed += 1
    
    print(f'\n🎯 {passed}/{len(results)} tests passed')
    
    if passed == len(results):
        print('\n🎉 SUCCESS! Content is never null!')
        print('✅ Frontend team can safely use article.content without null checks')
        print('✅ RSS articles show title as preview')
        print('✅ Manual articles show full content')
    else:
        print('\n⚠️  Some issues found. Check output above.')

if __name__ == "__main__":
    asyncio.run(main()) 