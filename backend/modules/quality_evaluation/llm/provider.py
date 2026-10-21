import logging
import os

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from .activity_logging import log_provider_call, log_fallback


logger = logging.getLogger(__name__)


T = TypeVar(
    "T",
    bound=BaseModel,
)


class QualityLLMUnavailableError(
    RuntimeError
):
    pass


class BaseQualityLLMProvider(ABC):

    name: str = "unknown"

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema_class: type[T],
    ) -> T:
        raise NotImplementedError


class GeminiQualityLLMProvider(
    BaseQualityLLMProvider
):

    name = "gemini"

    def __init__(
        self,
        model_name: str | None = None,
    ):

        api_key = os.environ.get(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise QualityLLMUnavailableError(
                "GEMINI_API_KEY is not configured."
            )

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise QualityLLMUnavailableError(
                (
                    "google-genai package is "
                    "not installed."
                )
            ) from exc

        self._types = types

        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=60000,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )

        self.model_name = (
            model_name
            or os.environ.get(
                "QUALITY_GEMINI_MODEL",
                "gemini-3.8-flash",
            )
        )

    @log_provider_call
    def generate_structured(
        self,
        prompt: str,
        schema_class: type[T],
    ) -> T:

        try:
            response = (
                self.client
                .models
                .generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=(
                        self._types
                        .GenerateContentConfig(
                            response_mime_type=(
                                "application/json"
                            ),
                            response_schema=(
                                schema_class
                            ),
                            temperature=0.1,
                        )
                    ),
                )
            )

            if not response.text:
                raise QualityLLMUnavailableError(
                    (
                        "Gemini returned an empty "
                        "response."
                    )
                )

            return (
                schema_class
                .model_validate_json(
                    response.text
                )
            )

        except Exception as exc:
            raise QualityLLMUnavailableError(
                (
                    "Gemini quality evaluation "
                    "request failed."
                )
            ) from exc


class GroqQualityLLMProvider(
    BaseQualityLLMProvider
):

    name = "groq"

    def __init__(
        self,
        model_name: str | None = None,
    ):

        api_key = os.environ.get(
            "GROQ_API_KEY"
        )

        if not api_key:
            raise QualityLLMUnavailableError(
                "GROQ_API_KEY is not configured."
            )

        try:
            from groq import Groq
        except ImportError as exc:
            raise QualityLLMUnavailableError(
                (
                    "groq package is "
                    "not installed."
                )
            ) from exc

        self.client = Groq(
            api_key=api_key, timeout=60.0, max_retries=0,
        )

        self.model_name = (
            model_name
            or os.environ.get(
                "QUALITY_GROQ_MODEL",
                "openai/gpt-oss-20b",
            )
        )

    @log_provider_call
    def generate_structured(
        self,
        prompt: str,
        schema_class: type[T],
    ) -> T:

        try:
            completion = (
                self.client
                .chat
                .completions
                .create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    temperature=0.1,
                    max_completion_tokens=1024,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": (
                                schema_class
                                .__name__
                            ),
                            "schema": (
                                schema_class
                                .model_json_schema()
                            ),
                        },
                    },
                )
            )

            content = (
                completion
                .choices[0]
                .message
                .content
            )

            if not content:
                raise QualityLLMUnavailableError(
                    (
                        "Groq returned an empty "
                        "response."
                    )
                )

            return (
                schema_class
                .model_validate_json(
                    content
                )
            )

        except Exception as exc:
            raise QualityLLMUnavailableError(
                (
                    "Groq quality evaluation "
                    "request failed."
                )
            ) from exc


class FallbackQualityLLMProvider(
    BaseQualityLLMProvider
):

    name = "fallback"

    def __init__(
        self,
        providers: list[
            BaseQualityLLMProvider
        ],
    ):

        if not providers:
            raise QualityLLMUnavailableError(
                (
                    "No LLM providers were "
                    "configured."
                )
            )

        self.providers = providers

        self.last_provider_name: (
            str | None
        ) = None

    def generate_structured(
        self,
        prompt: str,
        schema_class: type[T],
    ) -> T:

        self.last_provider_name = None
        for index, provider in enumerate(self.providers):

            try:
                result = (
                    provider
                    .generate_structured(
                        prompt,
                        schema_class,
                    )
                )

                self.last_provider_name = (
                    provider.name
                )

                return result

            except Exception:
                if index + 1 < len(self.providers):
                    log_fallback(provider.name, self.providers[index + 1].name)

        raise QualityLLMUnavailableError(
            (
                "All configured quality "
                "LLM providers failed."
            )
        )


def build_default_quality_llm_provider(
) -> BaseQualityLLMProvider:

    primary = os.environ.get(
        "QUALITY_LLM_PRIMARY_PROVIDER",
        "gemini",
    ).strip().lower()

    provider_names = [
        primary,
    ]

    for provider_name in [
        "gemini",
        "groq",
    ]:
        if provider_name not in provider_names:
            provider_names.append(
                provider_name
            )

    providers: list[
        BaseQualityLLMProvider
    ] = []

    for provider_name in provider_names:

        try:

            if provider_name == "gemini":
                if os.environ.get(
                    "GEMINI_API_KEY"
                ):
                    providers.append(
                        GeminiQualityLLMProvider()
                    )

            elif provider_name == "groq":
                if os.environ.get(
                    "GROQ_API_KEY"
                ):
                    providers.append(
                        GroqQualityLLMProvider()
                    )

        except Exception:
            logger.exception(
                (
                    "Could not initialize "
                    "quality LLM provider %s."
                ),
                provider_name,
            )

    if not providers:
        raise QualityLLMUnavailableError(
            (
                "No usable quality LLM "
                "provider is configured."
            )
        )

    if len(providers) == 1:
        return providers[0]

    return FallbackQualityLLMProvider(
        providers
    )
