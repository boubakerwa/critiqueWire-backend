"""
RSS Collection Service for CritiqueWire Backend.
Collects news articles from Tunisian RSS feeds and stores them in the unified articles table.
"""

import asyncio
import aiohttp
import feedparser
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import re

from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

from app.services.database_service import database_service
from app.services.content_extraction_service import ContentExtractionService

# Set seed for consistent language detection results
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

class RSSCollectionService:
    """Service for collecting and managing RSS news feeds."""
    
    def __init__(self):
        self.sources = {
            "TAP": "https://www.tap.info.tn/rss",
            "Business News": "https://www.businessnews.com.tn/feed", 
            "Kapitalis": "https://www.kapitalis.com/rss",
            "Tunisie Numerique": "https://www.tunisienumerique.com/rss",
            "Shems FM": "https://www.shemsfm.net/rss",
            "Mosaique FM": "https://www.mosaiquefm.net/rss",
            "Express FM": "https://www.expressfm.net/rss",
            "Webdo": "https://www.webdo.tn/rss",
            "Tekiano": "https://www.tekiano.com/rss",
            "African Manager": "https://africanmanager.com/rss"
        }
        
        self.content_extractor = ContentExtractionService()
        
        # User agent for RSS requests
        self.user_agent = "Mozilla/5.0 (compatible; CritiqueWire/1.0; +https://critiquewire.com)"
        
        # Language code mapping
        self.language_mapping = {
            'ar': 'ar',    # Arabic
            'fr': 'fr',    # French  
            'en': 'en',    # English
            'it': 'fr',    # Italian -> French (fallback for some mixed content)
            'es': 'fr',    # Spanish -> French (fallback)
        }
    
    def _detect_language_from_content(self, text: str) -> str:
        """Detect language from article content using langdetect."""
        if not text or len(text.strip()) < 20:
            return 'unknown'
        
        try:
            # Clean text for better detection
            clean_text = self._clean_text(text)
            if len(clean_text) < 20:
                return 'unknown'
            
            detected = detect(clean_text)
            return self.language_mapping.get(detected, 'unknown')
        
        except LangDetectException:
            logger.debug(f"Could not detect language from content: {text[:100]}...")
            return 'unknown'
        except Exception as e:
            logger.warning(f"Error in language detection: {e}")
            return 'unknown'
    
    def _extract_language_from_rss_metadata(self, feed, entry) -> Optional[str]:
        """Extract language from RSS feed metadata."""
        # Priority 1: Entry-level language (xml:lang attribute)
        if hasattr(entry, 'language') and entry.language:
            lang_code = entry.language.lower()
            if lang_code.startswith('ar'):
                return 'ar'
            elif lang_code.startswith('fr'):
                return 'fr'
            elif lang_code.startswith('en'):
                return 'en'
        
        # Priority 2: Feed-level language
        if hasattr(feed, 'feed') and hasattr(feed.feed, 'language') and feed.feed.language:
            lang_code = feed.feed.language.lower()
            if lang_code.startswith('ar'):
                return 'ar'
            elif lang_code.startswith('fr'):
                return 'fr'
            elif lang_code.startswith('en'):
                return 'en'
        
        # Priority 3: Check for xml:lang in feed root
        if hasattr(feed, 'feed') and hasattr(feed.feed, 'lang'):
            lang_code = feed.feed.lang.lower()
            if lang_code.startswith('ar'):
                return 'ar'
            elif lang_code.startswith('fr'):
                return 'fr'
            elif lang_code.startswith('en'):
                return 'en'
        
        return None
    
    def _determine_article_language(self, feed, entry, title: str, summary: str) -> str:
        """Determine article language using multiple strategies."""
        # Strategy 1: RSS metadata
        rss_language = self._extract_language_from_rss_metadata(feed, entry)
        if rss_language:
            logger.debug(f"Language from RSS metadata: {rss_language}")
            return rss_language
        
        # Strategy 2: Content-based detection
        # Combine title and summary for better detection
        content_for_detection = f"{title} {summary}".strip()
        if len(content_for_detection) >= 20:
            detected_language = self._detect_language_from_content(content_for_detection)
            if detected_language != 'unknown':
                logger.debug(f"Language detected from content: {detected_language}")
                return detected_language
        
        # Strategy 3: Source-based heuristics (fallback for Tunisian sources)
        # Most Tunisian sources are either Arabic or French
        return 'unknown'
    
    def _generate_content_hash(self, title: str, url: str) -> str:
        """Generate a hash for deduplication."""
        content = f"{title.lower().strip()}{url.strip()}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _format_datetime(self, dt) -> Optional[str]:
        """Format datetime for JSON serialization, handling both datetime objects and strings."""
        if dt is None:
            return None
        if isinstance(dt, str):
            return dt
        if hasattr(dt, 'isoformat'):
            return dt.isoformat()
        return str(dt)
    
    def _extract_main_image_from_rss_entry(self, entry) -> Optional[str]:
        """Extract the main image from RSS entry (single image only)."""
        # Priority 1: media thumbnail
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            for thumb in entry.media_thumbnail:
                if 'url' in thumb:
                    return thumb['url']
        
        # Priority 2: media content
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if 'url' in media:
                    # Accept media content if it's an image type or if type is unknown/empty
                    media_type = media.get('type', '').lower()
                    media_url = media['url']
                    
                    # Check if it's an image by type or by URL extension
                    is_image = (
                        media_type.startswith('image') or
                        media_type == '' or
                        media_type == 'unknown' or
                        any(media_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'])
                    )
                    
                    if is_image:
                        return media_url
        
        # Priority 3: enclosures
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image'):
                    return enclosure.get('href', '')
        
        # Priority 4: images in description HTML
        if hasattr(entry, 'description'):
            import re
            from bs4 import BeautifulSoup
            try:
                soup = BeautifulSoup(entry.description, 'html.parser')
                img_tags = soup.find_all('img')
                for img in img_tags:
                    src = img.get('src')
                    if src and src.startswith('http'):
                        return src
            except:
                pass
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean HTML tags and extra whitespace from text."""
        if not text:
            return ""
        
        # Remove HTML tags
        import re
        text = re.sub(r'<[^>]+>', '', text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats from RSS feeds."""
        if not date_str:
            return None
            
        try:
            # Try feedparser's built-in parsing first
            import time
            parsed_time = feedparser._parse_date(date_str)
            if parsed_time:
                return datetime(*parsed_time[:6], tzinfo=timezone.utc)
        except:
            pass
        
        try:
            # Try python-dateutil as fallback
            from dateutil import parser
            return parser.parse(date_str)
        except:
            pass
        
        return None
    
    async def _fetch_rss_feed(self, source_name: str, url: str, session: aiohttp.ClientSession) -> List[Dict]:
        """Fetch and parse a single RSS feed."""
        articles = []
        
        try:
            logger.info(f"Fetching RSS feed: {source_name}")
            
            headers = {'User-Agent': self.user_agent}
            async with session.get(url, headers=headers, timeout=30) as response:
                if response.status != 200:
                    logger.warning(f"RSS feed {source_name} returned status {response.status}")
                    return articles
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                if not feed.entries:
                    logger.warning(f"No entries found in RSS feed: {source_name}")
                    return articles
                
                logger.info(f"Found {len(feed.entries)} entries in {source_name}")
                
                for entry in feed.entries:
                    try:
                        # Extract basic info
                        title = self._clean_text(entry.get('title', ''))
                        link = entry.get('link', '')
                        summary = self._clean_text(entry.get('summary', ''))
                        author = self._clean_text(entry.get('author', ''))
                        
                        if not title or not link:
                            continue
                        
                        # Parse published date
                        published_at = None
                        if hasattr(entry, 'published'):
                            published_at = self._parse_date(entry.published)
                        
                        # Extract main image
                        image_url = self._extract_main_image_from_rss_entry(entry)
                        
                        # Detect language
                        language = self._determine_article_language(feed, entry, title, summary)
                        
                        # Generate content hash for deduplication
                        content_hash = self._generate_content_hash(title, link)
                        
                        article = {
                            'title': title,
                            'url': link,
                            'summary': summary,
                            'author': author,
                            'published_at': published_at,
                            'source_name': source_name,
                            'source_url': url,
                            'content_hash': content_hash,
                            'image_url': image_url,
                            'language': language,
                            'collected_at': datetime.now(timezone.utc)
                        }
                        
                        articles.append(article)
                        
                    except Exception as e:
                        logger.error(f"Error processing entry from {source_name}: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Error fetching RSS feed {source_name}: {e}")
        
        return articles
    
    async def _store_articles(self, articles: List[Dict]) -> int:
        """Store articles in database, avoiding duplicates."""
        if not articles:
            return 0
        
        stored_count = 0
        
        for article in articles:
            try:
                # Check if article already exists (by content_hash or URL)
                existing = database_service.supabase.table("articles").select("id").or_(
                    f"content_hash.eq.{article['content_hash']},url.eq.{article['url']}"
                ).execute()
                
                if existing.data:
                    logger.debug(f"Article already exists: {article['title'][:50]}...")
                    continue
                
                # Insert new article
                # Use title as content initially (will be extracted on-demand)
                content = f"{article['title']}\n\n(Click to read full article)"
                
                article_data = {
                    "title": article['title'],
                    "content": content,
                    "url": article['url'],
                    "source_name": article['source_name'],
                    "author": article.get('author'),
                    "published_at": self._format_datetime(article.get('published_at')),
                    "summary": article.get('summary'),
                    "source_url": article['source_url'],
                    "collected_at": self._format_datetime(article['collected_at']),
                    "content_hash": article['content_hash'],
                    "image_url": article.get('image_url'),
                    "language": article.get('language', 'unknown'),
                    "analysis_status": 'not_analyzed'
                }
                
                result = database_service.supabase.table("articles").insert(article_data).execute()
                
                if result.data:
                    stored_count += 1
                    logger.debug(f"Stored article: {article['title'][:50]}...")
                
            except Exception as e:
                logger.error(f"Error storing article {article['title'][:50]}...: {e}")
                continue
        
        return stored_count
    
    async def collect_all_feeds(self) -> Dict[str, Any]:
        """Collect articles from all RSS feeds."""
        start_time = datetime.now()
        total_articles_found = 0
        new_articles_stored = 0
        errors = []
        
        logger.info("Starting RSS collection from all feeds...")
        
        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                
                # Create tasks for all RSS feeds
                for source_name, url in self.sources.items():
                    task = self._fetch_rss_feed(source_name, url, session)
                    tasks.append(task)
                
                # Execute all tasks concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                all_articles = []
                for i, result in enumerate(results):
                    source_name = list(self.sources.keys())[i]
                    
                    if isinstance(result, Exception):
                        error_msg = f"Error fetching {source_name}: {result}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                    else:
                        all_articles.extend(result)
                        total_articles_found += len(result)
                
                # Store all articles
                if all_articles:
                    new_articles_stored = await self._store_articles(all_articles)
                
        except Exception as e:
            error_msg = f"Error in RSS collection: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        # Cleanup old RSS articles (older than 30 days)
        try:
            await self._cleanup_old_articles()
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        stats = {
            "timestamp": end_time.isoformat(),
            "feeds_processed": len(self.sources),
            "total_articles_found": total_articles_found,
            "new_articles_stored": new_articles_stored,
            "processing_time": round(processing_time, 2),
            "errors": errors
        }
        
        logger.info(f"RSS collection completed: {new_articles_stored} new articles stored")
        return stats
    
    async def _cleanup_old_articles(self):
        """Remove RSS articles older than 30 days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        result = database_service.supabase.table("articles").delete().not_.is_("collected_at", "null").lt("collected_at", cutoff_date.isoformat()).execute()
        
        if result.data:
            logger.info(f"Cleaned up {len(result.data)} old RSS articles")
    
    async def get_news_feed(self, page: int = 1, limit: int = 20, rss_only: bool = False, 
                           source: Optional[str] = None, search: Optional[str] = None, 
                           language: Optional[str] = None) -> Dict[str, Any]:
        """Get paginated news feed."""
        offset = (page - 1) * limit
        
        # Use Supabase client directly for queries
        try:
            # Build query
            query = database_service.supabase.table("articles").select(
                "id, title, content, url, source_name, author, published_at, "
                "summary, source_url, collected_at, image_url, language, "
                "analysis_status, analysis_id, created_at, updated_at"
            )
            
            # Apply filters
            if rss_only:
                query = query.not_.is_("collected_at", "null")
            
            if source:
                query = query.ilike("source_name", f"%{source}%")
            
            if language:
                query = query.eq("language", language)
            
            if search:
                query = query.or_(f"title.ilike.%{search}%,summary.ilike.%{search}%")
            
            # Get total count with same filters applied
            count_query = database_service.supabase.table("articles").select("*", count="exact")
            
            # Apply same filters to count query
            if rss_only:
                count_query = count_query.not_.is_("collected_at", "null")
            
            if source:
                count_query = count_query.ilike("source_name", f"%{source}%")
            
            if language:
                count_query = count_query.eq("language", language)
            
            if search:
                count_query = count_query.or_(f"title.ilike.%{search}%,summary.ilike.%{search}%")
            
            count_result = count_query.execute()
            total_articles = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
            
            # Get articles with pagination - order by most recent first
            articles_result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            articles = articles_result.data
            
        except Exception as e:
            logger.error(f"Error fetching news feed: {e}")
            articles = []
            total_articles = 0
        
        # Format articles for response
        formatted_articles = []
        for article in articles:
            formatted_article = {
                "id": str(article['id']),
                "title": article['title'],
                "content": article['content'],
                "url": article['url'],
                "source_name": article['source_name'],
                "author": article['author'],
                "published_at": self._format_datetime(article['published_at']),
                "summary": article['summary'],
                "source_url": article['source_url'],
                "collected_at": self._format_datetime(article['collected_at']),
                "image_url": article['image_url'],
                "language": article.get('language', 'unknown'),
                "analysis_status": article['analysis_status'],
                "analysis_id": str(article['analysis_id']) if article['analysis_id'] else None,
                "created_at": self._format_datetime(article['created_at']),
                "updated_at": self._format_datetime(article['updated_at'])
            }
            formatted_articles.append(formatted_article)
        
        # Calculate pagination
        total_pages = (total_articles + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "articles": formatted_articles,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_articles": total_articles,
                "has_next": has_next,
                "has_prev": has_prev,
                "limit": limit
            }
        }
    
    async def extract_article_content(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Extract full content for an RSS article."""
        try:
            # Get article
            result = database_service.supabase.table("articles").select("*").eq("id", article_id).execute()
            
            if not result.data:
                return None
            
            article = result.data[0]
            
            # Extract content using content extraction service
            extraction_result = await self.content_extractor.extract_content(article['url'])
            
            if extraction_result.get('status') == 'success':
                data = extraction_result['data']
                
                # Use the first extracted image if no image exists yet
                new_image_url = None
                if not article.get('image_url') and data.get('images'):
                    new_image_url = data['images'][0]
                
                # Update article with extracted content
                update_data = {
                    "content": data['content'],
                    "word_count": data['wordCount'],
                    "reading_time": data['readingTime'],
                    "content_extracted_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Add image URL if we found one
                if new_image_url:
                    update_data["image_url"] = new_image_url
                
                database_service.supabase.table("articles").update(update_data).eq("id", article_id).execute()
                
                return data
            
        except Exception as e:
            logger.error(f"Error extracting content for article {article_id}: {e}")
        
        return None
    
    def get_available_sources(self) -> List[str]:
        """Get list of available RSS sources."""
        return list(self.sources.keys())

# Create global instance
rss_collection_service = RSSCollectionService() 