import logging
import json
import httpx
import os
from contextvars import ContextVar
from threading import Lock
from time import monotonic

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
        self._source = ContextVar(f'quality_source_{id(self)}', default=None)
        self._cooldown = {}
        self._lock = Lock()

    @property
    def last_provider_name(self):
        return self._source.get()

    @last_provider_name.setter
    def last_provider_name(self, value):
        self._source.set(value)

    def generate_structured(
        self,
        prompt: str,
        schema_class: type[T],
    ) -> T:

        self.last_provider_name = None
        with self._lock:
            healthy = [p for p in self.providers if self._cooldown.get(id(p), 0) <= monotonic()]
        # Try healthy providers first, but retain cooled providers as a last
        # resort so an outage does not remove a rule's chance of evaluation.
        providers = healthy + [p for p in self.providers if p not in healthy]
        for index, provider in enumerate(providers):

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

            except Exception as exc:
                root = exc
                seen = set()
                while root.__cause__ is not None and id(root) not in seen:
                    seen.add(id(root))
                    root = root.__cause__
                code = getattr(root, 'status_code', None) or getattr(root, 'code', None)
                if code in {429, 500, 502, 503, 504}:
                    delay = 60.0
                    headers = getattr(getattr(root, 'response', None), 'headers', {})
                    try:
                        delay = max(delay, float(headers.get('retry-after', 0)))
                    except (TypeError, ValueError):
                        pass
                    with self._lock:
                        self._cooldown[id(provider)] = monotonic() + delay
                    logger.info('%s cooling down; prefer available fallback', provider.name)
                if index + 1 < len(providers):
                    log_fallback(provider.name, providers[index + 1].name)

        raise QualityLLMUnavailableError(
            (
                "All configured quality "
                "LLM providers failed."
            )
        )


class DeepSeekQualityLLMProvider(BaseQualityLLMProvider):
    name = "deepseek"

    def __init__(self, model_name=None):
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not self.api_key:
            raise QualityLLMUnavailableError("DEEPSEEK_API_KEY is not configured.")
        self.model_name = model_name or os.environ.get("QUALITY_DEEPSEEK_MODEL", "deepseek-flash")

    @log_provider_call
    def generate_structured(self, prompt: str, schema_class: type[T]) -> T:
        instructions = (
            "Return only a JSON object matching this JSON Schema: "
            + json.dumps(schema_class.model_json_schema(), separators=(",", ":"))
            + '\nFormat example for insufficient evidence: '
            + '{"status":"SKIPPED","evidence":[],"rationale":"Insufficient design evidence.",'
              '"affected_nfr_ids":[],"confidence":null,"recommendation":null}'
            + "\nEvaluate the supplied evidence independently; do not copy the example verdict."
        )
        try:
            response = httpx.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": instructions},
                        {"role": "user", "content": prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 2048,
                    "temperature": 0.1,
                },
                timeout=httpx.Timeout(60.0, connect=5.0),
            )
            response.raise_for_status()
            choice = response.json()["choices"][0]
            if choice.get("finish_reason") != "stop":
                raise QualityLLMUnavailableError("DeepSeek response was incomplete.")
            content = choice["message"].get("content")
            if not content:
                raise QualityLLMUnavailableError("DeepSeek returned an empty response.")
            return schema_class.model_validate_json(content, strict=True)
        except Exception as exc:
            raise QualityLLMUnavailableError("DeepSeek quality evaluation request failed.") from exc


def build_default_quality_llm_provider() -> BaseQualityLLMProvider:
    # Temporary DeepSeek-only mode. Existing Gemini/Groq environment settings
    # and implementations are retained but never selected or used as fallbacks.
    return DeepSeekQualityLLMProvider()
