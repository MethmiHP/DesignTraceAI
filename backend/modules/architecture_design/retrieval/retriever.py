"""
Architecture Evidence Retriever – Milestone 3.

Orchestrates the full RAG pipeline:
  1. Load knowledge items (knowledge_loader)
  2. Embed all items once at construction time
  3. Index embeddings in the vector store
  4. On retrieve():
       a. Embed the query
       b. Search the vector store
       c. Map results back to RetrievedEvidence Pydantic models

Query builder:
  build_query(active_qas, top_styles, asr_statements) → str

  Combines:
    - active quality attribute names (those with count > 0)
    - names of top-ranked architecture styles
    - original ASR statement text

  Example:
    "Security Scalability Performance Reliability architecture
     Event-Driven Architecture Microservices
     Patient information shall be protected from unauthorized access.
     The system shall support 500 concurrent users..."
"""

from __future__ import annotations

from typing import List

from ..schemas import QualityProfile, RetrievedEvidence
from .embedding_provider import BaseEmbeddingProvider, SentenceTransformerEmbeddingProvider
from .knowledge_loader import KnowledgeItem, get_knowledge_items
from .vector_store import BaseVectorStore, InMemoryVectorStore


# ---------------------------------------------------------------------------
# Query builder (pure function – easy to test in isolation)
# ---------------------------------------------------------------------------

def build_query(
    active_qas:      List[str],
    top_styles:      List[str],
    asr_statements:  List[str],
) -> str:
    """
    Construct a retrieval query string from project context.

    Args:
        active_qas:     Quality attribute names with count > 0 (importance order).
        top_styles:     Top-ranked architecture style names (from M2 scoring).
        asr_statements: Original ASR requirement text strings.

    Returns:
        A single string query ready for embedding.
    """
    parts: List[str] = []

    if active_qas:
        parts.append(" ".join(active_qas))

    if top_styles:
        parts.append("architecture " + " ".join(top_styles))

    if asr_statements:
        parts.extend(asr_statements)

    return " ".join(parts).strip()


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------

class ArchitectureRetriever:
    """
    RAG retriever for architecture evidence.

    At construction time, all knowledge items are embedded and indexed
    into the vector store (one-time cost).  Subsequent retrieve() calls
    only embed the query — fast inference path.

    Args:
        embedding_provider: Embedding model wrapper. Defaults to
                            SentenceTransformerEmbeddingProvider
                            (all-MiniLM-L6-v2).
        vector_store:       Vector store implementation. Defaults to
                            InMemoryVectorStore (cosine, no external deps).
        knowledge_items:    Pre-loaded knowledge items (for DI in tests).
                            Defaults to the module-level cached items.
    """

    def __init__(
        self,
        embedding_provider: BaseEmbeddingProvider | None = None,
        vector_store:       BaseVectorStore | None       = None,
        knowledge_items:    List[KnowledgeItem] | None   = None,
    ) -> None:
        self._provider: BaseEmbeddingProvider = (
            embedding_provider or SentenceTransformerEmbeddingProvider()
        )
        self._store: BaseVectorStore = vector_store or InMemoryVectorStore()
        self._items: List[KnowledgeItem] = (
            knowledge_items if knowledge_items is not None else get_knowledge_items()
        )
        self._index()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedEvidence]:
        """
        Retrieve the most relevant knowledge items for the given query.

        Args:
            query: Free-text retrieval query (built by build_query()).
            top_k: Maximum number of evidence items to return.

        Returns:
            List of RetrievedEvidence ordered by descending relevance score.
        """
        if not query.strip() or not self._items:
            return []

        query_vec = self._provider.embed([query])[0]
        results   = self._store.search(query_vec, top_k=top_k)

        # Map search results back to knowledge items
        item_map = {item.knowledge_id: item for item in self._items}
        evidence: List[RetrievedEvidence] = []

        for result in results:
            item = item_map.get(result.doc_id)
            if item is None:
                continue
            evidence.append(
                RetrievedEvidence(
                    knowledge_id        = item.knowledge_id,
                    title               = item.title,
                    content             = item.content,
                    source              = item.source,
                    relevance_score     = round(result.score, 4),
                    architecture_styles = item.architecture_styles,
                    quality_attributes  = item.quality_attributes,
                )
            )

        return evidence

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _index(self) -> None:
        """Embed all knowledge items and add them to the vector store."""
        if not self._items:
            return

        texts     = [item.content for item in self._items]
        embeddings = self._provider.embed(texts)

        ids      = [item.knowledge_id for item in self._items]
        metadata = [
            {
                "title":               item.title,
                "architecture_styles": item.architecture_styles,
                "quality_attributes":  item.quality_attributes,
                "source":              item.source,
                "source_type":         item.source_type,
            }
            for item in self._items
        ]

        self._store.add_documents(ids=ids, embeddings=embeddings, metadata=metadata)
