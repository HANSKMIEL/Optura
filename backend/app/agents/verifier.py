import logging
from typing import Dict, Any
from .base import BaseAgent
from ..prompts.verifier import VERIFIER_SYSTEM_PROMPT, VERIFIER_USER_TEMPLATE

logger = logging.getLogger(__name__)


class VerifierAgent(BaseAgent):
    """Agent that performs static analysis and security checks on artifacts."""

    def verify_artifact(
        self,
        filename: str,
        mime_type: str,
        size_bytes: int,
        file_content: str,
        task_name: str,
        task_description: str,
        expected_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify an artifact with static analysis and security checks.
        Falls back to basic checks if OpenAI is not available.
        """
        if not self.client:
            logger.warning("OpenAI not available, using deterministic fallback")
            return self._fallback_verification(filename, mime_type, file_content)

        try:
            # Truncate content if too large
            max_content_length = 8000
            truncated_content = file_content[:max_content_length]
            if len(file_content) > max_content_length:
                truncated_content += "\n... (content truncated)"

            user_prompt = VERIFIER_USER_TEMPLATE.format(
                filename=filename,
                mime_type=mime_type,
                size_bytes=size_bytes,
                file_content=truncated_content,
                task_name=task_name,
                task_description=task_description,
                expected_outputs=str(expected_outputs)
            )

            response = self._call_llm(VERIFIER_SYSTEM_PROMPT, user_prompt, temperature=0.3)
            verification = self._parse_json_response(response)

            # Validate verification structure
            required_keys = ["status", "overall_score", "checks"]
            if not self._validate_spec(verification, required_keys):
                logger.warning("Invalid verification structure, using fallback")
                return self._fallback_verification(filename, mime_type, file_content)

            return verification

        except Exception as e:
            logger.error(f"Verification failed: {e}, using fallback")
            return self._fallback_verification(filename, mime_type, file_content)

    def _fallback_verification(self, filename: str, mime_type: str, file_content: str) -> Dict[str, Any]:
        """Deterministic fallback verification when LLM is unavailable."""
        checks = []
        failed = 0
        warnings = 0

        # Basic security checks
        dangerous_patterns = {
            "hardcoded_secret": ["password", "api_key", "secret", "token"],
            "sql_injection": ["execute(", "executemany(", "raw_sql"],
            "command_injection": ["os.system", "subprocess.call", "eval(", "exec("],
            "xss": ["innerHTML", "dangerouslySetInnerHTML"]
        }

        for check_type, patterns in dangerous_patterns.items():
            for pattern in patterns:
                if pattern.lower() in file_content.lower():
                    checks.append({
                        "category": "security",
                        "check_name": check_type,
                        "status": "warning",
                        "severity": "high",
                        "message": f"Potential security issue: {check_type} pattern detected",
                        "location": filename,
                        "recommendation": f"Review usage of '{pattern}' for security implications"
                    })
                    warnings += 1

        # File size check
        if len(file_content) > 100000:
            checks.append({
                "category": "quality",
                "check_name": "file_size",
                "status": "warning",
                "severity": "low",
                "message": "Large file detected",
                "location": filename,
                "recommendation": "Consider splitting into smaller modules"
            })
            warnings += 1

        # If no issues found
        if not checks:
            checks.append({
                "category": "general",
                "check_name": "basic_validation",
                "status": "pass",
                "severity": "low",
                "message": "Basic validation passed",
                "location": filename,
                "recommendation": "None"
            })

        status = "pass" if failed == 0 else "fail" if warnings == 0 else "warning"

        return {
            "status": status,
            "overall_score": max(0.5, 1.0 - (failed * 0.2) - (warnings * 0.1)),
            "checks": checks,
            "summary": {
                "total_checks": len(checks),
                "passed": len([c for c in checks if c["status"] == "pass"]),
                "failed": failed,
                "warnings": warnings
            },
            "security_issues": [
                c for c in checks if c["category"] == "security"
            ],
            "recommendations": [
                "This is a basic automated verification",
                "Manual code review is recommended for production use"
            ]
        }
