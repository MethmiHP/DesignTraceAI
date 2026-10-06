from typing import Any

from .base import LLMProvider


class MockLLMClient(LLMProvider):

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        return "Mock response"

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
    ) -> dict[str, Any]:

        return {
            "service_id": "SVC-APT",
            "detailed_responsibility":
                "Reserve an available slot and create an appointment.",
            "method": "POST",
            "path": "/appointments",
        }