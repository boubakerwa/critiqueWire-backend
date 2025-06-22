#!/usr/bin/env python3

import os
from supabase import create_client, Client
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

def check_images():
    print("🔍 Checking for images in the database...")
    
    # Get all articles
    result = supabase.table("articles").select("id, title, images, thumbnail_url, source_name, url").execute()
    articles = result.data
    
    print(f"\n📊 Total articles: {len(articles)}")
    
    # Count articles with images
    articles_with_images = []
    articles_with_thumbnails = []
    
    for article in articles:
        has_images = article.get('images') and len(article['images']) > 0
        has_thumbnail = article.get('thumbnail_url') is not None
        
        if has_images:
            articles_with_images.append(article)
        
        if has_thumbnail:
            articles_with_thumbnails.append(article)
    
    print(f"🖼️  Articles with images array: {len(articles_with_images)}")
    print(f"🖼️  Articles with thumbnail_url: {len(articles_with_thumbnails)}")
    
    # Show some examples
    if articles_with_images:
        print(f"\n📋 Examples of articles with images:")
        for i, article in enumerate(articles_with_images[:5]):
            print(f"  {i+1}. {article['title'][:60]}...")
            print(f"     Source: {article['source_name']}")
            print(f"     Images: {len(article['images'])} images")
            print(f"     First image: {article['images'][0] if article['images'] else 'None'}")
            print()
    
    if articles_with_thumbnails:
        print(f"\n🖼️  Examples of articles with thumbnails:")
        for i, article in enumerate(articles_with_thumbnails[:5]):
            print(f"  {i+1}. {article['title'][:60]}...")
            print(f"     Source: {article['source_name']}")
            print(f"     Thumbnail: {article['thumbnail_url']}")
            print()
    
    # Check by source
    sources_with_images = {}
    for article in articles:
        source = article['source_name']
        if source not in sources_with_images:
            sources_with_images[source] = {'total': 0, 'with_images': 0, 'with_thumbnails': 0}
        
        sources_with_images[source]['total'] += 1
        
        if article.get('images') and len(article['images']) > 0:
            sources_with_images[source]['with_images'] += 1
        
        if article.get('thumbnail_url'):
            sources_with_images[source]['with_thumbnails'] += 1
    
    print(f"\n📊 Images by source:")
    for source, stats in sources_with_images.items():
        print(f"  {source}:")
        print(f"    Total articles: {stats['total']}")
        print(f"    With images: {stats['with_images']} ({stats['with_images']/stats['total']*100:.1f}%)")
        print(f"    With thumbnails: {stats['with_thumbnails']} ({stats['with_thumbnails']/stats['total']*100:.1f}%)")
        print()

if __name__ == "__main__":
    check_images() 