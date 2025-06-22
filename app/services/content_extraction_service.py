import asyncio
import aiohttp
import time
import re
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse, urljoin
import logging
from datetime import datetime

# Import extraction libraries
import newspaper
from newspaper import Article
from bs4 import BeautifulSoup
from readability import Document

logger = logging.getLogger(__name__)

class ContentExtractionService:
    """Service for extracting content from URLs using multiple strategies."""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        self.current_user_agent_index = 0
        
    def _get_next_user_agent(self) -> str:
        """Get the next user agent in rotation."""
        user_agent = self.user_agents[self.current_user_agent_index]
        self.current_user_agent_index = (self.current_user_agent_index + 1) % len(self.user_agents)
        return user_agent
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format and protocol."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['http', 'https'] and parsed.netloc
        except Exception:
            return False
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove common ad/navigation indicators
        text = re.sub(r'(Advertisement|ADVERTISEMENT|Click here|Subscribe|Sign up)', '', text, flags=re.IGNORECASE)
        # Clean up unicode characters
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        return text.strip()
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract image URLs from the article."""
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src:
                # Convert relative URLs to absolute
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)
                elif not src.startswith('http'):
                    src = urljoin(base_url, src)
                
                # Filter out small images (likely ads/icons)
                width = img.get('width')
                height = img.get('height')
                if width and height:
                    try:
                        if int(width) < 100 or int(height) < 100:
                            continue
                    except (ValueError, TypeError):
                        pass
                
                images.append(src)
        
        return images[:5]  # Limit to first 5 images
    
    def _calculate_reading_time(self, word_count: int) -> int:
        """Calculate estimated reading time in minutes."""
        # Average reading speed: 200-250 words per minute
        return max(1, round(word_count / 225))
    
    async def _extract_with_newspaper3k(self, url: str, html: str) -> Dict[str, Any]:
        """Extract content using newspaper3k library."""
        try:
            article = Article(url)
            article.set_html(html)
            article.parse()
            
            # Try to parse publish date
            publish_date = None
            if article.publish_date:
                publish_date = article.publish_date.isoformat()
            
            return {
                'title': self._clean_text(article.title),
                'content': self._clean_text(article.text),
                'author': ', '.join(article.authors) if article.authors else None,
                'publishDate': publish_date,
                'description': self._clean_text(article.meta_description),
                'images': article.images[:5] if article.images else [],
                'success': True
            }
        except Exception as e:
            logger.warning(f"Newspaper3k extraction failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _extract_with_readability(self, html: str) -> Dict[str, Any]:
        """Extract content using readability library."""
        try:
            doc = Document(html)
            soup = BeautifulSoup(doc.content(), 'html.parser')
            
            # Clean content
            content = soup.get_text()
            
            return {
                'title': self._clean_text(doc.title()),
                'content': self._clean_text(content),
                'success': True
            }
        except Exception as e:
            logger.warning(f"Readability extraction failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _extract_with_beautifulsoup(self, html: str, url: str) -> Dict[str, Any]:
        """Extract content using BeautifulSoup with custom selectors."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Try to find title
            title = None
            title_selectors = ['h1', 'h2', '.title', '.headline', '[class*="title"]', '[class*="headline"]']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text().strip():
                    title = self._clean_text(title_elem.get_text())
                    break
            
            # Try to find main content
            content = None
            content_selectors = [
                'article', '.article', '.content', '.post', '.entry',
                '[class*="article"]', '[class*="content"]', '[class*="post"]',
                '.story', '[class*="story"]', 'main'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = self._clean_text(content_elem.get_text())
                    if len(content) > 200:  # Ensure we have substantial content
                        break
            
            # Fallback to body content
            if not content or len(content) < 200:
                body = soup.find('body')
                if body:
                    content = self._clean_text(body.get_text())
            
            # Extract author from meta tags or common selectors
            author = None
            author_selectors = [
                'meta[name="author"]', 'meta[property="article:author"]',
                '.author', '.byline', '[class*="author"]', '[class*="byline"]'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    if author_elem.name == 'meta':
                        author = author_elem.get('content')
                    else:
                        author = author_elem.get_text()
                    if author:
                        author = self._clean_text(author)
                        break
            
            # Extract publish date
            publish_date = None
            date_selectors = [
                'meta[property="article:published_time"]',
                'meta[name="publishdate"]',
                'time[datetime]',
                '.date', '.publish-date', '[class*="date"]'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    if date_elem.name == 'meta':
                        publish_date = date_elem.get('content')
                    elif date_elem.name == 'time':
                        publish_date = date_elem.get('datetime') or date_elem.get_text()
                    else:
                        publish_date = date_elem.get_text()
                    
                    if publish_date:
                        publish_date = self._clean_text(publish_date)
                        # Try to parse the date
                        try:
                            from dateutil import parser
                            parsed_date = parser.parse(publish_date)
                            publish_date = parsed_date.isoformat()
                        except:
                            pass  # Keep original string if parsing fails
                        break
            
            # Extract description from meta tags
            description = None
            desc_elem = soup.find('meta', attrs={'name': 'description'}) or \
                       soup.find('meta', attrs={'property': 'og:description'})
            if desc_elem:
                description = self._clean_text(desc_elem.get('content', ''))
            
            # Extract images
            images = self._extract_images(soup, url)
            
            return {
                'title': title,
                'content': content,
                'author': author,
                'publishDate': publish_date,
                'description': description,
                'images': images,
                'success': True
            }
            
        except Exception as e:
            logger.warning(f"BeautifulSoup extraction failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def extract_content(self, url: str) -> Dict[str, Any]:
        """
        Extract content from URL using multiple strategies.
        
        Args:
            url: The URL to extract content from
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        start_time = time.time()
        
        # Validate URL
        if not self._validate_url(url):
            return {
                'status': 'error',
                'error': {
                    'code': 'INVALID_URL',
                    'message': 'Invalid URL format. Please provide a valid HTTP or HTTPS URL.'
                }
            }
        
        # Fetch HTML content with timeout
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            user_agent = self._get_next_user_agent()
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url, allow_redirects=True, max_redirects=3) as response:
                    if response.status != 200:
                        return {
                            'status': 'error',
                            'error': {
                                'code': 'HTTP_ERROR',
                                'message': f'Failed to fetch content. HTTP status: {response.status}'
                            }
                        }
                    
                    html = await response.text()
                    
        except asyncio.TimeoutError:
            return {
                'status': 'error',
                'error': {
                    'code': 'TIMEOUT',
                    'message': 'Request timed out. The website took too long to respond.'
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': {
                    'code': 'FETCH_ERROR',
                    'message': f'Failed to fetch content: {str(e)}'
                }
            }
        
        # Try extraction strategies in order of preference
        strategies = [
            ('newspaper3k', self._extract_with_newspaper3k),
            ('readability', self._extract_with_readability),
            ('beautifulsoup', self._extract_with_beautifulsoup)
        ]
        
        best_result = None
        best_score = 0
        
        for strategy_name, strategy_func in strategies:
            try:
                if strategy_name == 'newspaper3k':
                    result = await strategy_func(url, html)
                elif strategy_name == 'readability':
                    result = await strategy_func(html)
                else:  # beautifulsoup
                    result = await strategy_func(html, url)
                
                if result.get('success'):
                    # Score the result based on content quality
                    content_length = len(result.get('content', ''))
                    has_title = bool(result.get('title'))
                    has_author = bool(result.get('author'))
                    has_date = bool(result.get('publishDate'))
                    
                    score = content_length
                    if has_title: score += 100
                    if has_author: score += 50
                    if has_date: score += 50
                    
                    if score > best_score:
                        best_score = score
                        best_result = result
                        best_result['extractionStrategy'] = strategy_name
                        
            except Exception as e:
                logger.warning(f"Strategy {strategy_name} failed: {e}")
                continue
        
        if not best_result or best_score == 0:
            return {
                'status': 'error',
                'error': {
                    'code': 'EXTRACTION_FAILED',
                    'message': 'Unable to extract readable content from the provided URL. The page may be behind a paywall, require JavaScript, or have an unsupported format.'
                }
            }
        
        # Calculate additional metrics
        content = best_result.get('content', '')
        word_count = len(content.split()) if content else 0
        reading_time = self._calculate_reading_time(word_count)
        
        processing_time = time.time() - start_time
        
        # Build final response
        return {
            'status': 'success',
            'data': {
                'title': best_result.get('title') or 'Untitled',
                'content': content,
                'author': best_result.get('author'),
                'publishDate': best_result.get('publishDate'),
                'images': best_result.get('images', []),
                'description': best_result.get('description'),
                'wordCount': word_count,
                'readingTime': reading_time,
                'extractionStrategy': best_result.get('extractionStrategy'),
                'processingTime': round(processing_time, 2)
            }
        }

# Create global instance
content_extraction_service = ContentExtractionService() 