from fastapi import APIRouter, Depends, HTTPException
from app.api.v1 import schemas
from app.core.security import get_current_user
from app.services.openai_service import openai_service
from app.core.config import settings
import datetime
import asyncio
import time
from typing import List

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

@router.post(
    "/analysis/article/sync",
    response_model=schemas.AnalysisResultsResponse,
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

@router.get("/analysis/{analysis_id}", response_model=schemas.AnalysisResultsResponse)
async def get_analysis_results(
    analysis_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Retrieve analysis results.
    """
    # This is a placeholder response. In a real application,
    # you would fetch the results from a database or cache.
    return {
        "status": "success",
        "data": {
            "analysisId": analysis_id,
            "status": "completed",
            "results": {
                "biasAnalysis": await openai_service.get_bias_analysis("..."),
                "factCheck": await openai_service.get_fact_check("...")
            },
            "metadata": {
                "analyzedAt": datetime.datetime.utcnow().isoformat(),
                "processingTime": 30,
                "modelVersion": "gpt-4o-mini",
                "confidenceScore": 0.95
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
        "id": "mock-bookmark-id",
        "user_id": user.id,
        "article_id": request.article_id,
        "created_at": datetime.datetime.utcnow()
    }

@router.delete("/bookmarks/{bookmark_id}", status_code=204, tags=["User Data"])
async def delete_bookmark(bookmark_id: str, user: dict = Depends(get_current_user)):
    # Placeholder
    return

@router.get("/analyses", response_model=List[schemas.AnalysisRecord], tags=["User Data"])
async def list_user_analyses(user: dict = Depends(get_current_user)):
    # Placeholder
    return []

@router.get("/profile", response_model=schemas.UserProfile, tags=["User Data"])
async def get_user_profile(user: dict = Depends(get_current_user)):
    # Placeholder
    return {
        "id": user.id,
        "username": "mock_username",
        "full_name": "Mock User",
        "avatar_url": "http://example.com/avatar.png",
        "updated_at": datetime.datetime.utcnow()
    }

@router.patch("/profile", response_model=schemas.UserProfile, tags=["User Data"])
async def update_user_profile(request: schemas.UpdateUserProfileRequest, user: dict = Depends(get_current_user)):
    # Placeholder
    return {
        "id": user.id,
        "username": request.username or "mock_username",
        "full_name": request.full_name or "Mock User",
        "avatar_url": request.avatar_url or "http://example.com/avatar.png",
        "updated_at": datetime.datetime.utcnow()
    } 