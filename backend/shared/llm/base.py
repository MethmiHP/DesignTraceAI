from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        pass