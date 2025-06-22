# User Stories - Next Development Phase

## **Epic 1: URL Content Extraction System** 🔗

### **User Story 1.1: Basic URL Content Extraction**

**As a** user analyzing news articles  
**I want to** submit a URL and automatically extract the article content  
**So that** I don't have to manually copy/paste article text  

#### **Acceptance Criteria:**
- [ ] User can submit any news article URL via API
- [ ] System extracts title, content, author, publish date, and images
- [ ] System handles common news website formats (CNN, BBC, local news sites)
- [ ] System returns clean, readable text without ads or navigation
- [ ] System provides meaningful error messages for inaccessible URLs
- [ ] Extraction completes within 10 seconds for typical articles
- [ ] System handles both HTTP and HTTPS URLs

#### **Technical Requirements:**
- [ ] Implement multiple extraction strategies (newspaper3k, BeautifulSoup, Readability)
- [ ] Add content cleaning and normalization
- [ ] Handle different character encodings (UTF-8, Latin-1, etc.)
- [ ] Extract metadata (author, publish date, description)
- [ ] Implement timeout handling (10-second limit)
- [ ] Add user-agent rotation to avoid blocking

#### **API Specification:**
```python
POST /v1/content/extract
{
    "url": "https://example.com/article"
}

Response:
{
    "status": "success",
    "data": {
        "title": "Article Title",
        "content": "Full article text...",
        "author": "John Doe",
        "publishDate": "2024-06-22T10:30:00Z",
        "images": ["https://example.com/image1.jpg"],
        "description": "Article summary",
        "wordCount": 1250,
        "readingTime": 5
    }
}
```

#### **Testing Scenarios:**

##### **Happy Path Tests:**
1. **Test mainstream news sites:**
   - Submit CNN article URL → Should extract title, content, author, date
   - Submit BBC article URL → Should handle different HTML structure
   - Submit local news URL → Should work with smaller publications

2. **Test different content types:**
   - Long-form article (2000+ words) → Should extract completely
   - Short news brief (200 words) → Should extract properly
   - Article with images → Should capture image URLs
   - Article with video embeds → Should handle gracefully

##### **Edge Case Tests:**
3. **Test error handling:**
   - Invalid URL format → Should return 400 with clear error
   - Non-existent URL (404) → Should return appropriate error
   - Paywalled content → Should extract what's available or return meaningful error
   - Non-article URLs (homepage, search page) → Should detect and handle

4. **Test performance:**
   - Very long articles (5000+ words) → Should complete within timeout
   - Slow-loading websites → Should handle timeouts gracefully
   - Multiple simultaneous requests → Should handle concurrency

##### **Security Tests:**
5. **Test malicious inputs:**
   - Malformed URLs → Should validate and reject safely
   - URLs with redirects → Should follow safely (max 3 redirects)
   - Non-HTTP protocols → Should reject appropriately

#### **Manual Testing Checklist:**
- [ ] Test with 10 different Tunisian news websites
- [ ] Test with international news sites (CNN, BBC, Reuters)
- [ ] Test with various article lengths (short, medium, long)
- [ ] Test error scenarios (404, timeout, paywall)
- [ ] Verify extracted content quality and completeness
- [ ] Check that images and metadata are captured correctly

---

### **User Story 1.2: Enhanced Analysis with URL Support**

**As a** user wanting to analyze news articles  
**I want to** submit URLs directly to the analysis endpoint  
**So that** I can analyze articles without manual content extraction  

#### **Acceptance Criteria:**
- [ ] Existing analysis endpoints accept URLs in addition to text content
- [ ] URL content is automatically extracted before analysis
- [ ] Analysis results include source URL and metadata
- [ ] System validates URLs before processing
- [ ] Analysis works with both sync and async modes
- [ ] Error handling preserves existing behavior for text-only analysis

#### **API Enhancement:**
```python
POST /v1/analyses
{
    "url": "https://example.com/article",  # NEW: URL support
    "title": "Optional title override",
    "preset": "political",
    "options": {
        "includeBiasAnalysis": true,
        "includeSentimentAnalysis": true,
        "includeFactCheck": true
    },
    "async": true
}
```

#### **Testing Scenarios:**
1. **URL Analysis Tests:**
   - Submit URL for bias analysis → Should extract content and analyze
   - Submit URL for comprehensive analysis → Should include source credibility
   - Submit URL with custom title → Should use provided title over extracted

2. **Backward Compatibility:**
   - Existing text-based analysis → Should continue working unchanged
   - Mix of URL and text submissions → Should handle both properly

---

## **Epic 2: RSS News Collection System** 📰

### **User Story 2.1: Tunisian News Feed Collection**

**As a** user interested in Tunisian news  
**I want to** see automatically collected news from multiple Tunisian sources  
**So that** I have a centralized view of the latest news without visiting multiple websites  

