class MockLLMClient:

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        return "Mock response"

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict,
        temperature: float = 0.0,
    ) -> dict:

        prompt_lower = prompt.lower()


        # Simple Functional Requirement
        if "users shall log in" in prompt_lower:
            return {
                "requirements": [
                    {
                        "original_text": "Users shall log in.",
                        "normalized_statement": "Users shall log in.",
                        "asr": False,
                        "quality_issues": {
                            "ambiguous": False,
                            "incomplete": False,
                            "conflicting": False,
                            "potentially_missing": False,
                        },
                        "issue_details": [],
                    }
                ]
            }


        # Security Non-Functional Requirement
        if "user data must be secure" in prompt_lower:
            return {
                "requirements": [
                    {
                        "original_text": "User data must be secure.",
                        "normalized_statement": "User data shall be secure.",
                        "asr": True,
                        "quality_issues": {
                            "ambiguous": True,
                            "incomplete": False,
                            "conflicting": False,
                            "potentially_missing": False,
                        },
                        "issue_details": [
                            {
                                "issue_type": "ambiguity",
                                "evidence": "secure",
                                "rationale": (
                                    "The term 'secure' is broad and does not "
                                    "specify the required security controls."
                                ),
                                "recommendation": (
                                    "Specify measurable security controls such as "
                                    "authentication, authorization, encryption, "
                                    "or access-control requirements."
                                ),
                            }
                        ],
                    }
                ]
            }


        # Performance Non-Functional Requirement
        if "respond within 2 seconds" in prompt_lower:
            return {
                "requirements": [
                    {
                        "original_text":
                            "The system shall respond within 2 seconds.",
                        "normalized_statement":
                            "The system shall respond within 2 seconds.",
                        "asr": True,
                        "quality_issues": {
                            "ambiguous": False,
                            "incomplete": False,
                            "conflicting": False,
                            "potentially_missing": False,
                        },
                        "issue_details": [],
                    }
                ]
            }

        # Architecturally Significant Requirement
        if "10,000 concurrent users" in prompt_lower:
            return {
                "requirements": [
                    {
                        "original_text":
                            "The system shall support 10,000 concurrent users.",
                        "normalized_statement":
                            "The system shall support 10,000 concurrent users.",
                        "asr": True,
                        "quality_issues": {
                            "ambiguous": False,
                            "incomplete": False,
                            "conflicting": False,
                            "potentially_missing": False,
                        },
                        "issue_details": [],
                    }
                ]
            }


        # Ambiguous Requirement
        if "easy to use" in prompt_lower:
            return {
                "requirements": [
                    {
                        "original_text":
                            "The system shall be easy to use.",
                        "normalized_statement":
                            "The system shall be easy to use.",
                        "asr": False,
                        "quality_issues": {
                            "ambiguous": True,
                            "incomplete": False,
                            "conflicting": False,
                            "potentially_missing": False,
                        },
                        "issue_details": [
                            {
                                "issue_type": "ambiguity",
                                "evidence": "easy to use",
                                "rationale": (
                                    "The phrase 'easy to use' is subjective "
                                    "and does not provide a measurable usability target."
                                ),
                                "recommendation": (
                                    "Define measurable usability criteria such as "
                                    "task completion time, error rate, or user satisfaction."
                                ),
                            }
                        ],
                    }
                ]
            }


        # Generic fallback used by the main integration test
        return {
            "requirements": [
                {
                    "original_text":
                        "The system shall respond within 2 seconds.",
                    "normalized_statement":
                        "The system shall respond within 2 seconds.",
                    "asr": True,
                    "quality_issues": {
                        "ambiguous": False,
                        "incomplete": False,
                        "conflicting": False,
                        "potentially_missing": False,
                    },
                    "issue_details": [],
                }
            ]
        }