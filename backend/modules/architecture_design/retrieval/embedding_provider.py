"""
Embedding Provider – Milestone 3.

Design:
  BaseEmbeddingProvider  : abstract contract → the plug-in point.
  SentenceTransformerEmbeddingProvider : concrete implementation using
       the sentence-transformers library.

Default model  : sentence-transformers/all-MiniLM-L6-v2  (~80 MB, CPU-friendly)
Alternate model: BAAI/bge-m3  (~570 MB, higher quality)
Both are swapped at construction time — no code change required.

The rest of the module (vector store, retriever) depends only on
BaseEmbeddingProvider, so the model can be replaced without touching them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


# ---------------------------------------------------------------------------
# Abstract base – the plug-in point
# ---------------------------------------------------------------------------

class BaseEmbeddingProvider(ABC):
    """
    All embedding providers must implement embed().
    Inputs : list of plain text strings
    Outputs: list of float vectors (one per input text)
    """

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: Non-empty list of strings to embed.

        Returns:
            List of float vectors, same length as `texts`.
            Each vector has the same dimensionality (model-dependent).
        """


# ---------------------------------------------------------------------------
# Sentence-Transformers implementation
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """
    Embedding provider backed by the sentence-transformers library.

    Args:
        model_name: HuggingFace model identifier.
                    Defaults to all-MiniLM-L6-v2 (small, CPU-friendly).
                    Set to 'BAAI/bge-m3' for higher quality embeddings.

    Usage:
        provider = SentenceTransformerEmbeddingProvider()
        vectors  = provider.embed(["text one", "text two"])
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model_name = model_name
        # Lazy import so that the rest of the module can be imported even if
        # sentence-transformers is not installed (tests can mock this class).
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer(model_name)
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for SentenceTransformerEmbeddingProvider. "
                "Install it with: pip install sentence-transformers"
            ) from exc

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using the loaded SentenceTransformer model.

        Returns:
            List of float vectors (numpy arrays converted to plain lists
            for JSON-compatibility and Pydantic compatibility).
        """
        raw = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return [vec.tolist() for vec in raw]


# ---------------------------------------------------------------------------
# Deterministic Stub Implementation (Testing & Offline Evaluation)
# ---------------------------------------------------------------------------

_VOCAB = [
    "scalability", "scale", "concurrent", "concurrent users", "horizontal",
    "microservices", "service", "independent",
    "availability", "uptime", "failover", "replicate",
    "reliability", "fault", "circuit", "resilient",
    "performance", "latency", "cache", "fast",
    "maintainability", "modular", "module", "refactor", "testable",
    "layered", "layer", "n-tier",
    "mvc", "controller", "view", "model",
    "event-driven", "event", "broker", "kafka", "async",
    "security", "authentication", "encrypt", "protect", "unauthorized",
]


def _text_to_vec(text: str) -> List[float]:
    import math
    lower = text.lower()
    vec = [1.0 if kw in lower else 0.0 for kw in _VOCAB]
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class StubEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic embedding provider for tests and evaluation. No network, no file I/O."""

    model_name: str = "stub-keyword-embedding"

    def __init__(self, model_name: str = "stub-keyword-embedding") -> None:
        self.model_name = model_name

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [_text_to_vec(t) for t in texts]

