# Gemini client used only by the Requirement Analysis module.
#
# This keeps the Requirement Analysis component independent from
# shared.llm while preserving the same retry, timeout, and structured
# JSON generation behavior.

import json
from typing import Any

from google import genai
from google.genai import types

from shared.config import settings


class RequirementGeminiClient:

    def __init__(self):

        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,

            http_options=types.HttpOptions(
                timeout=60000,

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

        self.model_name = (
            settings.LLM_MODEL
        )


    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:

        response = await (
            self.client.aio.models.generate_content(

                model=
                    self.model_name,

                contents=
                    prompt,

                config=
                    types.GenerateContentConfig(
                        temperature=
                            temperature
                    ),
            )
        )

        if not response.text:

            raise ValueError(
                "Gemini returned an empty response."
            )

        return response.text


    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
    ) -> dict[str, Any]:

        response = await (
            self.client.aio.models.generate_content(

                model=
                    self.model_name,

                contents=
                    prompt,

                config=
                    types.GenerateContentConfig(

                        temperature=
                            temperature,

                        response_mime_type=
                            "application/json",

                        response_schema=
                            response_schema,
                    ),
            )
        )

        if not response.text:

            raise ValueError(
                "Gemini returned an empty "
                "structured response."
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
            dict,
        ):

            raise ValueError(
                "Gemini structured response "
                "must be a JSON object."
            )


        return result


def get_requirement_llm_client():

    return RequirementGeminiClient()