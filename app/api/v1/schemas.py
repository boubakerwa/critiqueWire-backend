from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union
import datetime

# Common
class ResponseModel(BaseModel):
    status: str
    timestamp: str

class ErrorResponse(ResponseModel):
    status: Literal["error"] = "error"
    error: dict

# Health Check
class HealthData(BaseModel):
    status: str
    version: str

class HealthResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: HealthData

# --- v0.2 Analysis Presets ---

class AnalysisPreset(BaseModel):
    id: str = Field(..., description="Preset ID")
    name: str = Field(..., description="Preset name")
    description: str = Field(..., description="Preset description")
    prompt: str = Field(..., description="Analysis prompt")
    isDefault: bool = Field(..., description="Is default preset")
    isCustom: bool = Field(..., description="Is custom preset")
    createdBy: Optional[str] = Field(None, description="Created by user ID")
    options: "AnalysisOptions" = Field(..., description="Analysis options")
    createdAt: datetime.datetime
    updatedAt: datetime.datetime

class CreatePresetRequest(BaseModel):
    name: str = Field(..., description="Preset name")
    description: str = Field(..., description="Preset description")
    prompt: str = Field(..., description="Analysis prompt")
    options: "AnalysisOptions" = Field(..., description="Analysis options")

# --- Enhanced Analysis Options (v0.2) ---

class AnalysisOptions(BaseModel):
    includeBiasAnalysis: bool = Field(default=True, description="Include bias analysis")
    includeSentimentAnalysis: bool = Field(default=True, description="Include sentiment analysis")
    includeFactCheck: bool = Field(default=True, description="Include fact checking")
    includeClaimExtraction: bool = Field(default=True, description="Include claim extraction")
    includeSourceCredibility: bool = Field(default=False, description="Include source credibility assessment")
    includeExecutiveSummary: bool = Field(default=True, description="Include executive summary")
    # Legacy options for backward compatibility
    includeContextAnalysis: bool = Field(default=False, description="Include context analysis")
    includeSummary: bool = Field(default=False, description="Include summary")
    includeExpertOpinion: bool = Field(default=False, description="Include expert opinion")
    includeImpactAssessment: bool = Field(default=False, description="Include impact assessment")

# --- v0.3 Unified Analysis Request ---

class UnifiedAnalyzeRequest(BaseModel):
    url: Optional[str] = Field(None, description="The URL of the article to analyze. Either url or content must be provided.")
    content: Optional[str] = Field(None, description="The raw text content to analyze. Either url or content must be provided.")
    title: str = Field(..., description="The title of the content being analyzed")
    preset: Literal["general", "political", "financial", "scientific", "opinion"] = Field(
        default="general", 
        description="The analysis preset to use, which determines focus areas and analysis depth"
    )
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)
    async_mode: bool = Field(
        default=True, 
        description="Whether to process the analysis asynchronously (True) or synchronously (False)"
    )

# --- v0.2 Comprehensive Analysis Request ---

class ComprehensiveAnalyzeRequest(BaseModel):
    url: Optional[str] = Field(None, description="The URL of the article to analyze. Either url or content must be provided.")
    content: Optional[str] = Field(None, description="The raw text content to analyze. Either url or content must be provided.")
    title: str = Field(..., description="The title of the content being analyzed")
    preset: Literal["general", "political", "financial", "scientific", "opinion"] = Field(
        default="general", 
        description="The analysis preset to use, which determines focus areas and analysis depth"
    )
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)

# --- v0.2 Enhanced Analysis Result Schemas ---

class SentimentAnalysisResult(BaseModel):
    overallSentiment: Literal["very-positive", "positive", "neutral", "negative", "very-negative"] = Field(
        ..., description="Overall sentiment"
    )
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    emotionalTone: List[str] = Field(..., description="Emotional tone indicators")

class ExtractedClaim(BaseModel):
    id: str = Field(..., description="Claim ID")
    statement: str = Field(..., description="Claim statement")
    context: str = Field(..., description="Context")
    importance: Literal["high", "medium", "low"] = Field(..., description="Claim importance")
    category: Literal["factual", "opinion", "prediction", "statistic"] = Field(..., description="Claim category")

class FactCheckSource(BaseModel):
    name: str = Field(..., description="Source name")
    url: str = Field(..., description="Source URL")
    credibilityScore: Optional[float] = Field(None, ge=0, le=100, description="Source credibility score")

