from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.v1 import schemas
from app.core.security import get_current_user, get_current_user_with_token
from app.services.openai_service import openai_service
from app.services.database_service import database_service
from app.services.content_extraction_service import content_extraction_service
from app.core.config import settings
import datetime
import asyncio
import logging
import time
import uuid
from typing import List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

router = APIRouter()

# Background processing function for async analyses
async def process_analysis_background(
    analysis_id: str,
    user_id: str,
    content: str,
    analysis_types: List[str],
    preset: str,
    options: schemas.AnalysisOptions,
    url: Optional[str] = None,
    jwt_token: Optional[str] = None
):
    """Process analysis in the background and update the database with results."""
    try:
        print(f"[DEBUG] Starting background processing for analysis {analysis_id}")
        start_time = time.time()
        
        # Retrieve full content and metadata from database to ensure we have complete data
        db_data = await database_service.get_analysis_content_and_metadata(analysis_id, user_id, jwt_token)
        if db_data:
            # Use content from database (which should be complete)
            content = db_data["content"] or content  # Fallback to passed content if db content is empty
            preset = db_data["preset"] or preset
            url = db_data["url"] or url
            analysis_types = db_data["analysis_types"] or analysis_types
            print(f"[DEBUG] Retrieved content from database: {len(content)} characters")
        else:
            print(f"[DEBUG] Could not retrieve content from database, using passed content: {len(content)} characters")
        
        # Build analysis tasks based on options
        tasks = {}
        
        if options.includeBiasAnalysis:
            tasks["biasAnalysis"] = openai_service.get_comprehensive_bias_analysis(content, preset)
        
        if options.includeSentimentAnalysis:
            tasks["sentimentAnalysis"] = openai_service.get_sentiment_analysis(content, preset)
        
        if options.includeClaimExtraction:
            tasks["claimsExtracted"] = openai_service.extract_claims(content, preset)
        
        if options.includeSourceCredibility and url:
            tasks["sourceCredibility"] = openai_service.assess_source_credibility(url)
        
        if options.includeExecutiveSummary:
            tasks["executiveSummary"] = openai_service.get_executive_summary(content, preset)
        
        # Execute tasks concurrently
        if tasks:
            results_values = await asyncio.gather(*tasks.values())
            results_dict = dict(zip(tasks.keys(), results_values))
        else:
            results_dict = {}
        
        # Check if we got any valid results from OpenAI
        valid_results = [v for v in results_dict.values() if v is not None]
        if not valid_results and tasks:
            # All OpenAI calls failed, mark analysis as failed
            print(f"[ERROR] All OpenAI analysis tasks failed for analysis {analysis_id}")
            raise Exception("All OpenAI analysis tasks failed - no valid results obtained")
        
        # Handle fact-checking after claim extraction
        fact_check_results = []
        if options.includeFactCheck and "claimsExtracted" in results_dict:
            claims = results_dict.get("claimsExtracted", [])
            if claims:
                fact_check_tasks = [
                    openai_service.fact_check_claim(claim.statement, claim.id) 
                    for claim in claims[:5]  # Limit to first 5 claims for performance
                ]
                fact_check_results = await asyncio.gather(*fact_check_tasks)
                # Filter out failed fact-check results
                fact_check_results = [result for result in fact_check_results if result is not None]
        
        # Calculate overall analysis score
        analysis_score = openai_service.calculate_analysis_score(results_dict)
        
        processing_time = time.time() - start_time
        
        # Build comprehensive results and convert Pydantic models to dictionaries
        def serialize_for_db(obj):
            """Convert Pydantic models and other objects to JSON-serializable format."""
            if hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif hasattr(obj, 'dict'):
                return obj.dict()
            elif isinstance(obj, list):
                return [serialize_for_db(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: serialize_for_db(v) for k, v in obj.items()}
            else:
                return obj
        
        # Only build results if we have valid data - no fallback to generic messages
        comprehensive_results = {
            "executiveSummary": results_dict.get("executiveSummary"),  # No fallback - will be None if failed
            "biasAnalysis": serialize_for_db(results_dict.get("biasAnalysis")),
            "sentimentAnalysis": serialize_for_db(results_dict.get("sentimentAnalysis")),
            "claimsExtracted": serialize_for_db(results_dict.get("claimsExtracted", [])),
            "factCheckResults": serialize_for_db(fact_check_results),
            "sourceCredibility": serialize_for_db(results_dict.get("sourceCredibility")),
            "analysisScore": analysis_score
        }
        
        # Update the analysis in the database with completed results
        try:
            success = await database_service.update_analysis_status(
                analysis_id=analysis_id,
                user_id=user_id,
                status="completed",
                results=comprehensive_results,
                jwt_token=jwt_token
            )
            
            if success:
                print(f"[DEBUG] Successfully completed background processing for analysis {analysis_id}")
            else:
                print(f"[ERROR] Failed to update analysis status for {analysis_id} - database update returned False")
                # If update failed, mark as failed
                await database_service.update_analysis_status(
                    analysis_id=analysis_id,
                    user_id=user_id,
                    status="failed",
                    results=None,
                    jwt_token=jwt_token
                )
        except Exception as update_error:
            print(f"[ERROR] Exception while updating analysis {analysis_id}: {update_error}")
            import traceback
            traceback.print_exc()
            # Mark as failed
            try:
                await database_service.update_analysis_status(
                    analysis_id=analysis_id,
                    user_id=user_id,
                    status="failed",
                    results=None,
                    jwt_token=jwt_token
                )
            except Exception as fail_error:
                print(f"[ERROR] Failed to mark analysis {analysis_id} as failed: {fail_error}")
            
    except Exception as e:
        print(f"[ERROR] Background processing failed for analysis {analysis_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Update analysis status to failed
        try:
            success = await database_service.update_analysis_status(
                analysis_id=analysis_id,
                user_id=user_id,
                status="failed",
                results=None,
                jwt_token=jwt_token
            )
            if success:
                print(f"[DEBUG] Successfully marked analysis {analysis_id} as failed")
            else:
                print(f"[ERROR] Failed to update analysis {analysis_id} status to failed")
        except Exception as update_error:
            print(f"[ERROR] Exception while updating analysis {analysis_id} to failed status: {update_error}")
            traceback.print_exc()

# --- Content Extraction Endpoints ---

@router.post(
    "/content/extract",
    response_model=schemas.ContentExtractionResponse,
    tags=["Content Extraction"],
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "cnn_article": {
                            "summary": "Extract CNN Article",
                            "value": {
                                "url": "https://www.cnn.com/2024/01/15/politics/example-news-article"
                            }
                        },
                        "bbc_article": {
                            "summary": "Extract BBC Article",
                            "value": {
                                "url": "https://www.bbc.com/news/world-12345678"
                            }
                        },
                        "local_news": {
                            "summary": "Extract Local News Article",
                            "value": {
                                "url": "https://www.localnews.com/articles/breaking-news-story"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def extract_content(
    request: schemas.ContentExtractionRequest,
    user: dict = Depends(get_current_user),
):
    """
    Extract content from a news article URL.
    
    This endpoint extracts the main content, metadata, and images from news articles
    using multiple extraction strategies to ensure the best possible results.
    
    **Features:**
    - Extracts title, content, author, and publication date
    - Handles various news website formats (CNN, BBC, local news sites)
    - Returns clean, readable text without ads or navigation
    - Provides meaningful error messages for inaccessible URLs
    - Extraction completes within 10 seconds
    - Supports both HTTP and HTTPS URLs
    - Uses multiple extraction strategies for reliability
    
    **Error Handling:**
    - Invalid URL format → Returns 400 with clear error message
    - Non-existent URLs (404) → Returns appropriate error
    - Timeout errors → Returns timeout message
    - Extraction failures → Returns detailed error information
    """
    try:
        result = await content_extraction_service.extract_content(request.url)
        
        if result['status'] == 'error':
            error_info = result['error']
            if error_info['code'] == 'INVALID_URL':
                raise HTTPException(status_code=400, detail=error_info['message'])
            elif error_info['code'] == 'HTTP_ERROR':
                raise HTTPException(status_code=502, detail=error_info['message'])
            elif error_info['code'] == 'TIMEOUT':
                raise HTTPException(status_code=504, detail=error_info['message'])
            elif error_info['code'] == 'EXTRACTION_FAILED':
                raise HTTPException(status_code=422, detail=error_info['message'])
            else:
                raise HTTPException(status_code=500, detail=error_info['message'])
        
        return schemas.ContentExtractionResponse(
            status="success",
            data=schemas.ExtractedContent(**result['data'])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in content extraction: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred during content extraction. Please try again."
        )

async def delayed_background_processing(
    analysis_id: str,
    user_id: str,
    content: str,
    analysis_types: List[str],
    preset: str,
    options: schemas.AnalysisOptions,
    url: Optional[str] = None,
    jwt_token: Optional[str] = None
):
    """Add a realistic delay before processing analysis."""
    # Wait 2-5 seconds to simulate realistic processing time
    await asyncio.sleep(3)
    await process_analysis_background(
        analysis_id=analysis_id,
        user_id=user_id,
        content=content,
        analysis_types=analysis_types,
        preset=preset,
        options=options,
        url=url,
        jwt_token=jwt_token
    )

@router.post("/analyses/{analysis_id}/process", tags=["Analysis"])
async def trigger_analysis_processing(
    analysis_id: str,
    auth_data: dict = Depends(get_current_user_with_token)
):
    """
    Manual trigger for analysis processing (useful for testing).
    This endpoint allows forcing the processing of a pending analysis.
    """
    user = auth_data["user"]
    user_id = getattr(user, 'id', 'user-123')
    
    # Get the analysis from database
    analysis_data = await database_service.get_analysis(analysis_id, user_id, auth_data["token"])
    
    if not analysis_data:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if analysis_data["data"]["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Analysis is not pending (current status: {analysis_data['data']['status']})")
    
    # Get the real content and metadata from database
    db_data = await database_service.get_analysis_content_and_metadata(analysis_id, user_id, auth_data["token"])
    
    if not db_data:
        raise HTTPException(status_code=500, detail="Could not retrieve analysis content from database")
    
    content = db_data["content"]
    preset = db_data["preset"]
    url = db_data["url"]
    analysis_types = db_data["analysis_types"]
    
    if not content:
        raise HTTPException(status_code=500, detail="No content found for analysis")
    
    # Create options based on stored analysis types
    options = schemas.AnalysisOptions(
        includeBiasAnalysis="bias" in analysis_types,
        includeSentimentAnalysis="sentiment" in analysis_types,
        includeFactCheck="factCheck" in analysis_types,
        includeClaimExtraction="claimExtraction" in analysis_types,
        includeSourceCredibility="sourceCredibility" in analysis_types,
        includeExecutiveSummary="executiveSummary" in analysis_types
    )
    
    # Start background processing
    asyncio.create_task(
        process_analysis_background(
            analysis_id=analysis_id,
            user_id=user_id,
            content=content,
            analysis_types=analysis_types,
            preset=preset,
            options=options,
            url=url,
            jwt_token=auth_data["token"]
        )
    )
    
    return {
        "status": "success",
        "message": "Analysis processing triggered",
        "analysisId": analysis_id,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@router.get("/health", response_model=schemas.HealthResponse)
async def health_check():
    """
    Health check endpoint.
    """
    # Test OpenAI connectivity
    openai_status = "unknown"
    try:
        # Simple test call to OpenAI
        test_result = await openai_service.get_executive_summary("Test health check", "general")
        openai_status = "healthy" if test_result else "error"
    except Exception as e:
        print(f"[ERROR] OpenAI health check failed: {e}")
        openai_status = "error"
    
    return {
        "status": "success",
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "openai_status": openai_status
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
    
    # Check if we got any valid results from OpenAI
    valid_results = [v for v in results_dict.values() if v is not None]
    if not valid_results and tasks:
        # All OpenAI calls failed, raise error instead of returning generic results
        raise HTTPException(status_code=500, detail="Analysis failed - OpenAI services unavailable")
    
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
            # Filter out failed fact-check results
            fact_check_results = [result for result in fact_check_results if result is not None]
    
    # Calculate overall analysis score
    analysis_score = openai_service.calculate_analysis_score(results_dict)
    
    processing_time = time.time() - start_time
    
    # Build comprehensive results
    comprehensive_results = schemas.ComprehensiveAnalysisResults(
        executiveSummary=results_dict.get("executiveSummary"),  # No fallback
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
    auth_data: dict = Depends(get_current_user_with_token)
):
    """
    Get analysis results for a specific analysis ID (unified format).
    This endpoint returns results in the new comprehensive format.
    """
    user = auth_data["user"]
    jwt_token = auth_data["token"]
    user_id = getattr(user, 'id', 'user-123')
    
    # Retrieve analysis from database
    analysis_data = await database_service.get_analysis(analysis_id, user_id, jwt_token)
    
    if not analysis_data:
        raise HTTPException(
            status_code=404, 
            detail=f"Analysis with ID '{analysis_id}' not found. This analysis may not exist or may not have been completed yet."
        )
    
    return analysis_data

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
    auth_data: dict = Depends(get_current_user_with_token),
):
    """
    Unified analysis endpoint that handles both comprehensive and legacy analysis types.
    Supports both async and sync modes based on the request configuration.
    """
    import asyncio  # Import asyncio at the function level for both sync and async paths
    
    start_time = time.time()
    
    user = auth_data["user"]
    jwt_token = auth_data["token"]
    user_id = getattr(user, 'id', 'user-123')
    
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
    
    # Convert options to analysis types list
    analysis_types = []
    if request.options.includeBiasAnalysis:
        analysis_types.append("bias")
    if request.options.includeSentimentAnalysis:
        analysis_types.append("sentiment")
    if request.options.includeFactCheck:
        analysis_types.append("factCheck")
    if request.options.includeClaimExtraction:
        analysis_types.append("claimExtraction")
    if request.options.includeExecutiveSummary:
        analysis_types.append("executiveSummary")
    
    # If async mode is requested, return immediately with task status
    if request.async_mode:
        # Store initial analysis record in database
        await database_service.create_analysis(
            analysis_id=analysis_id,
            user_id=user_id,
            content=content,
            analysis_types=analysis_types,
            content_type=analysis_type,
            preset=request.preset,
            jwt_token=jwt_token,
            title=request.title,
            url=request.url,
            article_id=article_id
        )
        
        # Start background processing with a small delay to simulate realistic processing
        asyncio.create_task(
            delayed_background_processing(
                analysis_id=analysis_id,
                user_id=user_id,
                content=content,
                analysis_types=analysis_types,
                preset=request.preset,
                options=request.options,
                url=request.url,
                jwt_token=jwt_token
            )
        )
        
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
    
    # Check if we got any valid results from OpenAI
    valid_results = [v for v in results_dict.values() if v is not None]
    if not valid_results and tasks:
        # All OpenAI calls failed, raise error instead of returning generic results
        raise HTTPException(status_code=500, detail="Analysis failed - OpenAI services unavailable")
    
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
            # Filter out failed fact-check results
            fact_check_results = [result for result in fact_check_results if result is not None]
    
    # Calculate overall analysis score
    analysis_score = openai_service.calculate_analysis_score(results_dict)
    
    processing_time = time.time() - start_time
    
    # Build comprehensive results
    comprehensive_results = schemas.ComprehensiveAnalysisResults(
        executiveSummary=results_dict.get("executiveSummary"),  # No fallback
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

@router.post("/analyses/{analysis_id}/test-complete", tags=["Analysis"])
async def test_complete_analysis(
    analysis_id: str,
    auth_data: dict = Depends(get_current_user_with_token)
):
    """
    Test endpoint to mark an analysis as completed with mock results.
    This helps debug database update issues.
    """
    user = auth_data["user"]
    user_id = getattr(user, 'id', 'user-123')
    
    # Simple mock results that should be JSON serializable
    mock_results = {
        "executiveSummary": "Test endpoint - analysis marked as completed for debugging purposes.",
        "biasAnalysis": None,
        "sentimentAnalysis": None,
        "claimsExtracted": [],
        "factCheckResults": [],
        "sourceCredibility": None,
        "analysisScore": 75.0
    }
    
    try:
        success = await database_service.update_analysis_status(
            analysis_id=analysis_id,
            user_id=user_id,
            status="completed",
            results=mock_results,
            jwt_token=auth_data["token"]
        )
        
        if success:
            return {
                "status": "success",
                "message": "Analysis marked as completed (test)",
                "analysisId": analysis_id,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update analysis status")
            
    except Exception as e:
        print(f"[ERROR] Test complete failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database update error: {str(e)}")

# --- RSS News Feed Endpoints ---

@router.get(
    "/news-feed",
    response_model=schemas.NewsFeedResponse,
    tags=["News Feed"],
    summary="Get news feed articles",
    description="Retrieve paginated news articles from RSS feeds and manual submissions"
)
async def get_news_feed(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of articles per page"),
    rss_only: bool = Query(default=False, description="Show only RSS-collected articles"),
    source: Optional[str] = Query(default=None, description="Filter by source name"),
    search: Optional[str] = Query(default=None, description="Search in title and summary"),
    user: dict = Depends(get_current_user),
):
    """
    Get paginated news feed with filtering options.
    
    - **page**: Page number (starts from 1)
    - **limit**: Number of articles per page (1-100)
    - **rss_only**: If true, only show RSS-collected articles
    - **source**: Filter by source name (partial match)
    - **search**: Search term for title and summary
    """
    try:
        from app.services.rss_collection_service import rss_collection_service
        
        result = await rss_collection_service.get_news_feed(
            page=page,
            limit=limit,
            rss_only=rss_only,
            source=source,
            search=search
        )
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting news feed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get news feed: {str(e)}")

@router.post(
    "/news-feed/articles/{article_id}/extract-content",
    response_model=schemas.ContentExtractionResponse,
    tags=["News Feed"],
    summary="Extract full content for RSS article",
    description="Extract and store full content for an RSS article using URL extraction"
)
async def extract_rss_article_content(
    article_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Extract full content for an RSS article.
    
    This endpoint:
    1. Gets the article URL from the database
    2. Extracts full content using the content extraction service
    3. Updates the article with the extracted content and images
    4. Returns the extracted content
    """
    try:
        from app.services.rss_collection_service import rss_collection_service
        
        result = await rss_collection_service.extract_article_content(article_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Article not found or content extraction failed")
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting content for article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Content extraction failed: {str(e)}")

@router.post(
    "/news-feed/articles/{article_id}/analyze",
    response_model=schemas.AnalysisResultsResponse,
    tags=["News Feed"],
    summary="Analyze RSS article",
    description="Start analysis for an RSS article"
)
async def analyze_rss_article(
    article_id: str,
    request: schemas.RSSArticleAnalysisRequest,
    auth_data: dict = Depends(get_current_user_with_token),
):
    """
    Analyze an RSS article.
    
    This endpoint:
    1. Gets the article from the database
    2. Extracts content if needed
    3. Starts the analysis process
    4. Returns analysis results or status
    """
    try:
        user = auth_data["user"]
        user_id = getattr(user, 'id', 'user-123')
        jwt_token = auth_data["token"]
        
        # Get article from database
        article = await database_service.fetch_one(
            "SELECT * FROM articles WHERE id = $1",
            article_id
        )
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Use article content or extract if needed
        content = article['content']
        
        # If content is just the title placeholder, extract full content
        if content and "(Click to read full article)" in content:
            from app.services.rss_collection_service import rss_collection_service
            extracted = await rss_collection_service.extract_article_content(article_id)
            if extracted:
                content = extracted['content']
        
        if not content or len(content.strip()) < 100:
            raise HTTPException(status_code=400, detail="Article content too short for analysis")
        
        analysis_id = str(uuid.uuid4())
        
        # Convert options to analysis types list
        analysis_types = []
        if request.options.includeBiasAnalysis:
            analysis_types.append("bias")
        if request.options.includeSentimentAnalysis:
            analysis_types.append("sentiment")
        if request.options.includeFactCheck:
            analysis_types.append("factCheck")
        if request.options.includeClaimExtraction:
            analysis_types.append("claimExtraction")
        if request.options.includeExecutiveSummary:
            analysis_types.append("executiveSummary")
        
        # Store initial analysis record
        await database_service.create_analysis(
            analysis_id=analysis_id,
            user_id=user_id,
            content=content,
            analysis_types=analysis_types,
            content_type="article",
            preset=request.preset,
            jwt_token=jwt_token,
            title=article['title'],
            url=article['url'],
            article_id=article_id
        )
        
        # Update article analysis status
        await database_service.execute_query(
            "UPDATE articles SET analysis_status = $1, analysis_id = $2 WHERE id = $3",
            "pending",
            analysis_id,
            article_id
        )
        
        # Start background processing
        asyncio.create_task(
            process_analysis_background(
                analysis_id=analysis_id,
                user_id=user_id,
                content=content,
                analysis_types=analysis_types,
                preset=request.preset,
                options=request.options,
                url=article['url'],
                jwt_token=jwt_token
            )
        )
        
        return {
            "status": "success",
            "data": {
                "analysisId": analysis_id,
                "articleId": article_id,
                "analysisType": "article",
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get(
    "/news-feed/sources",
    response_model=schemas.RSSSourcesResponse,
    tags=["News Feed"],
    summary="Get available RSS sources",
    description="Get list of configured RSS news sources"
)
async def get_rss_sources(user: dict = Depends(get_current_user)):
    """Get list of available RSS sources."""
    try:
        from app.services.rss_collection_service import rss_collection_service
        
        sources = rss_collection_service.get_available_sources()
        
        return {
            "status": "success",
            "data": {
                "sources": sources,
                "total": len(sources)
            },
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting RSS sources: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sources: {str(e)}")

# Admin endpoints for RSS management
@router.post(
    "/admin/rss/collect",
    response_model=schemas.RSSCollectionResponse,
    tags=["Admin"],
    summary="Trigger RSS collection",
    description="Manually trigger RSS feed collection (admin only)"
)
async def trigger_rss_collection(user: dict = Depends(get_current_user)):
    """Manually trigger RSS collection from all feeds."""
    try:
        from app.services.rss_collection_service import rss_collection_service
        
        stats = await rss_collection_service.collect_all_feeds()
        
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in RSS collection: {e}")
        raise HTTPException(status_code=500, detail=f"RSS collection failed: {str(e)}")

@router.get(
    "/admin/scheduler/status",
    tags=["Admin"],
    summary="Get scheduler status",
    description="Get status of background scheduler jobs"
)
async def get_scheduler_status(user: dict = Depends(get_current_user)):
    """Get status of background scheduler."""
    try:
        from app.services.scheduler_service import scheduler_service
        
        status = scheduler_service.get_job_status()
        
        return {
            "status": "success",
            "data": status,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}") 