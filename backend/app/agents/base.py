import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from ..config import settings

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all AI agents with LLM integration and fallback logic."""

    def __init__(self):
        self.client = None
        if settings.openai_api_key:
            try:
                self.client = OpenAI(api_key=settings.openai_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Call LLM with system and user prompts."""
        if not self.client:
            raise ValueError("OpenAI client not initialized. Please set OPENAI_API_KEY.")

        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature or settings.llm_temperature,
                max_tokens=max_tokens or settings.llm_max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM, handling markdown code blocks."""
        try:
            # Remove markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}\nResponse: {response}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")

    def _validate_spec(self, spec: Dict[str, Any], required_keys: list) -> bool:
        """Validate that spec contains required keys."""
        for key in required_keys:
            if key not in spec:
                logger.error(f"Missing required key in spec: {key}")
                return False
        return True
