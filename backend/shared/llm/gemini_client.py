# Implements the asynchronous Gemini LLM provider for DesignTraceAI.
# The client supports normal text and schema-constrained JSON generation,
# includes timeout and retry handling for temporary API failures, and validates
# structured responses before returning them to the application.

import json
from typing import Any

from google import genai
from google.genai import types

from shared.config import settings
from shared.llm.base import LLMProvider


class GeminiClient(LLMProvider):

    def __init__(self):

        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,

            http_options=types.HttpOptions(
                # Timeout is in milliseconds.
                timeout=60000,

                # Automatically retry temporary API errors.
                retry_options=types.HttpRetryOptions(
                    attempts=5,
                    initial_delay=2.0,
                    exp_base=2.0,
                    max_delay=20.0,
                    http_status_codes=[
                        408,
                        429,
                        500,
                        502,
                        503,
                        504,
                    ],
                ),
            ),
        )

        self.model_name = settings.LLM_MODEL


    # NORMAL TEXT GENERATION

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0
    ) -> str:

        response = await (
            self.client.aio.models.generate_content(
                model=self.model_name,

                contents=prompt,

                config=types.GenerateContentConfig(
                    temperature=temperature
                ),
            )
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        return response.text


    # STRUCTURED JSON GENERATION

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0
    ) -> dict[str, Any]:

        response = await (
            self.client.aio.models.generate_content(
                model=self.model_name,

                contents=prompt,

                config=types.GenerateContentConfig(
                    temperature=temperature,

                    response_mime_type=
                        "application/json",

                    response_schema=
                        response_schema,
                ),
            )
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty structured response."
            )

        try:
            result = json.loads(
                response.text
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Gemini returned invalid JSON."
            ) from exc


        if not isinstance(
            result,
            dict
        ):
            raise ValueError(
                "Gemini structured response "
                "must be a JSON object."
            )


        return result