from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.v1 import schemas
from app.core.security import get_current_user
from app.services.openai_service import openai_service
from app.core.config import settings
import datetime
import asyncio
import time
import uuid
from typing import List, Optional
from urllib.parse import urlparse

router = APIRouter()

@router.get("/health", response_model=schemas.HealthResponse)
def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "success",
        "data": {
            "status": "healthy",
            "version": "1.0.0"
        },
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

# --- v0.2 Comprehensive Analysis System ---

@router.post(
    "/analyses/comprehensive",
    response_model=schemas.AnalysisResultsResponse,
    tags=["Analysis"],
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "url_political_analysis": {
                            "summary": "Political Analysis of URL",
                            "value": {
                                "url": "https://example.com/political-article",
                                "title": "New Climate Policy Sparks Congressional Debate",
                                "preset": "political",
                                "options": {
                                    "includeBiasAnalysis": True,
                                    "includeSentimentAnalysis": True,
                                    "includeFactCheck": True,
                                    "includeClaimExtraction": True,
                                    "includeSourceCredibility": True,
                                    "includeExecutiveSummary": True
                                }
                            }
                        },
                        "text_financial_analysis": {
                            "summary": "Financial Analysis of Raw Text",
                            "value": {
                                "content": "The Federal Reserve announced today a surprise interest rate hike of 0.75 basis points, citing persistent inflation concerns. Market analysts predict this could trigger a recession within the next 6 months, though some economists argue the move was necessary to prevent runaway inflation.",
                                "title": "Fed Raises Interest Rates Amid Inflation Fears",
                                "preset": "financial",
                                "options": {
                                    "includeBiasAnalysis": True,
                                    "includeSentimentAnalysis": True,
                                    "includeFactCheck": True,
                                    "includeClaimExtraction": True,
                                    "includeExecutiveSummary": True
                                }
                            }
                        }
                    }
                }
            }
        }
    }
)
async def comprehensive_analysis(
    request: schemas.ComprehensiveAnalyzeRequest,
    user: dict = Depends(get_current_user),
):
    """
    Perform comprehensive analysis on URL or text content with configurable presets.
    Supports both URL and raw text analysis with advanced journalist features.
    """
    start_time = time.time()
    
    # Validate input
    if not request.url and not request.content:
        raise HTTPException(status_code=400, detail="Either 'url' or 'content' must be provided")
    
    if request.url and request.content:
        raise HTTPException(status_code=400, detail="Provide either 'url' or 'content', not both")
    
    # Determine analysis type and get content
    analysis_type = "url" if request.url else "text"
    article_id = None
    
    if analysis_type == "url":
        # TODO: Implement URL fetching and article_id generation
        # For now, simulate content extraction
        content = f"Content extracted from {request.url}. This is a placeholder implementation."
        article_id = str(uuid.uuid4())
        domain = urlparse(request.url).netloc
    else:
        content = request.content
        domain = None
    
    if not content:
        raise HTTPException(status_code=400, detail="Could not extract content from URL")
    
    analysis_id = str(uuid.uuid4())
    
    # Build comprehensive analysis tasks based on options
    tasks = {}
    
    if request.options.includeBiasAnalysis:
        tasks["biasAnalysis"] = openai_service.get_comprehensive_bias_analysis(content, request.preset)
    
    if request.options.includeSentimentAnalysis:
        tasks["sentimentAnalysis"] = openai_service.get_sentiment_analysis(content, request.preset)
    
    if request.options.includeClaimExtraction:
        tasks["claimsExtracted"] = openai_service.extract_claims(content, request.preset)
    
    if request.options.includeFactCheck:
        # We'll need claims first for fact-checking
        pass  # Will be handled after claim extraction
    
    if request.options.includeSourceCredibility and request.url:
        tasks["sourceCredibility"] = openai_service.assess_source_credibility(request.url)
    
    if request.options.includeExecutiveSummary:
        tasks["executiveSummary"] = openai_service.get_executive_summary(content, request.preset)
    
    # Execute tasks concurrently
    if tasks:
        results_values = await asyncio.gather(*tasks.values())
        results_dict = dict(zip(tasks.keys(), results_values))
    else:
        results_dict = {}
    
    # Handle fact-checking after claim extraction
    fact_check_results = []
    if request.options.includeFactCheck and "claimsExtracted" in results_dict:
        claims = results_dict.get("claimsExtracted", [])
        if claims:
            fact_check_tasks = [
                openai_service.fact_check_claim(claim.statement, claim.id) 
                for claim in claims[:5]  # Limit to first 5 claims for performance
            ]
            fact_check_results = await asyncio.gather(*fact_check_tasks)
    
    # Calculate overall analysis score
    analysis_score = openai_service.calculate_analysis_score(results_dict)
    
    processing_time = time.time() - start_time
    
    # Build comprehensive results
    comprehensive_results = schemas.ComprehensiveAnalysisResults(
        executiveSummary=results_dict.get("executiveSummary", "Analysis completed successfully."),
        biasAnalysis=results_dict.get("biasAnalysis"),
        sentimentAnalysis=results_dict.get("sentimentAnalysis"),
        claimsExtracted=results_dict.get("claimsExtracted", []),
        factCheckResults=fact_check_results,
        sourceCredibility=results_dict.get("sourceCredibility"),
        analysisScore=analysis_score
    )
    
    metadata = schemas.AnalysisMetadata(
        processingTime=round(processing_time, 2),
        preset=request.preset,
        wordsAnalyzed=len(content.split()),
        createdAt=datetime.datetime.utcnow()
    )
    
    return {
        "status": "success",
        "data": {
            "analysisId": analysis_id,
            "articleId": article_id,
            "analysisType": analysis_type,
            "status": "completed",
            "results": comprehensive_results,
            "metadata": metadata
        },
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

# --- Source Credibility Assessment ---

@router.post(
    "/source-credibility",
    response_model=schemas.SourceCredibilityResult,
    tags=["Analysis"]
)
async def assess_source_credibility(
    request: schemas.SourceCredibilityRequest,
    user: dict = Depends(get_current_user),
):
    """
    Assess the credibility of a news source or website URL.
    Provides detailed scoring across multiple credibility factors.
    """
    try:
        result = await openai_service.assess_source_credibility(request.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Credibility assessment failed: {str(e)}")

# --- Enhanced Analysis History ---

@router.get(
    "/analyses",
    response_model=schemas.PaginatedAnalysisHistoryResponse,
    tags=["Analysis"]
)
async def get_analysis_history(
    user: dict = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100, description="Number of analyses to return"),
    cursor: Optional[str] = Query(default=None, description="Cursor for pagination"),
    search: Optional[str] = Query(default=None, description="Search term to filter analyses"),
    preset: Optional[str] = Query(default=None, description="Filter by analysis preset"),
    analysis_type: Optional[str] = Query(default=None, description="Filter by analysis type"),
    date_from: Optional[str] = Query(default=None, description="Filter analyses from this date"),
    date_to: Optional[str] = Query(default=None, description="Filter analyses up to this date"),
):
    """
    Retrieve user's analysis history with advanced filtering and search capabilities.
    Supports pagination, search, and multiple filter options for efficient data retrieval.
    """
    # TODO: Implement actual database queries
    # For now, return comprehensive mock data for testing
    now = datetime.datetime.utcnow()
    mock_items = [
        schemas.AnalysisHistoryItem(
            analysisId="analysis-1",
            title="Climate Policy Analysis",
            preset="political",
            analysisType="url",
            createdAt=now - datetime.timedelta(days=1),
            summary="Comprehensive analysis of climate policy debate showing moderate bias toward environmental concerns.",
            analysisScore=78.5,
            article=schemas.ArticleSummary(
                id="article-1",
                title="New Climate Policy Sparks Congressional Debate",
                url="https://example.com/climate-policy",
                domain="example.com"
            )
        ),
        schemas.AnalysisHistoryItem(
            analysisId="analysis-2",
            title="Market Analysis Text",
            preset="financial",
            analysisType="text",
            createdAt=now - datetime.timedelta(days=2),
            summary="Financial analysis revealing bearish sentiment with high confidence in economic indicators.",
            analysisScore=82.3,
            article=None
        ),
        schemas.AnalysisHistoryItem(
            analysisId="analysis-3",
            title="Scientific Research Paper Review",
            preset="scientific",
            analysisType="url",
            createdAt=now - datetime.timedelta(days=3),
            summary="Detailed analysis of peer-reviewed research methodology and data integrity.",
            analysisScore=91.7,
            article=schemas.ArticleSummary(
                id="article-3",
                title="Breakthrough in Quantum Computing Research",
                url="https://nature.com/quantum-computing",
                domain="nature.com"
            )
        ),
        schemas.AnalysisHistoryItem(
            analysisId="analysis-4",
            title="Opinion Piece Analysis",
            preset="opinion",
            analysisType="text",
            createdAt=now - datetime.timedelta(days=4),
            summary="Analysis of editorial content revealing strong partisan bias and emotional language.",
            analysisScore=45.2,
            article=None
        ),
        schemas.AnalysisHistoryItem(
            analysisId="analysis-5",
            title="Economic Policy Debate",
            preset="political",
            analysisType="url",
            createdAt=now - datetime.timedelta(days=5),
            summary="Political analysis of economic policy proposals with focus on stakeholder impacts.",
            analysisScore=67.8,
            article=schemas.ArticleSummary(
                id="article-5",
                title="Tax Reform Bill Faces Opposition",
                url="https://news.com/tax-reform",
                domain="news.com"
            )
        )
    ]
    
    # Apply filters (comprehensive implementation)
    filtered_items = mock_items
    
    # Search filter
    if search:
        search_lower = search.lower()
        filtered_items = [
            item for item in filtered_items 
            if (search_lower in item.title.lower() or 
                search_lower in item.summary.lower())
        ]
    
    # Preset filter
    if preset:
        filtered_items = [item for item in filtered_items if item.preset == preset]
    
    # Analysis type filter
    if analysis_type:
        filtered_items = [item for item in filtered_items if item.analysisType == analysis_type]
    
    # Date range filters
    if date_from:
        try:
            date_from_obj = datetime.datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            filtered_items = [item for item in filtered_items if item.createdAt >= date_from_obj]
        except ValueError:
            # If date parsing fails, continue without date filtering
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            filtered_items = [item for item in filtered_items if item.createdAt <= date_to_obj]
        except ValueError:
            # If date parsing fails, continue without date filtering
            pass
    
    # Sort by creation date (newest first)
    filtered_items.sort(key=lambda x: x.createdAt, reverse=True)
    
    # Apply pagination
    total_count = len(filtered_items)
    start_index = 0
    
    # Handle cursor-based pagination (simplified implementation)
    if cursor and cursor != "next-cursor":
        # In a real implementation, you'd decode the cursor to get the start index
        start_index = 0  # Simplified for mock data
    
    end_index = start_index + limit
    items = filtered_items[start_index:end_index]
    
    # Determine next cursor
    next_cursor = None
    if end_index < total_count:
        next_cursor = "next-cursor"  # In real implementation, encode the next position
    
    return {
        "items": items,
        "nextCursor": next_cursor,
        "totalCount": total_count
    }

# --- Export & Share Functionality ---

@router.post(
    "/analyses/{analysis_id}/export",
    response_model=schemas.ExportResponse,
    tags=["Analysis"]
)
async def export_analysis(
    analysis_id: str,
    request: schemas.ExportRequest,
    user: dict = Depends(get_current_user),
):
    """
    Generate an exportable report of the analysis in the specified format.
    Supports multiple formats and templates for professional reporting.
    """
    # TODO: Implement actual export functionality
    # For now, return mock response
    filename = f"analysis-{analysis_id}.{request.format}"
    mock_url = f"https://api.critiquewire.com/exports/{filename}"
    
    return schemas.ExportResponse(
        downloadUrl=mock_url,
        filename=filename,
        fileSize=1024000,  # 1MB mock size
        expiresAt=datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    )

@router.post(
    "/analyses/{analysis_id}/share",
    response_model=schemas.ShareResponse,
    tags=["Analysis"]
)
async def share_analysis(
    analysis_id: str,
    request: schemas.ShareRequest,
    user: dict = Depends(get_current_user),
):
    """
    Create a shareable link for the analysis with configurable permissions.
    Supports password protection and expiration settings.
    """
    # TODO: Implement actual sharing functionality
    # For now, return mock response
    share_id = str(uuid.uuid4())
    share_url = f"https://app.critiquewire.com/shared/{share_id}"
    
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=request.expiresIn)
    
    return schemas.ShareResponse(
        shareUrl=share_url,
        shareId=share_id,
        expiresAt=expiration_time,
        accessLevel=request.accessLevel
    )

