from pydantic import BaseModel, Field
from typing import List, Optional, Literal
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

# Article Analysis
class AnalysisOptions(BaseModel):
    includeBiasAnalysis: bool
    includeFactCheck: bool
    includeContextAnalysis: bool
    includeSummary: bool
    includeExpertOpinion: bool
    includeImpactAssessment: bool

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

class FactCheckResult(BaseModel):
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
    factCheck: Optional[FactCheckResult] = None
    contextAnalysis: Optional[ContextAnalysisResult] = None
    summary: Optional[SummaryResult] = None
    expertOpinion: Optional[ExpertOpinionResult] = None
    impactAssessment: Optional[ImpactAssessmentResult] = None

class AnalysisResultsData(BaseModel):
    analysisId: str
    status: Literal["completed"]
    results: AnalysisResultTypes
    metadata: dict

class AnalysisResultsResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: AnalysisResultsData

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
    id: str # Should be UUID
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    updated_at: Optional[datetime.datetime] = None

class UpdateUserProfileRequest(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

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

# AI Reporter Chat
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