class FactCheckResult(BaseModel):
    claimId: str = Field(..., description="Associated claim ID")
    status: Literal["verified", "disputed", "unverified", "misleading", "false"] = Field(
        ..., description="Fact check status"
    )
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    sources: List[FactCheckSource] = Field(default_factory=list, description="Verification sources")
    explanation: str = Field(..., description="Fact check explanation")

class CredibilityFactors(BaseModel):
    transparency: float = Field(..., ge=0, le=100)
    accuracy: float = Field(..., ge=0, le=100)
    bias: float = Field(..., ge=0, le=100)
    ownership: float = Field(..., ge=0, le=100)
    expertise: float = Field(..., ge=0, le=100)

class SourceCredibilityResult(BaseModel):
    url: str = Field(..., description="Assessed URL")
    domain: str = Field(..., description="Domain")
    credibilityScore: float = Field(..., ge=0, le=100, description="Credibility score")
    assessment: Literal["highly-credible", "credible", "mixed", "questionable", "unreliable"] = Field(
        ..., description="Credibility assessment"
    )
    factors: CredibilityFactors = Field(..., description="Credibility factors")
    report: str = Field(..., description="Detailed assessment report")
    lastUpdated: datetime.datetime = Field(..., description="Last assessment update")

class ComprehensiveAnalysisResults(BaseModel):
    executiveSummary: str = Field(..., description="A concise summary of the analysis findings")
    biasAnalysis: Optional["BiasAnalysisResult"] = None
    sentimentAnalysis: Optional[SentimentAnalysisResult] = None
    claimsExtracted: List[ExtractedClaim] = Field(default_factory=list, description="Extracted claims")
    factCheckResults: List[FactCheckResult] = Field(default_factory=list, description="Fact check results")
    sourceCredibility: Optional[SourceCredibilityResult] = Field(None, description="Source credibility")
    analysisScore: float = Field(..., ge=0, le=100, description="Overall analysis score")

class AnalysisMetadata(BaseModel):
    processingTime: float = Field(..., description="Processing time in seconds")
    preset: str = Field(..., description="Analysis preset used")
    wordsAnalyzed: int = Field(..., description="Number of words analyzed")
    createdAt: datetime.datetime = Field(..., description="Analysis creation timestamp")

# --- Enhanced Analysis Results Data (v0.2) ---

class AnalysisResultsData(BaseModel):
    analysisId: str = Field(..., description="Analysis ID")
    articleId: Optional[str] = Field(None, description="The unique identifier for the article that was analyzed. Null for raw text analyses.")
    analysisType: Literal["url", "text"] = Field(..., description="Whether this analysis was performed on a URL or raw text content")
    status: Literal["pending", "completed", "failed"] = Field(..., description="Analysis status")
    results: Optional["ComprehensiveAnalysisResults"] = Field(None, description="Comprehensive analysis results (null when status is pending)")
    metadata: AnalysisMetadata = Field(..., description="Analysis metadata")

class AnalysisResultsResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: AnalysisResultsData

# --- Source Credibility Assessment ---

class SourceCredibilityRequest(BaseModel):
    url: str = Field(..., description="The URL of the source to assess for credibility")

# --- Analysis History (Enhanced v0.2) ---

class ArticleSummary(BaseModel):
    id: str = Field(..., description="Article ID")
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    domain: str = Field(..., description="Article domain")

class AnalysisHistoryItem(BaseModel):
    analysisId: str
    title: str
    preset: str
    analysisType: Literal["url", "text"]
    createdAt: datetime.datetime
    summary: str = Field(..., description="Brief summary of analysis results")
    analysisScore: float = Field(..., ge=0, le=100)
    article: Optional[ArticleSummary] = Field(None, description="Article details if analysis was performed on a URL")

class PaginatedAnalysisHistoryResponse(BaseModel):
    items: List[AnalysisHistoryItem]
    nextCursor: Optional[str] = None
    totalCount: int

# --- Export & Share Functionality ---

class ExportRequest(BaseModel):
    format: Literal["pdf", "docx", "html", "json", "csv"] = Field(..., description="Export format")
    includeCharts: bool = Field(default=True, description="Include charts and visualizations")
    includeRawData: bool = Field(default=False, description="Include raw analysis data")
    template: Literal["professional", "academic", "executive", "detailed"] = Field(
        default="professional", description="Report template"
    )