# --- Analysis Presets Management ---

@router.get(
    "/analysis-presets",
    response_model=List[schemas.AnalysisPreset],
    tags=["Analysis"]
)
async def get_analysis_presets(user: dict = Depends(get_current_user)):
    """
    Retrieve all available analysis presets for the user.
    Includes both default system presets and custom user presets.
    """
    # TODO: Implement actual preset retrieval from database
    # For now, return default presets plus any custom presets
    now = datetime.datetime.utcnow()
    default_presets = [
        schemas.AnalysisPreset(
            id="general",
            name="General Analysis",
            description="Balanced analysis suitable for most content types",
            prompt="Perform a comprehensive analysis focusing on objectivity, accuracy, and clarity.",
            isDefault=True,
            isCustom=False,
            createdBy=None,
            options=schemas.AnalysisOptions(),
            createdAt=now,
            updatedAt=now
        ),
        schemas.AnalysisPreset(
            id="political",
            name="Political Analysis",
            description="Specialized analysis for political content with bias detection",
            prompt="Analyze political content with focus on bias, loaded language, and partisan framing.",
            isDefault=True,
            isCustom=False,
            createdBy=None,
            options=schemas.AnalysisOptions(
                includeBiasAnalysis=True,
                includeSentimentAnalysis=True,
                includeClaimExtraction=True,
                includeFactCheck=True
            ),
            createdAt=now,
            updatedAt=now
        ),
        schemas.AnalysisPreset(
            id="financial",
            name="Financial Analysis",
            description="Analysis optimized for financial and economic content",
            prompt="Analyze financial content focusing on market sentiment, economic indicators, and data accuracy.",
            isDefault=True,
            isCustom=False,
            createdBy=None,
            options=schemas.AnalysisOptions(
                includeSentimentAnalysis=True,
                includeClaimExtraction=True,
                includeFactCheck=True,
                includeExecutiveSummary=True
            ),
            createdAt=now,
            updatedAt=now
        )
    ]
    
    # TODO: In a real implementation, fetch custom presets from database
    # For now, include a mock custom preset to demonstrate functionality
    user_id = getattr(user, 'id', None)
    custom_presets = [
        schemas.AnalysisPreset(
            id="a43c74cf-7f0c-4ee3-8afa-8b468250d17e",  # Mock custom preset ID
            name="Scientific Analysis",
            description="Specialized analysis for scientific papers and research",
            prompt="Analyze scientific content focusing on methodology, data integrity, and peer review standards.",
            isDefault=False,
            isCustom=True,
            createdBy=user_id,
            options=schemas.AnalysisOptions(
                includeBiasAnalysis=True,
                includeSentimentAnalysis=False,
                includeFactCheck=True,
                includeClaimExtraction=True,
                includeSourceCredibility=True,
                includeExecutiveSummary=True
            ),
            createdAt=now - datetime.timedelta(hours=1),
            updatedAt=now - datetime.timedelta(hours=1)
        )
    ]
    
    # Combine default and custom presets
    all_presets = default_presets + custom_presets
    
    return all_presets