#### **Acceptance Criteria:**
- [ ] System automatically collects news from 5-10 Tunisian RSS feeds
- [ ] News collection runs every 10-15 minutes
- [ ] Duplicate articles are detected and consolidated
- [ ] Articles are stored with source attribution
- [ ] System handles RSS feed failures gracefully
- [ ] Collection includes article images when available

#### **Technical Requirements:**
- [ ] Implement RSS feed parser using feedparser library
- [ ] Create scheduled background job (Celery or simple cron)
- [ ] Add article deduplication logic (title similarity)
- [ ] Store articles in database with proper indexing
- [ ] Handle RSS feed variations and errors
- [ ] Extract and store article images/thumbnails

#### **RSS Sources to Implement:**
```python
tunisia_rss_feeds = {
    "TAP (Official)": "https://www.tap.info.tn/rss",
    "Business News": "https://www.businessnews.com.tn/feed",
    "Kapitalis": "https://www.kapitalis.com/rss",
    "Tunisie Numerique": "https://www.tunisienumerique.com/rss",
    "Shems FM": "https://www.shemsfm.net/rss",
    "Mosaique FM": "https://www.mosaiquefm.net/rss",
    "Express FM": "https://www.expressfm.net/rss"
}
```

#### **Database Schema:**
```sql
CREATE TABLE collected_articles (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    url TEXT UNIQUE NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    author TEXT,
    published_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW(),
    thumbnail_url TEXT,
    images JSONB,
    analysis_id UUID REFERENCES analyses(id),
    analysis_status TEXT DEFAULT 'not_analyzed'
);
```

#### **Testing Scenarios:**

##### **RSS Collection Tests:**
1. **Test feed parsing:**
   - Parse valid RSS feed → Should extract all articles
   - Parse feed with missing fields → Should handle gracefully
   - Parse feed with encoding issues → Should handle character sets

2. **Test deduplication:**
   - Same article from multiple sources → Should consolidate
   - Similar titles with different wording → Should detect similarity
   - Completely different articles → Should store separately

3. **Test error handling:**
   - RSS feed returns 404 → Should log error and continue with other feeds
   - RSS feed timeout → Should handle gracefully
   - Malformed RSS XML → Should skip and continue

##### **Background Job Tests:**
4. **Test scheduling:**
   - Job runs every 15 minutes → Verify timing
   - Job handles overlapping runs → Should prevent concurrent execution
   - Job failure → Should retry and log errors

#### **Manual Testing Checklist:**
- [ ] Verify each RSS feed URL is accessible and returns valid XML
- [ ] Check that articles are being collected and stored properly
- [ ] Confirm deduplication is working (submit same article twice)
- [ ] Test background job scheduling and execution
- [ ] Verify images and metadata are being captured

---

### **User Story 2.2: News Feed Display and Browsing**

**As a** user browsing collected news  
**I want to** see a clean, organized feed of recent Tunisian news  
**So that** I can quickly scan headlines and choose articles to read or analyze  

#### **Acceptance Criteria:**
- [ ] Display paginated list of collected articles
- [ ] Show article title, summary, source, and publish date
- [ ] Include thumbnail images when available
- [ ] Allow filtering by source and date range
- [ ] Provide search functionality across articles
- [ ] Show "Analyze" button for each article
- [ ] Display analysis status (not analyzed, pending, completed)

#### **API Specification:**
```python
GET /v1/news-feed?page=1&limit=20&source=tap&search=economy&date_from=2024-06-01

Response:
{
    "status": "success",
    "data": {
        "articles": [
            {
                "id": "article-123",
                "title": "Tunisia Economic Reforms Progress",
                "summary": "Government announces new measures...",
                "url": "https://tap.info.tn/article/123",
                "source": "TAP",
                "publishedAt": "2024-06-22T10:30:00Z",
                "thumbnailUrl": "https://tap.info.tn/thumb.jpg",
                "analysisStatus": "completed",
                "analysisId": "analysis-456"
            }
        ],
        "pagination": {
            "currentPage": 1,
            "totalPages": 15,
            "totalArticles": 300,
            "hasNext": true
        }
    }
}
```

#### **Testing Scenarios:**
1. **Display Tests:**
   - Load news feed → Should show recent articles with metadata
   - Test pagination → Should navigate through pages correctly
   - Test empty state → Should handle gracefully when no articles

2. **Filtering Tests:**
   - Filter by source → Should show only articles from selected source
   - Filter by date range → Should respect date boundaries
   - Search by keyword → Should find relevant articles

---

### **User Story 2.3: On-Demand Article Analysis**

**As a** user viewing collected news articles  
**I want to** request analysis for any article with one click  
**So that** I can get bias and sentiment insights without leaving the news feed  

#### **Acceptance Criteria:**
- [ ] Each article shows "Analyze" button when not yet analyzed
- [ ] Clicking analyze starts async analysis process
- [ ] Analysis status updates in real-time (pending → completed)
- [ ] Once analyzed, results are visible to all users
- [ ] Analysis results are cached to avoid duplicate processing
- [ ] Analysis includes all standard features (bias, sentiment, claims, fact-check)