class ExportResponse(BaseModel):
    downloadUrl: str = Field(..., description="Download URL")
    filename: str = Field(..., description="Generated filename")
    fileSize: int = Field(..., description="File size in bytes")
    expiresAt: datetime.datetime = Field(..., description="Download link expiration")

class ShareRequest(BaseModel):
    accessLevel: Literal["view", "comment"] = Field(default="view", description="Access level")
    expiresIn: int = Field(default=604800, ge=3600, le=2592000, description="Expiration time in seconds")
    requirePassword: bool = Field(default=False, description="Require password")
    password: Optional[str] = Field(None, description="Share password")

class ShareResponse(BaseModel):
    shareUrl: str = Field(..., description="Shareable URL")
    shareId: str = Field(..., description="Share ID")
    expiresAt: datetime.datetime = Field(..., description="Share link expiration")
    accessLevel: str = Field(..., description="Access level")

# --- Legacy Analysis Schemas (for backward compatibility) ---

class AnalyzeArticleRequest(BaseModel):
    url: str
    content: Optional[str] = None
    title: str
    options: AnalysisOptions

class AnalysisStatusData(BaseModel):
    analysisId: str
    status: Literal["processing", "completed", "failed"]
    estimatedTime: int

class AnalysisStatusResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: AnalysisStatusData

class BiasedPhrase(BaseModel):
    phrase: str
    explanation: str
    suggestion: str

class BiasAnalysis(BaseModel):
    score: float
    politicalLean: Literal["left", "center", "right"]
    biasedPhrases: List[BiasedPhrase]
    overallAssessment: str

class VerifiedClaim(BaseModel):
    claim: str
    verdict: Literal["true", "false", "partially_true", "unverified"]
    explanation: str
    sources: List[str]

class FactCheck(BaseModel):
    verifiedClaims: List[VerifiedClaim]
    reliabilityScore: float

class RelatedEvent(BaseModel):
    event: str
    date: str
    relevance: str

class ContextAnalysis(BaseModel):
    historicalContext: str
    relatedEvents: List[RelatedEvent]
    keyStakeholders: List[str]

class Summary(BaseModel):
    executive: str
    detailed: str
    keyPoints: List[str]

class ExpertOpinion(BaseModel):
    analysis: str
    credentials: str
    potentialBias: str
    alternativeViewpoints: List[str]

class ImpactAssessment(BaseModel):
    socialImpact: str
    economicImpact: str
    politicalImpact: str
    environmentalImpact: str
    timeframe: Literal["short_term", "medium_term", "long_term"]

# --- Analysis Result Schemas (Refined based on FE feedback) ---

class BiasAnalysisDetail(BaseModel):
    quote: str
    explanation: str

class BiasAnalysisResult(BaseModel):
    score: float = Field(..., description="A score from 0.0 (neutral) to 1.0 (highly biased).")
    leaning: Literal["left", "center-left", "center", "center-right", "right"] = Field(..., description="The detected political leaning of the content.")
    summary: str = Field(..., description="A brief summary of the bias findings.")
    details: Optional[List[BiasAnalysisDetail]] = Field(None, description="Specific examples from the text that indicate bias.")

class FactCheckClaim(BaseModel):
    claim: str = Field(..., description="The claim extracted from the article.")
    verdict: Literal["verified", "unverified", "false", "misleading"] = Field(..., description="The verdict on the claim's accuracy.")
    source: Optional[str] = Field(None, description="A URL to a source validating the verdict.")
    explanation: Optional[str] = Field(None, description="A brief explanation of the fact-check.")

class FactCheckResultLegacy(BaseModel):
    claims: List[FactCheckClaim]

class ContextRelatedEvent(BaseModel):
    title: str
    url: str
    summary: Optional[str] = None

class ContextAnalysisResult(BaseModel):
    historicalBackground: str = Field(..., description="Historical context relevant to the article's topic.")
    relatedEvents: Optional[List[ContextRelatedEvent]] = Field(None, description="Links to articles about related events.")

class SummaryResult(BaseModel):
    text: str = Field(..., description="A concise summary of the article.")
    keyPoints: List[str] = Field(..., description="A list of bullet points highlighting the key takeaways.")

