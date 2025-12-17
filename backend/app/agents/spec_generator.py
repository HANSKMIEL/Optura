import logging
from typing import Dict, Any
from .base import BaseAgent
from ..prompts.spec_generator import SPEC_SYSTEM_PROMPT, SPEC_USER_TEMPLATE

logger = logging.getLogger(__name__)


class SpecGeneratorAgent(BaseAgent):
    """Agent that creates detailed, machine-readable specifications for tasks."""

    def generate_spec(
        self,
        task_name: str,
        task_description: str,
        project_context: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        tests: list
    ) -> Dict[str, Any]:
        """
        Generate a detailed specification for a task.
        Falls back to deterministic spec if OpenAI is not available.
        """
        if not self.client:
            logger.warning("OpenAI not available, using deterministic fallback")
            return self._fallback_spec(task_name, task_description, inputs, outputs, tests)

        try:
            user_prompt = SPEC_USER_TEMPLATE.format(
                task_name=task_name,
                task_description=task_description,
                project_context=project_context,
                inputs=str(inputs),
                outputs=str(outputs),
                tests=str(tests)
            )

            response = self._call_llm(SPEC_SYSTEM_PROMPT, user_prompt)
            spec = self._parse_json_response(response)

            # Validate spec structure
            required_keys = ["task_name", "objective", "inputs", "outputs", "test_cases"]
            if not self._validate_spec(spec, required_keys):
                logger.warning("Invalid spec structure, using fallback")
                return self._fallback_spec(task_name, task_description, inputs, outputs, tests)

            return spec

        except Exception as e:
            logger.error(f"Spec generation failed: {e}, using fallback")
            return self._fallback_spec(task_name, task_description, inputs, outputs, tests)

    def _fallback_spec(
        self,
        task_name: str,
        task_description: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        tests: list
    ) -> Dict[str, Any]:
        """Deterministic fallback when LLM is unavailable."""
        return {
            "task_name": task_name,
            "objective": task_description,
            "inputs": {
                key: {
                    "type": "any",
                    "description": value if isinstance(value, str) else str(value),
                    "validation": [],
                    "example": ""
                }
                for key, value in inputs.items()
            } if inputs else {},
            "outputs": {
                key: {
                    "type": "any",
                    "description": value if isinstance(value, str) else str(value),
                    "example": ""
                }
                for key, value in outputs.items()
            } if outputs else {},
            "test_cases": [
                {
                    "name": f"Test {i+1}",
                    "type": test.get("type", "unit") if isinstance(test, dict) else "unit",
                    "inputs": {},
                    "expected_output": {},
                    "expected_behavior": test.get("description", str(test)) if isinstance(test, dict) else str(test)
                }
                for i, test in enumerate(tests)
            ] if tests else [],
            "edge_cases": [],
            "security_requirements": [],
            "implementation_notes": [
                "This is a fallback specification generated without LLM assistance",
                "Please review and enhance with specific implementation details"
            ],
            "confidence_score": 0.5
        }
