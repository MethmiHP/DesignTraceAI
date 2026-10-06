from shared.config import settings

from .mock_client import MockLLMClient


def get_llm_provider():
    provider = settings.LLM_PROVIDER.lower()

    if provider == "mock":
        return MockLLMClient()

    if provider == "openai":
        from .openai_client import OpenAIClient
        return OpenAIClient()

    if provider == "gemini":
        from .gemini_client import GeminiClient
        return GeminiClient()

    raise ValueError(
        f"Unsupported LLM provider: {settings.LLM_PROVIDER}"
    )