class ExpertOpinionDetail(BaseModel):
    expertName: str
    field: str = Field(..., description="The expert's field of expertise.")
    opinion: str = Field(..., description="The expert's opinion on the topic.")
    source: Optional[str] = Field(None, description="A URL to the source of the opinion.")

class ExpertOpinionResult(BaseModel):
    opinions: List[ExpertOpinionDetail]

class ImpactAssessmentResult(BaseModel):
    potentialImpact: str = Field(..., description="Analysis of the potential societal, economic, or political impact.")
    affectedGroups: List[str] = Field(..., description="A list of groups or sectors that may be affected.")

class AnalysisResultTypes(BaseModel):
    """Contains results for the requested analysis types. A key is only present if its corresponding option was true in the request."""
    biasAnalysis: Optional[BiasAnalysisResult] = None
    factCheck: Optional[FactCheckResultLegacy] = None
    contextAnalysis: Optional[ContextAnalysisResult] = None
    summary: Optional[SummaryResult] = None
    expertOpinion: Optional[ExpertOpinionResult] = None
    impactAssessment: Optional[ImpactAssessmentResult] = None

class AnalysisResultsDataLegacy(BaseModel):
    analysisId: str
    status: Literal["completed"]
    results: AnalysisResultTypes
    metadata: dict

class AnalysisResultsResponseLegacy(ResponseModel):
    status: Literal["success"] = "success"
    data: AnalysisResultsDataLegacy

# --- User Data Schemas (from FE feedback) ---

class Bookmark(BaseModel):
    id: str # Should be UUID, but keeping as string for now
    user_id: str # Should be UUID
    article_id: str # Should be UUID
    created_at: datetime.datetime

class CreateBookmarkRequest(BaseModel):
    article_id: str # Should be UUID

class AnalysisRecord(BaseModel):
    analysis_id: str # Should be UUID
    article_title: str
    article_url: Optional[str] = None
    status: Literal["processing", "completed", "failed"]
    created_at: datetime.datetime

class UserProfile(BaseModel):
    id: str # Should be UUID, but keeping as string for now
    username: str
    fullName: Optional[str] = None
    avatarUrl: Optional[str] = None
    updatedAt: Optional[datetime.datetime] = None

class UpdateUserProfileRequest(BaseModel):
    username: Optional[str] = None
    fullName: Optional[str] = None
    avatarUrl: Optional[str] = None

# Follow-up Questions
class Question(BaseModel):
    question: str
    context: str
    type: Literal["critical", "exploratory", "clarifying"]

class FollowUpQuestionsData(BaseModel):
    questions: List[Question]

class FollowUpQuestionsResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: FollowUpQuestionsData

class ChatContext(BaseModel):
    articleId: Optional[str] = None
    analysisId: Optional[str] = None
    topic: Optional[str] = None

class StartChatRequest(BaseModel):
    context: Optional[ChatContext] = None

class ChatSessionData(BaseModel):
    sessionId: str
    expiresAt: str

class ChatSessionResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: ChatSessionData

class ChatAttachment(BaseModel):
    type: Literal["article", "image", "link"]
    content: str

class ChatMessageRequest(BaseModel):
    message: str
    attachments: Optional[List[ChatAttachment]] = None

class ChatResponseSource(BaseModel):
    title: str
    url: str
    relevance: float

class ChatMessageResponseData(BaseModel):
    messageId: str
    response: dict

class ChatMessageResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: ChatMessageResponseData

# --- Content Extraction Schemas ---

class ContentExtractionRequest(BaseModel):
    url: str = Field(..., description="The URL of the article to extract content from")

class ExtractedContent(BaseModel):
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Full article text content")
    author: Optional[str] = Field(None, description="Article author")
    publishDate: Optional[str] = Field(None, description="Publication date in ISO format")
    images: List[str] = Field(default_factory=list, description="List of image URLs from the article")
    description: Optional[str] = Field(None, description="Article description/summary")
    wordCount: int = Field(..., description="Number of words in the article")
    readingTime: int = Field(..., description="Estimated reading time in minutes")
    extractionStrategy: str = Field(..., description="The extraction strategy that was used")
    processingTime: float = Field(..., description="Processing time in seconds")

class ContentExtractionResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: ExtractedContent
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())

# Forward reference resolution
AnalysisPreset.model_rebuild()
CreatePresetRequest.model_rebuild()

