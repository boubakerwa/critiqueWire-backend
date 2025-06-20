from pydantic import BaseModel
from typing import List, Optional, Literal

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

class AnalysisResultsData(BaseModel):
    analysisId: str
    status: Literal["completed"]
    results: dict # Simplified for now, can be more specific
    metadata: dict

class AnalysisResultsResponse(ResponseModel):
    status: Literal["success"] = "success"
    data: AnalysisResultsData

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