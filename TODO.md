# Todo List

-   [x] ~~**Initial Project Setup & Dockerization**~~
-   [x] ~~**Implement & Debug Authentication**~~
    -   [x] ~~Setup Pydantic `Settings` in `app/core/config.py`.~~
    -   [x] ~~Create `.env.example` file.~~
    -   [x] ~~Define Pydantic schemas in `app/api/v1/schemas.py`.~~
    -   [x] ~~Create placeholder OpenAI service and API endpoints.~~
    -   [x] ~~Implement dependency to validate Supabase JWTs.~~
    -   [x] ~~Debug and fix `401 Unauthorized` errors by switching to `supabase-py` validation.~~
    -   [x] ~~Clean up debug code from endpoints and schemas.~~
-   [x] ~~**Refine OpenAI Service:**~~
    -   [x] ~~Implement actual OpenAI calls for each analysis type.~~
    -   [x] ~~Use OpenAI's JSON mode for reliable output.~~
-   [x] ~~**Implement Core OpenAI Service**~~
-   [x] ~~**Implement Frontend API Refinements (v0.1)**~~
    -   [x] ~~Implement strongly-typed analysis result schemas.~~
    -   [x] ~~Add placeholder endpoints for user profile, bookmarks, and analysis history.~~
    -   [x] ~~Add comprehensive error documentation to OpenAPI spec.~~

## **✅ COMPLETED: Phase 1 - Core Journalist Features (v0.2)**
-   [x] ~~**Comprehensive Analysis System:**~~
    -   [x] ~~Create comprehensive analysis schemas (BiasAnalysisResult, SentimentAnalysisResult, ExtractedClaim, etc.)~~
    -   [x] ~~Implement unified `/v1/analyses/comprehensive` endpoint (supports both URL and text)~~
    -   [x] ~~Add analysis presets system (general, political, financial, scientific, opinion)~~
    -   [x] ~~Enhance AnalysisResultsData with articleId and analysisType fields~~
    -   [x] ~~Update OpenAI service to support comprehensive analysis with presets~~
-   [x] ~~**Source Credibility Assessment:**~~
    -   [x] ~~Create `/v1/source-credibility` endpoint with SourceCredibilityResult schema~~
    -   [x] ~~Implement credibility scoring system (transparency, accuracy, bias, ownership, expertise)~~
    -   [x] ~~Add credibility assessment to comprehensive analysis when analyzing URLs~~
-   [x] ~~**Enhanced Analysis History:**~~
    -   [x] ~~Upgrade `/v1/analyses` endpoint with search, filtering, and pagination~~
    -   [x] ~~Add PaginatedAnalysisHistoryResponse and AnalysisHistoryItem schemas~~
    -   [x] ~~Support filtering by preset, analysis_type, date range, and search terms~~
    -   [x] ~~Implement cursor-based pagination for efficient large dataset handling~~

## **✅ COMPLETED: Phase 2 - Professional Features (v0.2)**
-   [x] ~~**Export & Share Functionality:**~~
    -   [x] ~~Create `/v1/analyses/{analysis_id}/export` endpoint~~
    -   [x] ~~Implement PDF, DOCX, HTML, JSON, CSV export formats~~
    -   [x] ~~Add report templates (professional, academic, executive, detailed)~~
    -   [x] ~~Create `/v1/analyses/{analysis_id}/share` endpoint with secure link generation~~
    -   [x] ~~Implement share permissions and expiration handling~~
-   [x] ~~**Analysis Presets Management:**~~
    -   [x] ~~Create `/v1/analysis-presets` GET endpoint for retrieving available presets~~
    -   [x] ~~Create `/v1/analysis-presets` POST endpoint for custom preset creation~~
    -   [x] ~~Add AnalysisPreset and CreatePresetRequest schemas~~
    -   [x] ~~Support organization-level custom presets~~