#### **API Specification:**
```python
POST /v1/articles/{article_id}/analyze
{
    "preset": "political",
    "options": {
        "includeBiasAnalysis": true,
        "includeSentimentAnalysis": true,
        "includeFactCheck": true,
        "includeClaimExtraction": true
    }
}

Response:
{
    "status": "success",
    "data": {
        "analysisId": "analysis-789",
        "status": "pending",
        "estimatedCompletionTime": "2024-06-22T10:35:00Z"
    }
}
```

#### **Testing Scenarios:**
1. **Analysis Request Tests:**
   - Click analyze on unanalyzed article → Should start analysis
   - Click analyze on already analyzed article → Should show existing results
   - Multiple users analyze same article → Should share results

2. **Status Update Tests:**
   - Analysis starts → Status should change to "pending"
   - Analysis completes → Status should change to "completed"
   - Analysis fails → Status should change to "failed" with error message

---

## **Epic 3: Integration and Polish** ✨

### **User Story 3.1: Unified Content Processing**

**As a** developer maintaining the system  
**I want** URL extraction to work seamlessly with RSS collection  
**So that** both manual URL submissions and RSS articles use the same processing pipeline  

#### **Acceptance Criteria:**
- [ ] RSS articles use URL extraction for full content
- [ ] Manual URL submissions and RSS articles have consistent data format
- [ ] Error handling is consistent across both flows
- [ ] Performance is optimized for batch processing (RSS) and single requests (manual)

#### **Testing Scenarios:**
1. **Integration Tests:**
   - RSS article processing → Should use URL extraction internally
   - Manual URL analysis → Should produce same format as RSS articles
   - Batch vs single processing → Should maintain consistency

---

## **Testing Strategy Overview** 🧪

### **Unit Tests:**
- [ ] URL extraction functions with various HTML structures
- [ ] RSS parsing with different feed formats
- [ ] Deduplication algorithms with edge cases
- [ ] Content cleaning and normalization

### **Integration Tests:**
- [ ] End-to-end URL analysis workflow
- [ ] RSS collection to analysis pipeline
- [ ] Database operations and data integrity
- [ ] API endpoint functionality

### **Performance Tests:**
- [ ] URL extraction speed (target: <10 seconds)
- [ ] RSS collection efficiency (target: process 100 articles in <5 minutes)
- [ ] Concurrent analysis handling
- [ ] Database query performance

### **User Acceptance Tests:**
- [ ] Real Tunisian news websites compatibility
- [ ] User workflow from news feed to analysis results
- [ ] Error handling and user feedback
- [ ] Mobile and desktop browser compatibility

---

## **Definition of Done** ✅

### **For URL Content Extraction:**
- [ ] Code implemented and tested
- [ ] API endpoints documented
- [ ] Unit tests with >80% coverage
- [ ] Integration tests passing
- [ ] Manual testing completed with 10+ news sites
- [ ] Error handling tested and documented
- [ ] Performance benchmarks met

### **For RSS News Collection:**
- [ ] Background job implemented and scheduled
- [ ] Database schema created and migrated
- [ ] RSS feeds configured and tested
- [ ] Deduplication working correctly
- [ ] News feed API implemented
- [ ] Frontend integration ready
- [ ] Monitoring and logging in place

### **For On-Demand Analysis:**
- [ ] Analysis request API implemented
- [ ] Status tracking working
- [ ] Result caching implemented
- [ ] Integration with existing analysis pipeline
- [ ] User interface updated
- [ ] Cost optimization verified

---

## **Estimated Timeline** 📅

### **Week 1: URL Content Extraction**
- Days 1-2: Core extraction implementation
- Days 3-4: Error handling and edge cases
- Days 5-7: Testing and refinement

### **Week 2: RSS Collection Backend**
- Days 1-3: RSS parsing and background jobs
- Days 4-5: Database integration and deduplication
- Days 6-7: Testing and optimization

### **Week 3: News Feed API and Frontend**
- Days 1-3: News feed API implementation
- Days 4-5: On-demand analysis integration
- Days 6-7: Frontend updates and testing

### **Week 4: Integration and Polish**
- Days 1-2: End-to-end testing
- Days 3-4: Performance optimization
- Days 5-7: Documentation and deployment preparation

---

## **Success Metrics** 📊

### **Technical Metrics:**
- URL extraction success rate: >95%
- RSS collection reliability: >99% uptime
- Analysis request response time: <2 seconds
- Background job completion rate: >98%

### **User Experience Metrics:**
- News feed load time: <3 seconds
- Analysis completion time: <60 seconds
- User error rate: <5%
- Feature adoption rate: >70% of users try news feed

### **Business Metrics:**
- Daily active users viewing news feed
- Analysis requests per article
- User retention after news feed launch
- Cost per analysis (target: <$0.20) 