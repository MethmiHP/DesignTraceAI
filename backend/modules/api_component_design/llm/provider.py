import os

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel


T = TypeVar(
    "T",
    bound=BaseModel,
)


class LLMUnavailableError(RuntimeError):
    """The provider remains unavailable after transient-error retries."""


class BaseLLMProvider(ABC):
    provider_name = "llm"

    def generate_structured_with_source(self, prompt: str, schema_class: type[T]):
        return self.generate_structured(prompt, schema_class), self.provider_name

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema_class: type[T],
    ) -> T:
        """
        Generate a structured response from an LLM
        and validate it using the supplied
        Pydantic schema.
        """
        raise NotImplementedError


class GeminiLLMProvider(
    BaseLLMProvider
):
    provider_name = "gemini"

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
    ):

        self.model_name = (
            model_name
            or os.environ.get(
                "API_COMPONENT_LLM_MODEL",
                "gemini-3.8-flash",
            )
        )


        try:

            from google import genai
            from google.genai import types

        except ImportError as exc:

            raise ImportError(
                "The 'google-genai' package is required "
                "to use GeminiLLMProvider. "
                "Run: pip install google-genai"
            ) from exc


        resolved_api_key = (
            api_key
            or os.environ.get(
                "GEMINI_API_KEY"
            )
        )


        if not resolved_api_key:

            raise ValueError(
                "GEMINI_API_KEY environment variable "
                "is missing."
            )


        self.client = genai.Client(
            api_key=resolved_api_key,
            http_options=types.HttpOptions(
                timeout=30000,
                retry_options=types.HttpRetryOptions(
                    attempts=4,
                    initial_delay=2.0,
                    max_delay=8.0,
                    exp_base=2.0,
                    jitter=1.0,
                    http_status_codes=[429, 500, 502, 503, 504],
                ),
            ),
        )

        self.types = types


    def generate_structured(
        self,
        prompt: str,
        schema_class: type[T],
    ) -> T:

        from google.genai.errors import APIError

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=(
                    self.types
                    .GenerateContentConfig(
                        response_mime_type=(
                            "application/json"
                        ),
                        response_schema=(
                            schema_class
                        ),
                        temperature=0.0,
                    )
                ),
            )
        except APIError as exc:
            if exc.code in (429, 500, 502, 503, 504):
                raise LLMUnavailableError(
                    f"Gemini model '{self.model_name}' is temporarily "
                    f"unavailable (HTTP {exc.code}) after retries. "
                    "Please try again later. For HTTP 429, also check "
                    "your API quota."
                ) from exc
            raise


        if not response.text:

            raise ValueError(
                "LLM returned an empty response."
            )


        return (
            schema_class
            .model_validate_json(
                response.text
            )
        )


    def close(self):
        self.client.close()
