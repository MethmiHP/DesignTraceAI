"""
Gemini implementation of the shared DesignTrace AI LLM provider.

The provider supports both plain-text generation and structured JSON
generation. Model name and API key are loaded through shared settings.
"""

import asyncio
import json
from typing import Any

from google import genai
from google.genai import types

from shared.config import settings
from shared.llm.base import LLMProvider


class GeminiClient(LLMProvider):
    """
    Shared Google Gemini provider used by DesignTrace AI modules.
    """

    MAX_RETRIES = 3

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        if not settings.LLM_MODEL:
            raise ValueError(
                "LLM_MODEL is not configured."
            )

        self.model = settings.LLM_MODEL

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        """
        Generate a normal text response.
        """

        response = await self._generate_with_retry(
            prompt=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
            ),
        )

        text = response.text

        if not text or not text.strip():
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return text.strip()

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """
        Generate structured JSON that follows the supplied schema.
        """

        response = await self._generate_with_retry(
            prompt=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
                response_json_schema=response_schema,
            ),
        )

        text = response.text

        if not text or not text.strip():
            raise RuntimeError(
                "Gemini returned an empty structured response."
            )

        try:
            parsed = json.loads(
                text
            )

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini returned invalid JSON."
            ) from exc

        if not isinstance(parsed, dict):
            raise RuntimeError(
                "Gemini structured response must be a JSON object."
            )

        return parsed

    async def _generate_with_retry(
        self,
        prompt: str,
        config: types.GenerateContentConfig,
    ):
        """
        Call Gemini with retry support for temporary provider failures.
        """

        last_error: Exception | None = None

        retry_delays = [
            2,
            4,
            8,
        ]

        for attempt in range(
            self.MAX_RETRIES
        ):
            try:
                return (
                    await self.client.aio.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=config,
                    )
                )

            except Exception as exc:
                last_error = exc

                if attempt >= (
                    self.MAX_RETRIES - 1
                ):
                    break

                await asyncio.sleep(
                    retry_delays[attempt]
                )

        raise RuntimeError(
            "Gemini generation failed after "
            f"{self.MAX_RETRIES} attempts: "
            f"{last_error}"
        ) from last_error