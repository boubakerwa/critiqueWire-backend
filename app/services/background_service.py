import asyncio
import time
from typing import Dict, Any
from app.services.openai_service import openai_service
from app.services.database_service import database_service
from app.api.v1 import schemas

class BackgroundService:
    """Simple background service for processing async analyses."""
    
    def __init__(self):
        self.running_tasks = {}
    
    async def process_analysis_async(self, analysis_id: str, user_id: str, content: str, request_data: Dict[str, Any]):
        """
        Process an analysis asynchronously in the background.
        
        Args:
            analysis_id: The analysis ID to process
            user_id: The user ID
            content: The content to analyze
            request_data: The original request data
        """
        try:
            # Update status to processing
            await database_service.update_analysis_status(analysis_id, user_id, "processing")
            
            start_time = time.time()
            
            # Build analysis tasks based on options
            tasks = {}
            options = request_data.get("options", {})
            preset = request_data.get("preset", "general")
            
            if options.get("includeBiasAnalysis"):
                tasks["biasAnalysis"] = openai_service.get_comprehensive_bias_analysis(content, preset)
            
            if options.get("includeSentimentAnalysis"):
                tasks["sentimentAnalysis"] = openai_service.get_sentiment_analysis(content, preset)
            
            if options.get("includeClaimExtraction"):
                tasks["claimsExtracted"] = openai_service.extract_claims(content, preset)
            
            if options.get("includeSourceCredibility") and request_data.get("url"):
                tasks["sourceCredibility"] = openai_service.assess_source_credibility(request_data["url"])
            
            if options.get("includeExecutiveSummary"):
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
                # All OpenAI calls failed, mark as failed instead of returning generic results
                raise Exception("All OpenAI analysis tasks failed - no valid results obtained")
            
            # Handle fact-checking after claim extraction
            fact_check_results = []
            if options.get("includeFactCheck") and "claimsExtracted" in results_dict:
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
            
            # Update analysis with results
            await database_service.update_analysis_status(
                analysis_id, 
                user_id, 
                "completed", 
                comprehensive_results.model_dump()
            )
            
            # Remove from running tasks
            if analysis_id in self.running_tasks:
                del self.running_tasks[analysis_id]
                
        except Exception as e:
            # Update status to failed
            await database_service.update_analysis_status(analysis_id, user_id, "failed")
            
            # Remove from running tasks
            if analysis_id in self.running_tasks:
                del self.running_tasks[analysis_id]
            
            print(f"Background analysis failed for {analysis_id}: {e}")
    
    def start_analysis_task(self, analysis_id: str, user_id: str, content: str, request_data: Dict[str, Any]):
        """
        Start an analysis task in the background.
        
        Args:
            analysis_id: The analysis ID to process
            user_id: The user ID
            content: The content to analyze
            request_data: The original request data
        """
        # Create and start the background task
        task = asyncio.create_task(
            self.process_analysis_async(analysis_id, user_id, content, request_data)
        )
        
        # Store the task reference
        self.running_tasks[analysis_id] = task
        
        return task
    
    def get_task_status(self, analysis_id: str):
        """
        Get the status of a running task.
        
        Args:
            analysis_id: The analysis ID
            
        Returns:
            Task status or None if not found
        """
        if analysis_id in self.running_tasks:
            task = self.running_tasks[analysis_id]
            if task.done():
                return "completed"
            elif task.cancelled():
                return "cancelled"
            else:
                return "running"
        return None

# Create a singleton instance
background_service = BackgroundService() 