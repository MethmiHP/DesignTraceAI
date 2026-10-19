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

        return {
            "requirements": [
                {
                    "original_text":
                        "The system shall respond within 2 seconds.",

                    "normalized_statement":
                        "The system shall respond within 2 seconds.",

                    "requirement_type":
                        "NFR",

                    "quality_attribute":
                        "Performance",

                    "asr":
                        True,

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