## **✅ COMPLETED: OpenAPI v0.3 User Stories**
-   [x] ~~**Unified Analysis Endpoint (v0.3 #1):**~~
    -   [x] ~~Create single `POST /v1/analyses` endpoint for all analysis types~~
    -   [x] ~~Support both URL and text content analysis~~
    -   [x] ~~Configurable analysis options and presets~~
-   [x] ~~**Consistent Analysis Response Model (v0.3 #2):**~~
    -   [x] ~~All endpoints return same `AnalysisResultsResponse` structure~~
    -   [x] ~~Unified schema with optional results for async mode~~
    -   [x] ~~Consistent metadata and status fields~~
-   [x] ~~**Asynchronous by Default (v0.3 #3):**~~
    -   [x] ~~`async_mode: true` is the default~~
    -   [x] ~~Returns immediate task ID with `status: "pending"`~~
    -   [x] ~~Sync mode available when `async_mode: false`~~
-   [x] ~~**Consistent API Naming Conventions (v0.3 #4):**~~
    -   [x] ~~All properties use `camelCase` consistently~~
    -   [x] ~~No more mixed naming like `analysisId` vs `next_cursor`~~
-   [x] ~~**Clear and Unambiguous Naming (v0.3 #5):**~~
    -   [x] ~~Removed confusing "Legacy" prefixes~~
    -   [x] ~~Clear, descriptive endpoint names~~
    -   [x] ~~Self-documenting schema names~~

## **✅ COMPLETED: OpenAPI v0.4 User Stories**
-   [x] ~~**Unified Analysis Endpoint (v0.4 #1):**~~
    -   [x] ~~Create single `POST /v1/analyses` endpoint for all analysis types~~
    -   [x] ~~Support both URL and text content analysis~~
    -   [x] ~~Configurable analysis options and presets~~
-   [x] ~~**Consistent Analysis Response Model (v0.4 #2):**~~
    -   [x] ~~All endpoints return same `AnalysisResultsResponse` structure~~
    -   [x] ~~Unified schema with optional results for async mode~~
    -   [x] ~~Consistent metadata and status fields~~
-   [x] ~~**Asynchronous by Default (v0.4 #3):**~~
    -   [x] ~~`async_mode: true` is the default~~
    -   [x] ~~Returns immediate task ID with `status: "pending"`~~
    -   [x] ~~Sync mode available when `async_mode: false`~~
-   [x] ~~**Consistent API Naming Conventions (v0.4 #4):**~~
    -   [x] ~~All properties use `camelCase` consistently~~
    -   [x] ~~No more mixed naming like `analysisId` vs `next_cursor`~~
-   [x] ~~**Clear and Unambiguous Naming (v0.4 #5):**~~
    -   [x] ~~Removed confusing "Legacy" prefixes~~
    -   [x] ~~Clear, descriptive endpoint names~~
    -   [x] ~~Self-documenting schema names~~
-   [x] ~~**Unified Fact-Check Result Models (v0.4 #6):**~~
    -   [x] ~~Implement unified fact-check result models~~
-   [x] ~~**Added `GET /v1/analyses/{analysis_id}` Endpoint (v0.4 #7):**~~
    -   [x] ~~Add `GET /v1/analyses/{analysis_id}` endpoint for new unified format~~
-   [x] ~~**Consolidated Redundant Endpoints (v0.4 #8):**~~
    -   [x] ~~Consolidate redundant endpoints (kept legacy for backward compatibility)~~

## **✅ COMPLETED: Background Processing & Error Handling (v0.5)**
-   [x] ~~**Async Background Processing:**~~
    -   [x] ~~Fixed validation errors in analysis response formatting~~
    -   [x] ~~Implemented proper background task processing with asyncio~~
    -   [x] ~~Added manual trigger endpoint for testing background processing~~
    -   [x] ~~Fixed JSON serialization issues with Pydantic models~~
    -   [x] ~~Switched from GPT-4o-mini to GPT-4o for better reliability~~
    -   [x] ~~Enhanced JWT authentication for background processing~~
    -   [x] ~~Fixed asyncio import issues in production environment~~
-   [x] ~~**Database Content Storage:**~~
    -   [x] ~~Added full content storage to analyses table (not just preview)~~
    -   [x] ~~Fixed background processing to retrieve full content from database~~
    -   [x] ~~Enhanced content retrieval methods for background processing~~
-   [x] ~~**Production Error Handling:**~~
    -   [x] ~~Added comprehensive OpenAI error logging and handling~~
    -   [x] ~~Enhanced error tracking with detailed tracebacks~~
    -   [x] ~~Added OpenAI connectivity validation in health checks~~
    -   [x] ~~Resolved OpenAI API key configuration issues~~
-   [x] ~~**Honest Failure Reporting:**~~
    -   [x] ~~Removed fallback mechanisms that returned generic "Analysis completed successfully" messages~~
    -   [x] ~~Background processing now properly fails with "failed" status when OpenAI calls fail~~
    -   [x] ~~Sync endpoints return HTTP 500 errors when OpenAI services are unavailable~~
    -   [x] ~~Enhanced result validation to detect and handle OpenAI failures~~
    -   [x] ~~Filtered out failed fact-check results to avoid null entries~~

## **✅ Completed Features**

### v0.2 - Comprehensive Analysis System ✅
- [x] Comprehensive analysis endpoint with configurable presets
- [x] Source credibility assessment
- [x] Analysis history with filtering and pagination
- [x] Export and share functionality
- [x] Analysis presets management (built-in and custom)

### v0.3 - Unified Async Analysis ✅
- [x] Unified analysis endpoint (`POST /v1/analyses`) with async/sync modes
- [x] Async-first approach with background processing capability
- [x] Backward compatibility with legacy endpoints
- [x] Enhanced response models for async operations

### v0.4 - API Consistency & Standardization ✅
- [x] Standardized API naming convention (camelCase throughout)
- [x] Removed ambiguous "Legacy" naming from models
- [x] Unified fact-check result models
- [x] Added `GET /v1/analyses/{analysis_id}` endpoint for new unified format
- [x] Consolidated redundant endpoints (kept legacy for backward compatibility)

### v0.5 - Database Integration & Persistence ✅
- [x] Supabase database integration with PostgreSQL
- [x] Analysis storage and retrieval functionality
- [x] User-specific analysis history with filtering and pagination
- [x] Background task processing for async analyses
- [x] Real-time status updates via database polling
- [x] Row Level Security (RLS) for data protection
- [x] Production-ready background processing with proper error handling
- [x] Honest failure reporting (no more misleading "completed" status with generic results)

## 🔄 Current Priorities

### High Priority
1. **URL Content Extraction** ⭐
   - Implement robust web scraping with fallbacks
   - Content cleaning and normalization
   - Metadata extraction (author, date, etc.)
   - Error handling for inaccessible URLs

2. **Production Background Task System**
   - Replace simple background service with Celery/Redis
   - Task queue management and monitoring
   - Retry logic for failed analyses
   - Task cancellation and cleanup

3. **Real-time Status Updates**
   - WebSocket implementation for live progress
   - Analysis status notifications
   - Real-time collaboration features

4. **🆕 Automated News Collection & Display System** ⭐⭐⭐
   - **News Collection Pipeline (Phase 1)**
     - [ ] RSS feed integration for Tunisian news sources (no registration required)
     - [ ] News API integrations as backup (Google News, NewsAPI, etc.)
     - [ ] Scheduled background job (every 10-15 minutes)
     - [ ] Content extraction and normalization from RSS feeds
     - [ ] Media extraction (thumbnails, images, videos from RSS)
   - **Content Storage & Display**
     - [ ] Article storage with metadata (headline, summary, source, timestamp)
     - [ ] Media storage and optimization (images, thumbnails)
     - [ ] Duplicate article detection and consolidation
     - [ ] Public news feed display (like a news aggregator)
     - [ ] Source attribution and credibility indicators
   - **On-Demand Analysis System**
     - [ ] "Analyze" button for each article
     - [ ] Async analysis execution only when user requests
     - [ ] Analysis result caching - once analyzed, show to all users
     - [ ] Analysis status tracking (pending/completed/failed)
     - [ ] Cost optimization through smart caching
   - **User Experience Features**
     - [ ] News feed browsing and filtering
     - [ ] Search functionality across collected articles
     - [ ] Source filtering and preferences
     - [ ] Analysis history and popular analyses
     - [ ] Trending articles and most-analyzed content

## 🚀 FUTURE: LangGraph Integration Planning

### **Phase 1: LangGraph Foundation (v0.6)** 🎯
- [ ] **Research & Architecture Planning**
  - [ ] Evaluate LangGraph vs LangChain for our use case
  - [ ] Design agent-based workflow architecture
  - [ ] Plan migration strategy from direct OpenAI calls
  - [ ] Define agent interaction patterns
  - [ ] **🆕 Design news monitoring agent workflow architecture**

- [ ] **Core LangGraph Setup**
  - [ ] Install and configure LangGraph dependencies
  - [ ] Create base agent framework and workflow engine
  - [ ] Implement state management for multi-step workflows
  - [ ] Set up workflow visualization and debugging tools

- [ ] **Basic Agent Implementation**
  - [ ] Convert existing analysis tasks to LangGraph agents
  - [ ] Create Content Analysis Agent (bias, sentiment, claims)
  - [ ] Create Fact-Check Agent with external API integration
  - [ ] Implement agent coordination and handoff mechanisms
  - [ ] **🆕 Create News Monitoring Agent (RSS feeds, APIs, scraping)**
  - [ ] **🆕 Create Deduplication Agent (headline similarity, content matching)**

### **Phase 2: Advanced Agent Workflows (v0.7)** 🤖
- [ ] **Multi-Agent Analysis Pipeline**
  - [ ] Investigative Research Agent (find related articles, cross-reference sources)
  - [ ] Source Verification Agent (author credibility, publication history)
  - [ ] Editorial Workflow Agent (flagging, approval processes)
  - [ ] Quality Assurance Agent (result validation, confidence scoring)
  - [ ] **🆕 News Aggregation Agent (multi-source collection and coordination)**
  - [ ] **🆕 Trend Analysis Agent (pattern detection across time and sources)**

- [ ] **Action-Based Agents**
  - [ ] Notification Agent (email, SMS, webhooks)
  - [ ] Archive Agent (knowledge base storage, indexing)
  - [ ] Report Generation Agent (automated summaries, alerts)
  - [ ] User Engagement Agent (personalized recommendations)
  - [ ] **🆕 Breaking News Alert Agent (urgent story detection and notification)**
  - [ ] **🆕 Source Monitoring Agent (new source discovery and validation)**

- [ ] **Workflow Orchestration**
  - [ ] Conditional routing based on content type and analysis results
  - [ ] Parallel vs sequential agent execution optimization
  - [ ] Error handling and agent fallback strategies
  - [ ] Human-in-the-loop integration points
  - [ ] **🆕 Automated news pipeline orchestration (monitoring → analysis → storage → alerts)**

### **Phase 3: Intelligent Agent Features (v0.8)** 🧠
- [ ] **Adaptive Workflows**
  - [ ] Content-aware agent selection (news vs opinion vs research papers)
  - [ ] Dynamic analysis depth based on bias/credibility scores
  - [ ] User preference learning and workflow customization
  - [ ] Historical pattern recognition and proactive analysis
  - [ ] **🆕 Geographic and topic-based monitoring customization**
  - [ ] **🆕 Source reliability learning and adaptive monitoring frequency**

- [ ] **Cross-Analysis Intelligence**
  - [ ] Source reputation tracking across analyses
  - [ ] Pattern detection in bias trends
  - [ ] Automated alert systems for significant findings
  - [ ] Knowledge graph building from analysis results
  - [ ] **🆕 Cross-source story correlation and bias comparison**
  - [ ] **🆕 Temporal bias trend analysis and prediction**

- [ ] **Multi-Model Integration**
  - [ ] Model specialization per agent (Claude for bias, GPT for claims, etc.)
  - [ ] Cost optimization through intelligent model selection
  - [ ] Fallback chains for reliability (GPT-4 → GPT-3.5 → Claude)
  - [ ] Performance monitoring and model effectiveness tracking
  - [ ] **🆕 News-specific model optimization (headline analysis, source credibility)**

### **Phase 4: Production Agent System (v0.9)** 🏭
- [ ] **Scalability & Performance**
  - [ ] Agent load balancing and resource management
  - [ ] Workflow caching and result reuse
  - [ ] Agent performance monitoring and optimization
  - [ ] Horizontal scaling for high-volume analysis
  - [ ] **🆕 High-frequency news monitoring with efficient resource usage**
  - [ ] **🆕 Real-time processing for breaking news scenarios**

- [ ] **Advanced Integration**
  - [ ] External API integrations (fact-check databases, news APIs)
  - [ ] Real-time data feeds and live analysis
  - [ ] Third-party service orchestration
  - [ ] Webhook and event-driven workflows
  - [ ] **🆕 Multi-country news monitoring expansion**
  - [ ] **🆕 Social media monitoring integration (Twitter, Facebook, etc.)**

- [ ] **Enterprise Features**
  - [ ] Custom agent development framework
  - [ ] Workflow templates and marketplace
  - [ ] Team collaboration on agent workflows
  - [ ] Advanced analytics and workflow insights
  - [ ] **🆕 Custom monitoring dashboards for news organizations**
  - [ ] **🆕 White-label news intelligence platform**

## 🚀 Future Enhancements

### Advanced Features
- **Collaborative Analysis**: Team workspaces and shared analyses
- **AI Chat Integration**: Interactive analysis discussions with agents
- **Custom Analysis Templates**: User-defined agent workflows
- **Integration APIs**: Third-party service connections via agents
- **Mobile API**: Optimized endpoints for mobile apps

### Analytics & Insights
- **Usage Analytics**: Track analysis patterns and preferences
- **Performance Metrics**: Monitor analysis quality and speed
- **User Behavior Analysis**: Understand feature usage patterns
- **Agent Performance Analytics**: Monitor agent effectiveness and optimization opportunities

### Security & Compliance
- **Data Privacy**: GDPR compliance and data retention policies
- **Access Control**: Fine-grained permissions and role management
- **Audit Logging**: Comprehensive activity tracking
- **Agent Security**: Secure agent-to-agent communication and external API access 