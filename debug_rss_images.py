#!/usr/bin/env python3

import feedparser
import requests
from bs4 import BeautifulSoup
import json

def debug_rss_images():
    # Test a few RSS feeds
    feeds = {
        "Tekiano": "https://www.tekiano.com/rss",
        "Mosaique FM": "https://www.mosaiquefm.net/rss",
        "Webdo": "https://www.webdo.tn/rss"
    }
    
    for source_name, url in feeds.items():
        print(f"\n{'='*60}")
        print(f"🔍 Debugging RSS feed: {source_name}")
        print(f"📡 URL: {url}")
        print(f"{'='*60}")
        
        try:
            # Fetch RSS feed
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; CritiqueWire/1.0)'}
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch feed: HTTP {response.status_code}")
                continue
            
            # Parse feed
            feed = feedparser.parse(response.text)
            
            if not feed.entries:
                print(f"❌ No entries found in feed")
                continue
            
            print(f"📰 Found {len(feed.entries)} entries")
            
            # Examine first few entries for images
            for i, entry in enumerate(feed.entries[:3]):
                print(f"\n--- Entry {i+1}: {entry.get('title', 'No title')[:50]}... ---")
                
                # Check various image sources
                images_found = []
                
                # 1. Media thumbnail
                if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                    print(f"📸 Media thumbnails: {len(entry.media_thumbnail)}")
                    for thumb in entry.media_thumbnail:
                        if 'url' in thumb:
                            images_found.append(('media_thumbnail', thumb['url']))
                            print(f"   - {thumb['url']}")
                
                # 2. Media content
                if hasattr(entry, 'media_content') and entry.media_content:
                    print(f"📸 Media content: {len(entry.media_content)}")
                    for media in entry.media_content:
                        if 'url' in media:
                            images_found.append(('media_content', media['url']))
                            print(f"   - {media['url']} (type: {media.get('type', 'unknown')})")
                
                # 3. Enclosures
                if hasattr(entry, 'enclosures') and entry.enclosures:
                    print(f"📸 Enclosures: {len(entry.enclosures)}")
                    for enclosure in entry.enclosures:
                        if enclosure.get('type', '').startswith('image'):
                            images_found.append(('enclosure', enclosure.get('href', '')))
                            print(f"   - {enclosure.get('href', '')} (type: {enclosure.get('type', 'unknown')})")
                
                # 4. Images in description HTML
                if hasattr(entry, 'description') and entry.description:
                    try:
                        soup = BeautifulSoup(entry.description, 'html.parser')
                        img_tags = soup.find_all('img')
                        if img_tags:
                            print(f"📸 Images in description HTML: {len(img_tags)}")
                            for img in img_tags:
                                src = img.get('src')
                                if src:
                                    images_found.append(('description_html', src))
                                    print(f"   - {src}")
                        else:
                            print(f"📸 No img tags in description HTML")
                    except Exception as e:
                        print(f"❌ Error parsing description HTML: {e}")
                
                # 5. Check summary for images
                if hasattr(entry, 'summary') and entry.summary:
                    try:
                        soup = BeautifulSoup(entry.summary, 'html.parser')
                        img_tags = soup.find_all('img')
                        if img_tags:
                            print(f"📸 Images in summary HTML: {len(img_tags)}")
                            for img in img_tags:
                                src = img.get('src')
                                if src:
                                    images_found.append(('summary_html', src))
                                    print(f"   - {src}")
                    except Exception as e:
                        print(f"❌ Error parsing summary HTML: {e}")
                
                # Show all available attributes
                print(f"\n🔍 Available entry attributes:")
                for attr in dir(entry):
                    if not attr.startswith('_') and hasattr(entry, attr):
                        value = getattr(entry, attr)
                        if isinstance(value, str) and len(value) > 100:
                            print(f"   {attr}: {type(value).__name__} (length: {len(value)})")
                        elif not callable(value):
                            print(f"   {attr}: {value}")
                
                print(f"\n📊 Total images found for this entry: {len(images_found)}")
                if images_found:
                    for source_type, img_url in images_found:
                        print(f"   - {source_type}: {img_url}")
                else:
                    print("   ❌ No images found")
                
                print(f"\n" + "-"*50)
        
        except Exception as e:
            print(f"❌ Error processing feed {source_name}: {e}")

if __name__ == "__main__":
    debug_rss_images() 