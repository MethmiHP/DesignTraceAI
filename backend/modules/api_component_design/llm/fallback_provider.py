"""Ordered, lazy LLM fallback. The service owns the final baseline fallback."""
import logging
from time import perf_counter

from pydantic import BaseModel

from .provider import BaseLLMProvider, GeminiLLMProvider, LLMUnavailableError, T
from .groq_provider import GroqLLMProvider
from .activity_logging import failure_reason, requirement_context

logger = logging.getLogger(__name__)


class FallbackLLMProvider(BaseLLMProvider):
    def __init__(self, providers=None):
        # Factories delay key/SDK checks until the provider is actually needed.
        self.providers = providers if providers is not None else [
            ('Gemini', GeminiLLMProvider),
            ('Groq', GroqLLMProvider),
        ]

    def generate_structured(self, prompt: str, schema_class: type[T]) -> T:
        result, _ = self.generate_structured_with_source(prompt, schema_class)
        return result

    def generate_structured_with_source(self, prompt: str, schema_class: type[T]):
        failures = []
        requirement = requirement_context.get()
        previous = None
        for name, factory in self.providers:
            if previous is not None:
                logger.info('[API %s] %s -> %s', requirement, previous.lower(), name.lower())
            started = perf_counter()
            logger.info('[API %s] %s started', requirement, name.lower())
            try:
                provider = factory()
                try:
                    result = provider.generate_structured(prompt, schema_class)
                    # Validate again at the boundary, including injected providers.
                    if isinstance(result, BaseModel):
                        result = result.model_dump()
                    validated = schema_class.model_validate(result, strict=True)
                finally:
                    close = getattr(provider, 'close', None)
                    if close is not None:
                        close()
                logger.info('[API %s] %s OK (%.1fs)', requirement, name.lower(), perf_counter() - started)
                return validated, name.lower() if name.lower() in {"gemini", "groq"} else "llm"
            except Exception as exc:
                # Do not log prompts, keys, raw output, or provider response bodies.
                failures.append(f'{name}: {type(exc).__name__}')
                logger.warning('[API %s] %s failed: %s', requirement, name.lower(), failure_reason(exc))
                previous = name
        raise LLMUnavailableError('All configured LLM providers failed: ' + '; '.join(failures))
