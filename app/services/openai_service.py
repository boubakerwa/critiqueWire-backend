from openai import AsyncOpenAI
from app.core.config import settings
from app.api.v1 import schemas
import json
import datetime
import uuid
from pydantic import ValidationError
from urllib.parse import urlparse
from typing import List, Dict, Any, Union, Optional

class OpenAIService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            print("[ERROR] OPENAI_API_KEY is not set!")
        else:
            print(f"[DEBUG] OpenAI API key configured: {settings.OPENAI_API_KEY[:10]}...")
        
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"

    async def _analyze(self, article_text: str, system_prompt: str, response_model):
        """
        A generic method to call the OpenAI API for analysis and validate the response.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": article_text},
                ],
            )
            response_json = json.loads(response.choices[0].message.content)
            return response_model.model_validate(response_json)
        except (json.JSONDecodeError, ValidationError, IndexError) as e:
            print(f"[ERROR] OpenAI analysis parsing error: {e}")
            print(f"[ERROR] Response content: {response.choices[0].message.content if 'response' in locals() else 'No response'}")
            return None
        except Exception as e:
            print(f"[ERROR] OpenAI API error: {type(e).__name__}: {e}")
            # More specific error information
            if hasattr(e, 'status_code'):
                print(f"[ERROR] HTTP Status Code: {e.status_code}")
            if hasattr(e, 'response'):
                print(f"[ERROR] Response: {e.response}")
            import traceback
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
            return None

    def _get_system_prompt(self, task_description: str, response_model, preset: str = "general") -> str:
        """
        Creates a standardized system prompt for a given task with preset-specific instructions.
        """
        schema = response_model.model_json_schema()
        
        # Preset-specific instructions
        preset_instructions = {
            "general": "Provide balanced, objective analysis suitable for general audiences.",
            "political": "Focus on political implications, bias detection, partisan language, and policy impacts. Pay special attention to loaded language and political framing.",
            "financial": "Emphasize market implications, economic indicators, financial data accuracy, and business impact. Focus on quantitative claims and market sentiment.",
            "scientific": "Prioritize scientific accuracy, methodology assessment, peer review status, and evidence quality. Evaluate statistical claims and research validity.",
            "opinion": "Distinguish between factual claims and opinions. Analyze argumentative structure, logical fallacies, and persuasive techniques."
        }
        
        preset_instruction = preset_instructions.get(preset, preset_instructions["general"])
        
        return (
            f"You are a world-class expert analysis engine specialized in journalistic content analysis. "
            f"Your task is to {task_description}. "
            f"Analysis preset: {preset.upper()} - {preset_instruction} "
            "Analyze the provided article text and return your analysis. "
            "Your response must be a JSON object that strictly adheres to the following JSON Schema. "
            "Do not include any other explanatory text in your response, only the JSON object.\n\n"
            f"JSON Schema:\n{json.dumps(schema, indent=2)}"
        )

    # --- Legacy Methods (Backward Compatibility) ---

    async def get_bias_analysis(self, text: str) -> Union[schemas.BiasAnalysisResult, None]:
        prompt = self._get_system_prompt(
            "perform a bias analysis", schemas.BiasAnalysisResult
        )
        return await self._analyze(text, prompt, schemas.BiasAnalysisResult)

    async def get_fact_check(self, text: str) -> Union[schemas.FactCheckResultLegacy, None]:
        prompt = self._get_system_prompt(
            "perform a fact-check", schemas.FactCheckResultLegacy
        )
        return await self._analyze(text, prompt, schemas.FactCheckResultLegacy)

    async def get_context_analysis(self, text: str) -> Union[schemas.ContextAnalysisResult, None]:
        prompt = self._get_system_prompt(
            "perform a contextual analysis", schemas.ContextAnalysisResult
        )
        return await self._analyze(text, prompt, schemas.ContextAnalysisResult)

    async def get_summary(self, text: str) -> Union[schemas.SummaryResult, None]:
        prompt = self._get_system_prompt(
            "provide a comprehensive summary", schemas.SummaryResult
        )
        return await self._analyze(text, prompt, schemas.SummaryResult)

    async def get_expert_opinion(self, text: str) -> Union[schemas.ExpertOpinionResult, None]:
        prompt = self._get_system_prompt(
            "provide an expert opinion as if you were a domain expert on the topic",
            schemas.ExpertOpinionResult,
        )
        return await self._analyze(text, prompt, schemas.ExpertOpinionResult)

    async def get_impact_assessment(self, text: str) -> Union[schemas.ImpactAssessmentResult, None]:
        prompt = self._get_system_prompt(
            "provide a detailed impact assessment",
            schemas.ImpactAssessmentResult,
        )
        return await self._analyze(text, prompt, schemas.ImpactAssessmentResult)

    # --- v0.2 Comprehensive Analysis Methods ---

    async def get_comprehensive_bias_analysis(self, text: str, preset: str = "general") -> Union[schemas.BiasAnalysisResult, None]:
        """Enhanced bias analysis with preset-specific focus."""
        prompt = self._get_system_prompt(
            "perform a comprehensive bias analysis with detailed scoring and examples", 
            schemas.BiasAnalysisResult, 
            preset
        )
        return await self._analyze(text, prompt, schemas.BiasAnalysisResult)

    async def get_sentiment_analysis(self, text: str, preset: str = "general") -> Union[schemas.SentimentAnalysisResult, None]:
        """Analyze sentiment and emotional tone of the content."""
        prompt = self._get_system_prompt(
            "perform a detailed sentiment analysis including emotional tone indicators", 
            schemas.SentimentAnalysisResult, 
            preset
        )
        return await self._analyze(text, prompt, schemas.SentimentAnalysisResult)

    async def extract_claims(self, text: str, preset: str = "general") -> List[schemas.ExtractedClaim]:
        """Extract and categorize key claims from the content."""
        
        # Custom schema for claim extraction
        class ClaimsResponse(schemas.BaseModel):
            claims: List[schemas.ExtractedClaim]
        
        prompt = self._get_system_prompt(
            "extract and categorize all significant claims from the text, assigning unique IDs and importance levels", 
            ClaimsResponse, 
            preset
        )
        
        result = await self._analyze(text, prompt, ClaimsResponse)
        return result.claims if result else []

    async def fact_check_claim(self, claim: str, claim_id: str) -> Union[schemas.FactCheckResult, None]:
        """Fact-check a specific claim."""
        
        # Create a custom prompt for individual claim fact-checking
        prompt = (
            f"You are an expert fact-checker. Analyze the following claim and provide a detailed fact-check assessment. "
            f"Claim ID: {claim_id}\n"
            f"Claim: {claim}\n\n"
            "Your response must be a JSON object that strictly adheres to the following JSON Schema. "
            "Do not include any other explanatory text in your response, only the JSON object.\n\n"
            f"JSON Schema:\n{json.dumps(schemas.FactCheckResult.model_json_schema(), indent=2)}"
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Fact-check this claim: {claim}"},
                ],
            )
            response_json = json.loads(response.choices[0].message.content)
            # Ensure the claim ID is set correctly
            response_json["claimId"] = claim_id
            return schemas.FactCheckResult.model_validate(response_json)
        except Exception as e:
            print(f"[ERROR] Claim fact-checking error: {type(e).__name__}: {e}")
            if hasattr(e, 'status_code'):
                print(f"[ERROR] HTTP Status Code: {e.status_code}")
            import traceback
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
            return None

    async def assess_source_credibility(self, url: str) -> Union[schemas.SourceCredibilityResult, None]:
        """Assess the credibility of a news source or website."""
        
        domain = urlparse(url).netloc
        
        # Create a comprehensive credibility assessment prompt
        prompt = (
            f"You are an expert media literacy analyst. Assess the credibility of the news source: {domain} "
            f"Consider factors like transparency, accuracy history, bias patterns, ownership, and editorial standards. "
            f"URL being assessed: {url}\n\n"
            "Your response must be a JSON object that strictly adheres to the following JSON Schema. "
            "Do not include any other explanatory text in your response, only the JSON object.\n\n"
            f"JSON Schema:\n{json.dumps(schemas.SourceCredibilityResult.model_json_schema(), indent=2)}"
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Assess the credibility of {domain} based on the URL: {url}"},
                ],
            )
            response_json = json.loads(response.choices[0].message.content)
            
            # Ensure required fields are set
            response_json["url"] = url
            response_json["domain"] = domain
            response_json["lastUpdated"] = datetime.datetime.utcnow().isoformat()
            
            return schemas.SourceCredibilityResult.model_validate(response_json)
        except Exception as e:
            print(f"[ERROR] Credibility assessment error: {type(e).__name__}: {e}")
            if hasattr(e, 'status_code'):
                print(f"[ERROR] HTTP Status Code: {e.status_code}")
            import traceback
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
            return None

    async def get_executive_summary(self, text: str, preset: str = "general") -> str:
        """Generate an executive summary of the analysis findings."""
        
        class SummaryResponse(schemas.BaseModel):
            summary: str
        
        prompt = self._get_system_prompt(
            "create a concise executive summary highlighting the key findings and insights from the analysis", 
            SummaryResponse, 
            preset
        )
        
        result = await self._analyze(text, prompt, SummaryResponse)
        return result.summary if result else "Analysis completed successfully."

    def calculate_analysis_score(self, results_dict: Dict[str, Any]) -> float:
        """Calculate an overall analysis score based on the results."""
        
        score = 0.0
        factors = 0
        
        # Bias analysis score (lower bias = higher score)
        if "biasAnalysis" in results_dict and results_dict["biasAnalysis"]:
            bias_score = (1.0 - results_dict["biasAnalysis"].score) * 100
            score += bias_score
            factors += 1
        
        # Sentiment confidence
        if "sentimentAnalysis" in results_dict and results_dict["sentimentAnalysis"]:
            sentiment_score = results_dict["sentimentAnalysis"].confidence * 100
            score += sentiment_score
            factors += 1
        
        # Fact-check confidence (average of all fact-checks)
        if "factCheckResults" in results_dict and results_dict["factCheckResults"]:
            fact_check_scores = [fc.confidence * 100 for fc in results_dict["factCheckResults"]]
            if fact_check_scores:
                avg_fact_score = sum(fact_check_scores) / len(fact_check_scores)
                score += avg_fact_score
                factors += 1
        
        # Source credibility
        if "sourceCredibility" in results_dict and results_dict["sourceCredibility"]:
            score += results_dict["sourceCredibility"].credibilityScore
            factors += 1
        
        # Claims extraction quality (more claims with higher importance = higher score)
        if "claimsExtracted" in results_dict and results_dict["claimsExtracted"]:
            claims = results_dict["claimsExtracted"]
            if claims:
                importance_weights = {"high": 3, "medium": 2, "low": 1}
                claim_score = sum(importance_weights.get(claim.importance, 1) for claim in claims)
                # Normalize to 0-100 scale (assume max 10 high-importance claims)
                normalized_claim_score = min(claim_score / 30 * 100, 100)
                score += normalized_claim_score
                factors += 1
        
        # Return average score or default
        return round(score / factors, 1) if factors > 0 else 75.0

    # --- Utility Methods ---

    def get_preset_configuration(self, preset: str) -> Dict[str, Any]:
        """Get the configuration for a specific analysis preset."""
        
        configurations = {
            "general": {
                "focus_areas": ["objectivity", "accuracy", "clarity"],
                "bias_sensitivity": "medium",
                "fact_check_depth": "standard"
            },
            "political": {
                "focus_areas": ["bias", "partisan_language", "policy_impact"],
                "bias_sensitivity": "high",
                "fact_check_depth": "thorough"
            },
            "financial": {
                "focus_areas": ["market_sentiment", "data_accuracy", "economic_indicators"],
                "bias_sensitivity": "medium",
                "fact_check_depth": "data_focused"
            },
            "scientific": {
                "focus_areas": ["methodology", "evidence_quality", "peer_review"],
                "bias_sensitivity": "low",
                "fact_check_depth": "research_focused"
            },
            "opinion": {
                "focus_areas": ["argument_structure", "logical_fallacies", "persuasion"],
                "bias_sensitivity": "high",
                "fact_check_depth": "claim_focused"
            }
        }
        
        return configurations.get(preset, configurations["general"])

openai_service = OpenAIService() 