from openai import AsyncOpenAI
from app.core.config import settings
from app.api.v1 import schemas
import json
from pydantic import ValidationError

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"

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
            # TODO: Add more robust error handling and logging
            print(f"Error during OpenAI analysis: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def _get_system_prompt(self, task_description: str, response_model) -> str:
        """
        Creates a standardized system prompt for a given task.
        """
        schema = response_model.model_json_schema()
        return (
            f"You are a world-class expert analysis engine. Your task is to {task_description}. "
            "Analyze the provided article text and return your analysis. "
            "Your response must be a JSON object that strictly adheres to the following JSON Schema. "
            "Do not include any other explanatory text in your response, only the JSON object.\n\n"
            f"JSON Schema:\n{json.dumps(schema, indent=2)}"
        )

    async def get_bias_analysis(self, text: str) -> schemas.BiasAnalysis | None:
        prompt = self._get_system_prompt(
            "perform a bias analysis", schemas.BiasAnalysis
        )
        return await self._analyze(text, prompt, schemas.BiasAnalysis)

    async def get_fact_check(self, text: str) -> schemas.FactCheck | None:
        prompt = self._get_system_prompt(
            "perform a fact-check", schemas.FactCheck
        )
        return await self._analyze(text, prompt, schemas.FactCheck)

    async def get_context_analysis(self, text: str) -> schemas.ContextAnalysis | None:
        prompt = self._get_system_prompt(
            "perform a contextual analysis", schemas.ContextAnalysis
        )
        return await self._analyze(text, prompt, schemas.ContextAnalysis)

    async def get_summary(self, text: str) -> schemas.Summary | None:
        prompt = self._get_system_prompt(
            "provide a comprehensive summary", schemas.Summary
        )
        return await self._analyze(text, prompt, schemas.Summary)

    async def get_expert_opinion(self, text: str) -> schemas.ExpertOpinion | None:
        prompt = self._get_system_prompt(
            "provide an expert opinion as if you were a domain expert on the topic",
            schemas.ExpertOpinion,
        )
        return await self._analyze(text, prompt, schemas.ExpertOpinion)

    async def get_impact_assessment(self, text: str) -> schemas.ImpactAssessment | None:
        prompt = self._get_system_prompt(
            "provide a detailed impact assessment",
            schemas.ImpactAssessment,
        )
        return await self._analyze(text, prompt, schemas.ImpactAssessment)

openai_service = OpenAIService() 