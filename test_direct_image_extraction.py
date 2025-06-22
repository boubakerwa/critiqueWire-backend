#!/usr/bin/env python3

import feedparser
import requests
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.rss_collection_service import RSSCollectionService

def test_direct_extraction():
    print("🧪 Testing direct image extraction...")
    
    # Create RSS service instance
    rss_service = RSSCollectionService()
    
    # Fetch Mosaique FM RSS feed directly
    url = "https://www.mosaiquefm.net/rss"
    
    try:
        print(f"📡 Fetching RSS feed: {url}")
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; CritiqueWire/1.0)'}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch feed: HTTP {response.status_code}")
            return
        
        # Parse feed
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            print(f"❌ No entries found in feed")
            return
        
        print(f"📰 Found {len(feed.entries)} entries")
        
        # Test image extraction on first few entries
        for i, entry in enumerate(feed.entries[:5]):
            print(f"\n--- Entry {i+1}: {entry.get('title', 'No title')[:50]}... ---")
            
            # Test our image extraction function
            images = rss_service._extract_images_from_rss_entry(entry)
            thumbnail = rss_service._extract_thumbnail_from_rss_entry(entry)
            
            print(f"🖼️  Images extracted: {len(images)}")
            for j, img in enumerate(images):
                print(f"   {j+1}. {img}")
            
            print(f"🖼️  Thumbnail: {thumbnail or 'None'}")
            
            # Show raw media_content for debugging
            if hasattr(entry, 'media_content') and entry.media_content:
                print(f"🔍 Raw media_content:")
                for media in entry.media_content:
                    print(f"   - URL: {media.get('url', 'N/A')}")
                    print(f"   - Type: {media.get('type', 'N/A')}")
                    print(f"   - Width: {media.get('width', 'N/A')}")
                    print(f"   - Height: {media.get('height', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_extraction() 