@router.post(
    "/analysis-presets",
    response_model=schemas.AnalysisPreset,
    status_code=201,
    tags=["Analysis"]
)
async def create_analysis_preset(
    request: schemas.CreatePresetRequest,
    user: dict = Depends(get_current_user),
):
    """
    Create a new custom analysis preset for the user or organization.
    Custom presets allow tailored analysis configurations for specific needs.
    """
    try:
        # Generate a unique preset ID
        preset_id = str(uuid.uuid4())
        
        # Get user ID from the Supabase user object
        # The user object from Supabase has an 'id' field, not 'user_id'
        user_id = getattr(user, 'id', None)
        
        return schemas.AnalysisPreset(
            id=preset_id,
            name=request.name,
            description=request.description,
            prompt=request.prompt,
            isDefault=False,
            isCustom=True,
            createdBy=user_id,
            options=request.options,
            createdAt=datetime.datetime.utcnow(),
            updatedAt=datetime.datetime.utcnow()
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error creating preset: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create preset: {str(e)}"
        )

# --- Legacy Analysis Endpoints (Backward Compatibility) ---

@router.post(
    "/analysis/article/sync",
    response_model=schemas.AnalysisResultsResponseLegacy,
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "minimal_analysis": {
                            "summary": "Minimal Analysis (Bias & Fact-Check)",
                            "value": {
                                "url": "http://example.com/article1",
                                "content": "A new study published today suggests that eating chocolate every day can lead to significant weight loss. The study, funded by the International Confectioners Guild, followed 50 participants over a two-week period. Critics, however, argue the study's methodology is flawed and the sample size is too small to be conclusive.",
                                "title": "Daily Chocolate Intake Linked to Weight Loss, Study Finds",
                                "options": {
                                    "includeBiasAnalysis": True,
                                    "includeFactCheck": True,
                                    "includeContextAnalysis": False,
                                    "includeSummary": False,
                                    "includeExpertOpinion": False,
                                    "includeImpactAssessment": False,
                                },
                            },
                        },
                        "full_analysis": {
                            "summary": "Full Analysis (All Options)",
                            "value": {
                                "url": "http://example.com/article2",
                                "content": "Lawmakers in the state are debating a controversial new bill that would mandate all new vehicle sales be electric by 2035. Proponents claim the move is essential for meeting climate goals and reducing air pollution. Opponents, including automotive industry lobbyists and some consumer groups, warn of skyrocketing vehicle prices, grid instability, and a lack of charging infrastructure, particularly in rural areas.",
                                "title": "State Debates Landmark Bill to Ban Gas Cars by 2035",
                                "options": {
                                    "includeBiasAnalysis": True,
                                    "includeFactCheck": True,
                                    "includeContextAnalysis": True,
                                    "includeSummary": True,
                                    "includeExpertOpinion": True,
                                    "includeImpactAssessment": True,
                                },
                            },
                        },
                    }
                }
            }
        }
    },
)
async def analyze_article_sync(
    request: schemas.AnalyzeArticleRequest,
    user: dict = Depends(get_current_user),
):
    """
    Submit an article for synchronous analysis.
    Returns the full analysis results directly.
    """
    start_time = time.time()
    article_content = request.content or "" # Assuming content is provided for now

    if not article_content:
        # TODO: Implement URL fetching if content is not provided
        raise HTTPException(status_code=400, detail="Article content is required for now.")

    tasks = {}
    options_map = {
        "biasAnalysis": (request.options.includeBiasAnalysis, openai_service.get_bias_analysis),
        "factCheck": (request.options.includeFactCheck, openai_service.get_fact_check),
        "contextAnalysis": (request.options.includeContextAnalysis, openai_service.get_context_analysis),
        "summary": (request.options.includeSummary, openai_service.get_summary),
        "expertOpinion": (request.options.includeExpertOpinion, openai_service.get_expert_opinion),
        "impactAssessment": (request.options.includeImpactAssessment, openai_service.get_impact_assessment),
    }

    for key, (include, method) in options_map.items():
        if include:
            tasks[key] = method(article_content)

    # Run tasks concurrently
    if not tasks:
        return {
             "status": "success",
             "data": {
                "analysisId": f"sync-{int(start_time)}",
                "status": "completed",
                "results": {},
                "metadata": {
                    "analyzedAt": datetime.datetime.utcnow().isoformat(),
                    "processingTime": 0,
                    "modelVersion": openai_service.model,
                }
            },
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    results_values = await asyncio.gather(*tasks.values())
    results_dict = dict(zip(tasks.keys(), results_values))

    processing_time = time.time() - start_time

    # Construct the final results object using the refined schema
    final_results = schemas.AnalysisResultTypes(**results_dict)

    return {
        "status": "success",
        "data": {
            "analysisId": f"sync-{int(start_time)}",
            "status": "completed",
            "results": final_results,
            "metadata": {
                "analyzedAt": datetime.datetime.utcnow().isoformat(),
                "processingTime": round(processing_time, 2),
                "modelVersion": openai_service.model,
            }
        },
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@router.post("/analysis/article", response_model=schemas.AnalysisStatusResponse)
async def analyze_article(
    request: schemas.AnalyzeArticleRequest,
    user: dict = Depends(get_current_user)
):
    """
    Submit an article for analysis.
    """
    # This is a placeholder response. In a real application,
    # you would start a background task here.
    return {
        "status": "success",
        "data": {
            "analysisId": "mock-analysis-id",
            "status": "processing",
            "estimatedTime": 60
        },
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@router.get("/analysis/{analysis_id}", response_model=schemas.AnalysisResultsResponseLegacy)
async def get_analysis_results(
    analysis_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get analysis results for a specific analysis ID (legacy format).
    """
    # Placeholder implementation
    return {
        "status": "success",
        "data": {
            "analysisId": analysis_id,
            "status": "completed",
            "results": {
                "biasAnalysis": {
                    "score": 0.3,
                    "leaning": "center",
                    "summary": "The article shows minimal bias.",
                    "details": []
                },
                "factCheck": {
                    "claims": [
                        {
                            "claim": "Sample claim",
                            "verdict": "verified",
                            "source": "https://example.com",
                            "explanation": "This claim has been verified."
                        }
                    ]
                }
            },
            "metadata": {
                "processingTime": 2.5,
                "preset": "general",
                "wordsAnalyzed": 500
            }
        },
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@router.get("/analyses/{analysis_id}", response_model=schemas.AnalysisResultsResponse)
async def get_unified_analysis_results(
    analysis_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get analysis results for a specific analysis ID (unified format).
    This endpoint returns results in the new comprehensive format.
    """
    # Placeholder implementation - in real app, this would fetch from database
    return {
        "status": "success",
        "data": {
            "analysisId": analysis_id,
            "articleId": "article-123",
            "analysisType": "url",
            "status": "completed",
            "results": {
                "executiveSummary": "This analysis found moderate bias and verified several key claims.",
                "biasAnalysis": {
                    "score": 0.3,
                    "leaning": "center",
                    "summary": "The article shows minimal bias.",
                    "details": []
                },
                "sentimentAnalysis": {
                    "overallSentiment": "neutral",
                    "confidence": 0.8,
                    "emotionalTone": ["objective", "analytical"]
                },
                "claimsExtracted": [
                    {
                        "id": "claim-1",
                        "statement": "Sample claim statement",
                        "context": "Context of the claim",
                        "importance": "high",
                        "category": "factual"
                    }
                ],
                "factCheckResults": [
                    {
                        "claimId": "claim-1",
                        "status": "verified",
                        "confidence": 0.9,
                        "sources": [
                            {
                                "name": "Reliable Source",
                                "url": "https://example.com/verification",
                                "credibilityScore": 95.0
                            }
                        ],
                        "explanation": "This claim has been verified by multiple sources."
                    }
                ],
                "sourceCredibility": {
                    "url": "https://example.com/article",
                    "domain": "example.com",
                    "credibilityScore": 85.0,
                    "assessment": "credible",
                    "factors": {
                        "transparency": 80.0,
                        "accuracy": 90.0,
                        "bias": 75.0,
                        "ownership": 85.0,
                        "expertise": 80.0
                    },
                    "report": "This source demonstrates good credibility with transparent reporting.",
                    "lastUpdated": datetime.datetime.utcnow()
                },
                "analysisScore": 82.5
            },
            "metadata": {
                "processingTime": 2.5,
                "preset": "general",
                "wordsAnalyzed": 500,
                "createdAt": datetime.datetime.utcnow()
            }
        },
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

# --- User Data Endpoints (Placeholders) ---

@router.get("/bookmarks", response_model=List[schemas.Bookmark], tags=["User Data"])
async def list_user_bookmarks(user: dict = Depends(get_current_user)):
    # Placeholder
    return []

@router.post("/bookmarks", response_model=schemas.Bookmark, status_code=201, tags=["User Data"])
async def create_bookmark(request: schemas.CreateBookmarkRequest, user: dict = Depends(get_current_user)):
    # Placeholder
    return {
        "id": "bookmark-123", 
        "user_id": user.get("user_id", "user-123"), 
        "article_id": request.article_id, 
        "created_at": datetime.datetime.utcnow()
    }

@router.delete("/bookmarks/{bookmark_id}", status_code=204, tags=["User Data"])
async def delete_bookmark(bookmark_id: str, user: dict = Depends(get_current_user)):
    # Placeholder
    pass

@router.get("/profile", response_model=schemas.UserProfile, tags=["User Data"])
async def get_user_profile(user: dict = Depends(get_current_user)):
    """
    Get user profile information.
    """
    # Placeholder implementation
    return {
        "id": getattr(user, 'id', 'user-123'),
        "username": getattr(user, 'email', 'testuser').split('@')[0],
        "fullName": "Test User",
        "avatarUrl": "https://example.com/avatar.jpg",
        "updatedAt": datetime.datetime.utcnow()
    }

@router.patch("/profile", response_model=schemas.UserProfile, tags=["User Data"])
async def update_user_profile(request: schemas.UpdateUserProfileRequest, user: dict = Depends(get_current_user)):
    """
    Update user profile information.
    """
    # Placeholder implementation
    return {
        "id": getattr(user, 'id', 'user-123'),
        "username": request.username or getattr(user, 'email', 'testuser').split('@')[0],
        "fullName": request.fullName or "Test User",
        "avatarUrl": request.avatarUrl or "https://example.com/avatar.jpg",
        "updatedAt": datetime.datetime.utcnow()
    }

# --- Unified Analysis Endpoint (v0.3) ---

@router.post(
    "/analyses",
    response_model=schemas.AnalysisResultsResponse,
    tags=["Analysis"],
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "async_comprehensive_analysis": {
                            "summary": "Async Comprehensive Analysis",
                            "value": {
                                "url": "https://example.com/article",
                                "title": "Article Title",
                                "preset": "general",
                                "options": {
                                    "includeBiasAnalysis": True,
                                    "includeSentimentAnalysis": True,
                                    "includeFactCheck": True,
                                    "includeClaimExtraction": True,
                                    "includeSourceCredibility": True,
                                    "includeExecutiveSummary": True
                                },
                                "async": True
                            }
                        },
                        "sync_quick_analysis": {
                            "summary": "Sync Quick Analysis",
                            "value": {
                                "content": "Article content here...",
                                "title": "Quick Analysis",
                                "preset": "general",
                                "options": {
                                    "includeBiasAnalysis": True,
                                    "includeFactCheck": True
                                },
                                "async": False
                            }
                        }
                    }
                }
            }
        }
    }
)
async def unified_analysis(
    request: schemas.UnifiedAnalyzeRequest,
    user: dict = Depends(get_current_user),
):
    """
    Unified analysis endpoint that handles both comprehensive and legacy analysis types.
    Supports both async and sync modes based on the request configuration.
    """
    start_time = time.time()
    
    # Validate input
    if not request.url and not request.content:
        raise HTTPException(status_code=400, detail="Either 'url' or 'content' must be provided")
    
    if request.url and request.content:
        raise HTTPException(status_code=400, detail="Provide either 'url' or 'content', not both")
    
    # Determine analysis type and get content
    analysis_type = "url" if request.url else "text"
    article_id = None
    
    if analysis_type == "url":
        # TODO: Implement URL fetching and article_id generation
        content = f"Content extracted from {request.url}. This is a placeholder implementation."
        article_id = str(uuid.uuid4())
        domain = urlparse(request.url).netloc
    else:
        content = request.content
        domain = None
    
    if not content:
        raise HTTPException(status_code=400, detail="Could not extract content from URL")
    
    analysis_id = str(uuid.uuid4())
    
    # If async mode is requested, return immediately with task status
    if request.async_mode:
        # TODO: In production, this would start a background task
        return {
            "status": "success",
            "data": {
                "analysisId": analysis_id,
                "articleId": article_id,
                "analysisType": analysis_type,
                "status": "pending",
                "results": None,
                "metadata": schemas.AnalysisMetadata(
                    processingTime=0,
                    preset=request.preset,
                    wordsAnalyzed=len(content.split()),
                    createdAt=datetime.datetime.utcnow()
                )
            },
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    
    # Sync mode - perform analysis immediately
    # Build analysis tasks based on options
    tasks = {}
    
    if request.options.includeBiasAnalysis:
        tasks["biasAnalysis"] = openai_service.get_comprehensive_bias_analysis(content, request.preset)
    
    if request.options.includeSentimentAnalysis:
        tasks["sentimentAnalysis"] = openai_service.get_sentiment_analysis(content, request.preset)
    
    if request.options.includeClaimExtraction:
        tasks["claimsExtracted"] = openai_service.extract_claims(content, request.preset)
    
    if request.options.includeFactCheck:
        # Will be handled after claim extraction
        pass
    
    if request.options.includeSourceCredibility and request.url:
        tasks["sourceCredibility"] = openai_service.assess_source_credibility(request.url)
    
    if request.options.includeExecutiveSummary:
        tasks["executiveSummary"] = openai_service.get_executive_summary(content, request.preset)
    
    # Execute tasks concurrently
    if tasks:
        results_values = await asyncio.gather(*tasks.values())
        results_dict = dict(zip(tasks.keys(), results_values))
    else:
        results_dict = {}
    
    # Handle fact-checking after claim extraction
    fact_check_results = []
    if request.options.includeFactCheck and "claimsExtracted" in results_dict:
        claims = results_dict.get("claimsExtracted", [])
        if claims:
            fact_check_tasks = [
                openai_service.fact_check_claim(claim.statement, claim.id) 
                for claim in claims[:5]  # Limit to first 5 claims for performance
            ]
            fact_check_results = await asyncio.gather(*fact_check_tasks)
    
    # Calculate overall analysis score
    analysis_score = openai_service.calculate_analysis_score(results_dict)
    
    processing_time = time.time() - start_time
    
    # Build comprehensive results
    comprehensive_results = schemas.ComprehensiveAnalysisResults(
        executiveSummary=results_dict.get("executiveSummary", "Analysis completed successfully."),
        biasAnalysis=results_dict.get("biasAnalysis"),
        sentimentAnalysis=results_dict.get("sentimentAnalysis"),
        claimsExtracted=results_dict.get("claimsExtracted", []),
        factCheckResults=fact_check_results,
        sourceCredibility=results_dict.get("sourceCredibility"),
        analysisScore=analysis_score
    )
    
    metadata = schemas.AnalysisMetadata(
        processingTime=round(processing_time, 2),
        preset=request.preset,
        wordsAnalyzed=len(content.split()),
        createdAt=datetime.datetime.utcnow()
    )
    
    return {
        "status": "success",
        "data": {
            "analysisId": analysis_id,
            "articleId": article_id,
            "analysisType": analysis_type,
            "status": "completed",
            "results": comprehensive_results,
            "metadata": metadata
        },
        "timestamp": datetime.datetime.utcnow().isoformat()
    } 