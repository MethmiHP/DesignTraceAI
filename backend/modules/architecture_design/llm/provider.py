"""
LLM Provider – Architecture Decision Agent M7.3.

Provides:
- BaseLLMProvider
- GeminiLLMProvider with retry + exponential backoff
- ExternalModelProviderError for exhausted transient failures
- StubLLMProvider for deterministic offline tests
"""

from __future__ import annotations

import logging
import os
import re
import time
from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel


logger = logging.getLogger(__name__)


class ExternalModelProviderError(RuntimeError):
    """
    Raised when an external LLM provider remains unavailable
    after retry attempts have been exhausted.

    Only safe metadata is exposed to higher layers.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code


class BaseLLMProvider(ABC):
    """Abstract interface for LLM operations."""

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
    ) -> BaseModel:
        """Generate a validated structured LLM response."""


class GeminiLLMProvider(BaseLLMProvider):
    """
    Gemini provider using google-genai.

    Temporary failures are retried using exponential backoff.

    Retryable examples:
    - 429 rate limit / resource exhausted
    - 500 provider internal error
    - 502 bad gateway
    - 503 unavailable
    - 504 timeout
    - temporary connection failures
    """

    RETRYABLE_STATUS_CODES = {
        429,
        500,
        502,
        503,
        504,
    }

    RETRYABLE_ERROR_MARKERS = (
        "servererror",
        "serviceunavailable",
        "unavailable",
        "resource_exhausted",
        "resourceexhausted",
        "rate limit",
        "rate_limit",
        "too many requests",
        "temporarily unavailable",
        "internal server error",
        "bad gateway",
        "gateway timeout",
        "connection reset",
        "connection aborted",
        "connection error",
        "timeout",
    )

    NON_RETRYABLE_ERROR_MARKERS = (
        "api key",
        "api_key",
        "authentication",
        "permission denied",
        "permission_denied",
        "invalid argument",
        "invalid_argument",
        "model not found",
    )

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        max_retries: int = 3,
        initial_retry_delay: float = 2.0,
        max_retry_delay: float = 8.0,
    ) -> None:
        self.model_name = (
            model_name
            or os.environ.get(
                "ARCHITECTURE_LLM_MODEL",
                "gemini-3.5-flash-lite",
            )
        )

        self.max_retries = max(
            0,
            max_retries,
        )

        self.initial_retry_delay = max(
            0.0,
            initial_retry_delay,
        )

        self.max_retry_delay = max(
            self.initial_retry_delay,
            max_retry_delay,
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
                "GEMINI_API_KEY environment variable is missing."
            )

        self.client = genai.Client(
            api_key=resolved_api_key
        )

        self.types = types

    def _extract_status_code(
        self,
        exc: Exception,
    ) -> int | None:
        """
        Best-effort extraction of an HTTP status code
        from google-genai exceptions.
        """

        for attribute_name in (
            "status_code",
            "code",
        ):
            value = getattr(
                exc,
                attribute_name,
                None,
            )

            if isinstance(
                value,
                int,
            ):
                return value

            if isinstance(
                value,
                str,
            ):
                match = re.search(
                    r"\b(4\d\d|5\d\d)\b",
                    value,
                )

                if match:
                    return int(
                        match.group(1)
                    )

        match = re.search(
            r"\b(400|401|403|404|408|409|429|500|502|503|504)\b",
            str(exc),
        )

        if match:
            return int(
                match.group(1)
            )

        return None

    def _is_retryable_exception(
        self,
        exc: Exception,
    ) -> bool:
        """
        Return True only for failures that are likely temporary.
        """

        exception_name = (
            type(exc).__name__.lower()
        )

        exception_text = (
            str(exc).lower()
        )

        combined = (
            f"{exception_name} "
            f"{exception_text}"
        )

        # Permanent configuration/authentication failures
        # should fail immediately.
        if any(
            marker in combined
            for marker
            in self.NON_RETRYABLE_ERROR_MARKERS
        ):
            return False

        status_code = (
            self._extract_status_code(
                exc
            )
        )

        if (
            status_code
            in self.RETRYABLE_STATUS_CODES
        ):
            return True

        if any(
            marker in combined
            for marker
            in self.RETRYABLE_ERROR_MARKERS
        ):
            return True

        return False

    def _generate_once(
        self,
        prompt: str,
        schema: Type[BaseModel],
    ) -> BaseModel:
        """Execute one Gemini request."""

        response = (
            self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.0,
                ),
            )
        )

        if not response.text:
            raise ValueError(
                "LLM returned an empty response."
            )

        return schema.model_validate_json(
            response.text
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
    ) -> BaseModel:
        """
        Generate structured Gemini output.

        Maximum attempts with max_retries=3:

        attempt 1
        retry after 2 seconds
        retry after 4 seconds
        retry after 8 seconds
        """

        retry_count = 0

        retry_delay = (
            self.initial_retry_delay
        )

        while True:
            try:
                return self._generate_once(
                    prompt,
                    schema,
                )

            except Exception as exc:
                retryable = (
                    self._is_retryable_exception(
                        exc
                    )
                )

                status_code = (
                    self._extract_status_code(
                        exc
                    )
                )

                # Permanent errors should not be retried.
                if not retryable:
                    logger.error(
                        "Gemini request failed with "
                        "non-retryable error type=%s "
                        "status=%s",
                        type(exc).__name__,
                        status_code,
                    )

                    raise

                # Retries already exhausted.
                if (
                    retry_count
                    >= self.max_retries
                ):
                    logger.error(
                        "Gemini temporary failure persisted "
                        "after %s retries. "
                        "type=%s status=%s",
                        self.max_retries,
                        type(exc).__name__,
                        status_code,
                    )

                    raise ExternalModelProviderError(
                        (
                            "Gemini remained temporarily "
                            "unavailable after retry attempts."
                        ),
                        status_code=status_code,
                    ) from exc

                retry_count += 1

                logger.warning(
                    "Gemini temporary failure. "
                    "type=%s status=%s "
                    "retry=%s/%s delay=%.1fs",
                    type(exc).__name__,
                    status_code,
                    retry_count,
                    self.max_retries,
                    retry_delay,
                )

                time.sleep(
                    retry_delay
                )

                retry_delay = min(
                    retry_delay * 2,
                    self.max_retry_delay,
                )


class StubLLMProvider(
    BaseLLMProvider
):
    """
    Deterministic offline provider used by tests.
    """

    model_name: str = "stub"

    def __init__(
        self,
        canned_response: BaseModel | None = None,
    ) -> None:
        self.canned_response = (
            canned_response
        )

        self.model_name = "stub"

    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
    ) -> BaseModel:

        if (
            self.canned_response
            is not None
            and isinstance(
                self.canned_response,
                schema,
            )
        ):
            return self.canned_response

        if (
            schema.__name__
            == "ArchitectureRecommendation"
        ):
            style_match = re.search(
                r"1\.\s+([A-Za-z\- ]+?)\s+\(",
                prompt,
            )

            selected_style = (
                style_match.group(1).strip()
                if style_match
                else "Event-Driven Architecture"
            )

            score_match = re.search(
                r"1\..*?Score:\s+([0-9.]+)",
                prompt,
                re.DOTALL,
            )

            score = (
                float(
                    score_match.group(1)
                )
                if score_match
                else 85.0
            )

            data = {
                "selected_style":
                    selected_style,

                "score":
                    score,

                "rationale":
                    "Automated stub rationale.",

                "key_quality_attributes": [
                    "Scalability"
                ],

                "strengths": [
                    "Test strength"
                ],

                "weaknesses": [
                    "Test weakness"
                ],

                "tradeoffs": [
                    "Test tradeoff"
                ],

                "rejected_alternatives":
                    [],

                "evidence_ids": [
                    "KB-001"
                ],

                "review_required":
                    False,
            }

            return schema.model_validate(
                data
            )

        if (
            schema.__name__
            == "HighLevelArchitectureDesign"
        ):
            data = {
                "style":
                    "Event-Driven Architecture",

                "components": [
                    {
                        "component_id":
                            "event_broker",

                        "name":
                            "Event Broker",

                        "responsibility":
                            "Pub/Sub message router",

                        "component_type":
                            "queue",

                        "grounding_type":
                            "architecture_structural",

                        "related_requirements":
                            [],

                        "related_quality_attributes":
                            [
                                "Scalability",
                                "Reliability",
                            ],
                    }
                ],

                "connections":
                    [],

                "design_rationale":
                    "Automated stub design.",

                "evidence_ids": [
                    "KB-001"
                ],
            }

            return schema.model_validate(
                data
            )

        raise NotImplementedError(
            "StubLLMProvider doesn't know "
            f"how to mock schema "
            f"{schema.__name__}"
        )