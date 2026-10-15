"""
Vector Store – Milestone 3.

Design:
  BaseVectorStore    : abstract contract → replaceable (ChromaDB, Pinecone later).
  InMemoryVectorStore: cosine similarity using numpy only.
                       Zero external dependencies — works in any CI environment.

SearchResult carries the document id, its metadata, and the cosine similarity
score so callers never need to touch raw vectors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

@dataclass
class SearchResult:
    doc_id:    str
    score:     float            # cosine similarity in [0, 1]
    metadata:  Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Abstract base – the plug-in point for future vector stores
# ---------------------------------------------------------------------------

class BaseVectorStore(ABC):
    """
    All vector stores must implement add_documents() and search().
    The retriever depends only on this interface.
    """

    @abstractmethod
    def add_documents(
        self,
        ids:        List[str],
        embeddings: List[List[float]],
        metadata:   List[Dict[str, Any]],
    ) -> None:
        """
        Index a batch of documents.

        Args:
            ids:        Unique identifier for each document.
            embeddings: Pre-computed embedding vectors (one per doc).
            metadata:   Arbitrary metadata dict stored alongside each vector.
        """

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[SearchResult]:
        """
        Return the top-k most similar documents.

        Args:
            query_embedding: Embedding of the query string.
            top_k:           Maximum number of results to return.

        Returns:
            List of SearchResult ordered by descending cosine similarity score.
        """


# ---------------------------------------------------------------------------
# In-memory cosine similarity implementation (no external dependencies)
# ---------------------------------------------------------------------------

class InMemoryVectorStore(BaseVectorStore):
    """
    Lightweight in-memory vector store using numpy cosine similarity.

    Suitable for the prototype and CI testing. All data is held in RAM
    and not persisted between process restarts.
    """

    def __init__(self) -> None:
        self._ids:        List[str]               = []
        self._embeddings: np.ndarray | None       = None   # shape (N, D)
        self._metadata:   List[Dict[str, Any]]    = []

    # ------------------------------------------------------------------
    # BaseVectorStore interface
    # ------------------------------------------------------------------

    def add_documents(
        self,
        ids:        List[str],
        embeddings: List[List[float]],
        metadata:   List[Dict[str, Any]],
    ) -> None:
        if not ids:
            return
        self._ids.extend(ids)
        self._metadata.extend(metadata)

        matrix = np.array(embeddings, dtype=np.float32)
        if self._embeddings is None:
            self._embeddings = matrix
        else:
            self._embeddings = np.vstack([self._embeddings, matrix])

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[SearchResult]:
        if self._embeddings is None or len(self._ids) == 0:
            return []

        q = np.array(query_embedding, dtype=np.float32)

        # Cosine similarity: dot product of normalised vectors
        q_norm = np.linalg.norm(q)
        q_unit = q / q_norm if q_norm > 0 else q

        norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
        # Avoid division by zero for zero-norm rows
        norms = np.where(norms == 0, 1e-9, norms)
        doc_units = self._embeddings / norms

        scores: np.ndarray = doc_units @ q_unit          # shape (N,)

        # Clamp to [0, 1] — cosine can be slightly negative for unrelated items
        scores = np.clip(scores, 0.0, 1.0)

        k = min(top_k, len(self._ids))
        top_indices = np.argsort(scores)[::-1][:k]

        return [
            SearchResult(
                doc_id   = self._ids[i],
                score    = float(scores[i]),
                metadata = self._metadata[i],
            )
            for i in top_indices
        ]
