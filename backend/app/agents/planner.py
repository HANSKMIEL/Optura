import logging
from typing import Dict, Any, List
from .base import BaseAgent
from ..prompts.planner import PLANNER_SYSTEM_PROMPT, PLANNER_USER_TEMPLATE

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """Agent that converts project goals into structured task plans."""

    def generate_plan(
        self,
        project_name: str,
        goal: str,
        description: str,
        acceptance_criteria: List[str],
        environment: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a structured plan with tasks and dependencies.
        Falls back to deterministic plan if OpenAI is not available.
        """
        if not self.client:
            logger.warning("OpenAI not available, using deterministic fallback")
            return self._fallback_plan(project_name, goal, description)

        try:
            user_prompt = PLANNER_USER_TEMPLATE.format(
                project_name=project_name,
                goal=goal,
                description=description,
                acceptance_criteria="\n".join(f"- {c}" for c in acceptance_criteria) if acceptance_criteria else "N/A",
                environment=environment or "Not specified"
            )

            response = self._call_llm(PLANNER_SYSTEM_PROMPT, user_prompt)
            plan = self._parse_json_response(response)

            # Validate plan structure
            if not self._validate_spec(plan, ["tasks", "risk_level"]):
                logger.warning("Invalid plan structure, using fallback")
                return self._fallback_plan(project_name, goal, description)

            return plan

        except Exception as e:
            logger.error(f"Plan generation failed: {e}, using fallback")
            return self._fallback_plan(project_name, goal, description)

    def _fallback_plan(self, project_name: str, goal: str, description: str) -> Dict[str, Any]:
        """Deterministic fallback when LLM is unavailable."""
        return {
            "tasks": [
                {
                    "name": "Research and Requirements",
                    "description": f"Analyze requirements for: {goal}",
                    "inputs": {"requirements": description},
                    "outputs": {"specification": "Detailed requirements document"},
                    "tests": [{"type": "review", "description": "Stakeholder review of requirements"}],
                    "security_checks": [],
                    "estimate_hours": 2.0,
                    "order": 0,
                    "requires_approval": True,
                    "confidence_score": 0.7,
                    "dependencies": []
                },
                {
                    "name": "Implementation",
                    "description": f"Implement solution for: {goal}",
                    "inputs": {"specification": "Requirements document"},
                    "outputs": {"code": "Working implementation"},
                    "tests": [
                        {"type": "unit", "description": "Unit tests for core functionality"},
                        {"type": "integration", "description": "Integration tests"}
                    ],
                    "security_checks": [{"type": "code_review", "description": "Security code review"}],
                    "estimate_hours": 4.0,
                    "order": 1,
                    "requires_approval": False,
                    "confidence_score": 0.6,
                    "dependencies": [0]
                },
                {
                    "name": "Testing and Validation",
                    "description": "Run comprehensive tests and validation",
                    "inputs": {"code": "Implementation"},
                    "outputs": {"test_results": "Test reports"},
                    "tests": [
                        {"type": "e2e", "description": "End-to-end testing"},
                        {"type": "integration", "description": "Full system integration test"}
                    ],
                    "security_checks": [{"type": "vulnerability_scan", "description": "Security vulnerability scan"}],
                    "estimate_hours": 2.0,
                    "order": 2,
                    "requires_approval": True,
                    "confidence_score": 0.8,
                    "dependencies": [1]
                }
            ],
            "risk_level": "medium",
            "estimated_total_hours": 8.0
        }