# --- RSS News Feed Schemas ---

class CollectedArticle(BaseModel):
    """Unified article schema for both RSS-collected and manual articles."""
    # Original articles table columns (always present)
    id: str = Field(..., description="Article UUID (primary key)")
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Article content (always available - uses title as fallback for RSS)")
    url: str = Field(..., description="Article URL")
    source_name: str = Field(..., description="News source name")
    author: Optional[str] = Field(None, description="Article author")
    published_at: Optional[str] = Field(None, description="Publication date")
    image_url: Optional[str] = Field(None, description="Article image URL (single image for all articles)")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    
    # RSS-specific columns (will be NULL for manual articles)
    summary: Optional[str] = Field(None, description="Article summary/excerpt (RSS)")
    source_url: Optional[str] = Field(None, description="RSS feed URL")
    collected_at: Optional[str] = Field(None, description="RSS collection timestamp (NULL for manual)")
    content_hash: Optional[str] = Field(None, description="Content hash for deduplication")
    word_count: Optional[int] = Field(None, description="Word count (if content extracted)")
    reading_time: Optional[int] = Field(None, description="Reading time in minutes")
    content_extracted_at: Optional[str] = Field(None, description="Content extraction timestamp")
    language: str = Field(default="unknown", description="Article language (ar, fr, en, unknown)")
    analysis_status: Literal["not_analyzed", "pending", "completed", "failed"] = Field(
        default="not_analyzed", description="Analysis status"
    )
    analysis_id: Optional[str] = Field(None, description="Analysis ID if analyzed")

class NewsFeedPagination(BaseModel):
    current_page: int = Field(..., description="Current page number")
    total_pages: int = Field(..., description="Total number of pages")
    total_articles: int = Field(..., description="Total number of articles")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")

class NewsFeedData(BaseModel):
    articles: List[CollectedArticle] = Field(..., description="List of news articles")
    pagination: NewsFeedPagination = Field(..., description="Pagination information")

class NewsFeedResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: NewsFeedData

class AnalyzeArticleRequest(BaseModel):
    preset: Literal["general", "political", "financial", "scientific", "opinion"] = Field(
        default="general", description="Analysis preset to use"
    )
    options: AnalysisOptions = Field(default_factory=AnalysisOptions, description="Analysis options")

class ArticleAnalysisData(BaseModel):
    analysis_id: str = Field(..., description="Analysis ID")
    status: Literal["pending", "completed", "failed"] = Field(..., description="Analysis status")
    estimated_completion_time: Optional[str] = Field(None, description="Estimated completion time")

class ArticleAnalysisResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: ArticleAnalysisData

class RSSCollectionStats(BaseModel):
    timestamp: str = Field(..., description="Collection timestamp")
    processing_time: float = Field(..., description="Processing time in seconds")
    feeds_processed: int = Field(..., description="Number of feeds processed")
    total_articles_found: int = Field(..., description="Total articles found")
    new_articles_stored: int = Field(..., description="New articles stored")
    errors: List[str] = Field(default_factory=list, description="Collection errors")

class RSSCollectionResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: RSSCollectionStats

class SchedulerJob(BaseModel):
    id: str = Field(..., description="Job ID")
    name: str = Field(..., description="Job name")
    next_run: Optional[str] = Field(None, description="Next run time")
    trigger: str = Field(..., description="Job trigger description")

class SchedulerStatus(BaseModel):
    status: Literal["running", "stopped", "not_started"] = Field(..., description="Scheduler status")
    jobs: List[SchedulerJob] = Field(..., description="List of scheduled jobs")

class SchedulerStatusResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: SchedulerStatus

class AvailableSourcesData(BaseModel):
    sources: List[str] = Field(..., description="Available news sources")

class AvailableSourcesResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: AvailableSourcesData

# Missing schemas for RSS endpoints
class RSSArticleAnalysisRequest(BaseModel):
    preset: Literal["general", "political", "financial", "scientific", "opinion"] = Field(
        default="general", description="Analysis preset to use"
    )
    options: AnalysisOptions = Field(default_factory=AnalysisOptions, description="Analysis options")

class RSSSourcesData(BaseModel):
    sources: List[str] = Field(..., description="Available RSS sources")
    total: int = Field(..., description="Total number of sources")

class RSSSourcesResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: RSSSourcesData 