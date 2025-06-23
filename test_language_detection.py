#!/usr/bin/env python3
"""
Comprehensive test script for language detection functionality in RSS collection.
Tests both RSS metadata extraction and content-based language detection.
"""

import asyncio
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.rss_collection_service import RSSCollectionService

async def test_content_based_detection():
    """Test content-based language detection."""
    print("=== Testing Content-Based Language Detection ===")
    
    service = RSSCollectionService()
    
    test_cases = [
        # Arabic text
        {
            "text": "وزير الصحة التونسي يعلن عن إجراءات جديدة لمكافحة انتشار الفيروس في البلاد",
            "expected": "ar",
            "description": "Arabic news text"
        },
        # French text
        {
            "text": "Le ministre de la Santé tunisien annonce de nouvelles mesures pour lutter contre la propagation du virus dans le pays",
            "expected": "fr", 
            "description": "French news text"
        },
        # English text
        {
            "text": "The Tunisian Health Minister announces new measures to combat the spread of the virus in the country",
            "expected": "en",
            "description": "English news text"
        },
        # Mixed Arabic-French (common in Tunisia)
        {
            "text": "الرئيس التونسي يلتقي بالوزير الأول الفرنسي لمناقشة العلاقات الثنائية والتعاون الاقتصادي",
            "expected": "ar",
            "description": "Arabic text with French influence"
        },
        # Short text (should return unknown)
        {
            "text": "Hi there!",
            "expected": "unknown",
            "description": "Short text"
        },
        # Empty text
        {
            "text": "",
            "expected": "unknown", 
            "description": "Empty text"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {case['description']}")
        print(f"Text: {case['text'][:50]}...")
        
        detected = service._detect_language_from_content(case['text'])
        expected = case['expected']
        
        status = "✅ PASS" if detected == expected else "❌ FAIL"
        print(f"Expected: {expected}, Detected: {detected} - {status}")
    
    print("\nContent-based detection tests completed!")

async def test_rss_metadata_extraction():
    """Test RSS metadata language extraction."""
    print("\n=== Testing RSS Metadata Language Extraction ===")
    
    service = RSSCollectionService()
    
    # Mock RSS feed and entry objects for testing
    class MockFeed:
        def __init__(self, language=None):
            self.feed = MockFeedInfo(language)
    
    class MockFeedInfo:
        def __init__(self, language=None):
            if language:
                self.language = language
    
    class MockEntry:
        def __init__(self, language=None):
            if language:
                self.language = language
    
    test_cases = [
        {
            "feed": MockFeed("ar-TN"),
            "entry": MockEntry(),
            "expected": "ar",
            "description": "Feed-level Arabic language"
        },
        {
            "feed": MockFeed("fr-FR"),
            "entry": MockEntry(),
            "expected": "fr", 
            "description": "Feed-level French language"
        },
        {
            "feed": MockFeed(),
            "entry": MockEntry("en-US"),
            "expected": "en",
            "description": "Entry-level English language"
        },
        {
            "feed": MockFeed(),
            "entry": MockEntry(),
            "expected": None,
            "description": "No language metadata"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {case['description']}")
        
        detected = service._extract_language_from_rss_metadata(case['feed'], case['entry'])
        expected = case['expected']
        
        status = "✅ PASS" if detected == expected else "❌ FAIL"
        print(f"Expected: {expected}, Detected: {detected} - {status}")
    
    print("\nRSS metadata extraction tests completed!")

async def test_language_determination_strategy():
    """Test the overall language determination strategy."""
    print("\n=== Testing Language Determination Strategy ===")
    
    service = RSSCollectionService()
    
    # Mock objects with both metadata and content
    class MockFeed:
        def __init__(self, language=None):
            self.feed = MockFeedInfo(language)
    
    class MockFeedInfo:
        def __init__(self, language=None):
            if language:
                self.language = language
    
    class MockEntry:
        def __init__(self, language=None):
            if language:
                self.language = language
    
    test_cases = [
        {
            "feed": MockFeed("ar-TN"),
            "entry": MockEntry(),
            "title": "الأخبار التونسية اليوم",
            "summary": "آخر الأخبار من تونس والعالم العربي",
            "expected": "ar",
            "description": "RSS metadata (Arabic) + Arabic content - should prefer metadata"
        },
        {
            "feed": MockFeed(),
            "entry": MockEntry(),
            "title": "Actualités tunisiennes aujourd'hui",
            "summary": "Les dernières nouvelles de Tunisie et du monde francophone",
            "expected": "fr",
            "description": "No metadata + French content - should detect from content"
        },
        {
            "feed": MockFeed("fr-FR"),
            "entry": MockEntry(),
            "title": "أخبار تونس",
            "summary": "الأخبار السياسية والاقتصادية",
            "expected": "fr",
            "description": "RSS metadata (French) + Arabic content - should prefer metadata"
        },
        {
            "feed": MockFeed(),
            "entry": MockEntry(),
            "title": "Hi",
            "summary": "Test",
            "expected": "unknown",
            "description": "No metadata + short content - should return unknown"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {case['description']}")
        print(f"Title: {case['title']}")
        print(f"Summary: {case['summary'][:50]}...")
        
        detected = service._determine_article_language(
            case['feed'], 
            case['entry'], 
            case['title'], 
            case['summary']
        )
        expected = case['expected']
        
        status = "✅ PASS" if detected == expected else "❌ FAIL"
        print(f"Expected: {expected}, Detected: {detected} - {status}")
    
    print("\nLanguage determination strategy tests completed!")

async def test_language_mapping():
    """Test language code mapping."""
    print("\n=== Testing Language Code Mapping ===")
    
    service = RSSCollectionService()
    
    # Test the language mapping
    mapping_tests = [
        ("ar", "ar", "Arabic"),
        ("fr", "fr", "French"),
        ("en", "en", "English"),
        ("it", "fr", "Italian -> French fallback"),
        ("es", "fr", "Spanish -> French fallback"),
        ("de", "unknown", "German -> Unknown (not mapped)")
    ]
    
    for input_lang, expected, description in mapping_tests:
        mapped = service.language_mapping.get(input_lang, 'unknown')
        status = "✅ PASS" if mapped == expected else "❌ FAIL"
        print(f"{description}: {input_lang} -> {mapped} - {status}")
    
    print("\nLanguage mapping tests completed!")

async def main():
    """Run all language detection tests."""
    print("🧪 Language Detection Test Suite")
    print("=" * 60)
    
    try:
        # Test content-based detection
        await test_content_based_detection()
        
        # Test RSS metadata extraction
        await test_rss_metadata_extraction()
        
        # Test overall determination strategy
        await test_language_determination_strategy()
        
        # Test language mapping
        await test_language_mapping()
        
        print("\n" + "=" * 60)
        print("🎉 All language detection tests completed!")
        print("\n💡 To test with real RSS feeds, run:")
        print("   python test_rss_collection.py")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 