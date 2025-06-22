#!/usr/bin/env python3

import asyncio
import feedparser
import requests
import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.rss_collection_service import RSSCollectionService
from app.services.database_service import database_service

async def backfill_images():
    print("🔄 Backfilling images for existing RSS articles...")
    
    # Create RSS service instance
    rss_service = RSSCollectionService()
    
    # Get all articles without images from sources that might have images
    sources_to_check = ["Mosaique FM"]  # We know this one has images
    
    for source_name in sources_to_check:
        print(f"\n📡 Processing {source_name}...")
        
        # Get articles from this source that don't have images
        articles_result = database_service.supabase.table("articles").select(
            "id, title, url, images, thumbnail_url"
        ).eq("source_name", source_name).execute()
        
        articles = articles_result.data
        articles_without_images = [a for a in articles if not a.get('images') or len(a['images']) == 0]
        
        print(f"📊 Found {len(articles)} total articles, {len(articles_without_images)} without images")
        
        if not articles_without_images:
            print("✅ All articles already have images!")
            continue
        
        # Get the RSS feed URL for this source
        rss_url = rss_service.sources.get(source_name)
        if not rss_url:
            print(f"❌ No RSS URL found for {source_name}")
            continue
        
        try:
            # Fetch current RSS feed
            headers = {'User-Agent': rss_service.user_agent}
            response = requests.get(rss_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch RSS feed: HTTP {response.status_code}")
                continue
            
            # Parse feed
            feed = feedparser.parse(response.text)
            
            if not feed.entries:
                print(f"❌ No entries found in RSS feed")
                continue
            
            print(f"📰 Found {len(feed.entries)} entries in RSS feed")
            
            # Create a mapping of URLs to RSS entries
            rss_entries_by_url = {}
            for entry in feed.entries:
                url = entry.get('link', '')
                if url:
                    rss_entries_by_url[url] = entry
            
            # Update articles with images
            updated_count = 0
            
            for article in articles_without_images:
                article_url = article['url']
                
                # Find matching RSS entry
                if article_url in rss_entries_by_url:
                    rss_entry = rss_entries_by_url[article_url]
                    
                    # Extract images using our fixed function
                    images = rss_service._extract_images_from_rss_entry(rss_entry)
                    thumbnail_url = rss_service._extract_thumbnail_from_rss_entry(rss_entry)
                    
                    if images or thumbnail_url:
                        # Update the article in the database
                        update_data = {}
                        if images:
                            update_data['images'] = images
                        if thumbnail_url:
                            update_data['thumbnail_url'] = thumbnail_url
                        
                        try:
                            database_service.supabase.table("articles").update(update_data).eq("id", article['id']).execute()
                            updated_count += 1
                            
                            print(f"✅ Updated '{article['title'][:50]}...' with {len(images)} images")
                            
                        except Exception as e:
                            print(f"❌ Failed to update article {article['id']}: {e}")
                    else:
                        print(f"⚠️  No images found for '{article['title'][:50]}...'")
                else:
                    print(f"⚠️  RSS entry not found for '{article['title'][:50]}...'")
            
            print(f"✅ Updated {updated_count} articles with images")
            
        except Exception as e:
            print(f"❌ Error processing {source_name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(backfill_images()) 