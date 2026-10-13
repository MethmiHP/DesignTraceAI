# Provides a mock LLM client for testing the Requirement Analysis Module
# by returning predefined text and structured requirement-analysis responses
# without calling a real LLM API.
from typing import Any

from .base import LLMProvider

class MockLLMClient(LLMProvider):

    async def generate(self, prompt: str, **kwargs):
        return "Mock response"

    async def generate_structured(self, prompt: str, **kwargs):

        prompt_lower = prompt.lower()

        # 1. Simple FR
        if "users shall log in" in prompt_lower:
            return {
                "requirements": [
                    {
                        "original_text": "Users shall log in.",
                        "normalized_statement": "Users shall log in.",
                        "requirement_type": "FR",
                        "quality_attribute": None,
                        "asr": False,
                        "quality_issues": {
                            "ambiguous": False,
                            "incomplete": False,
                            "conflicting": False,
                            "potentially_missing": False
                        },
                        "issue_details": [],
                        "confidence": 0.95
                    }
                ]
            }

        # 2. Security NFR
        if "user data must be secure" in prompt_lower:
            return {
                "requirements": [
                    {
                        "original_text": "User data must be secure.",
                        "normalized_statement": "User data must be secure.",
                        "requirement_type": "NFR",
                        "quality_attribute": "Security",
                        "asr": True,
                        "quality_issues": {
                            "ambiguous": True,
                            "incomplete": True,
                            "conflicting": False,
                            "potentially_missing": False
                        },
                        "issue_details": [],
                        "confidence": 0.92
                    }
                ]
            }

        # 3. Performance NFR
        if "respond within 2 seconds" in prompt_lower:
            return {
                "requirements": [
                    {
                        "original_text": "The system shall respond within 2 seconds.",
                        "normalized_statement": "The system shall respond within 2 seconds.",
                        "requirement_type": "NFR",
                        "quality_attribute": "Performance",
                        "asr": True,
                        "quality_issues": {
                            "ambiguous": False,
                            "incomplete": False,
                            "conflicting": False,
                            "potentially_missing": False
                        },
                        "issue_details": [],
                        "confidence": 0.98
                    }
                ]
            }

        # 4. Ambiguous performance NFR
        if "system should be fast" in prompt_lower:
            return {
                "requirements": [
                    {
                        "original_text": "The system should be fast.",
                        "normalized_statement": "The system should be fast.",
                        "requirement_type": "NFR",
                        "quality_attribute": "Performance",
                        "asr": False,
                        "quality_issues": {
                            "ambiguous": True,
                            "incomplete": True,
                            "conflicting": False,
                            "potentially_missing": False
                        },
                        "issue_details": [],
                        "confidence": 0.85
                    }
                ]
            }

        # 5. ASR scalability requirement
        if "10,000 concurrent users" in prompt_lower:
            return {
                "requirements": [
                    {
                        "original_text": "The system shall support 10,000 concurrent users.",
                        "normalized_statement": "The system shall support 10,000 concurrent users.",
                        "requirement_type": "NFR",
                        "quality_attribute": "Scalability",
                        "asr": True,
                        "quality_issues": {
                            "ambiguous": False,
                            "incomplete": False,
                            "conflicting": False,
                            "potentially_missing": False
                        },
                        "issue_details": [],
                        "confidence": 0.97
                    }
                ]
            }

        # Default response for your original test
        return {
            "requirements": [
                {
                    "original_text": "Patients should be able to register.",
                    "normalized_statement": "Patients shall be able to register.",
                    "requirement_type": "FR",
                    "quality_attribute": None,
                    "asr": False,
                    "quality_issues": {
                        "ambiguous": False,
                        "incomplete": False,
                        "conflicting": False,
                        "potentially_missing": False
                    },
                    "issue_details": [],
                    "confidence": 0.96
                }
            ]
        }