"""
Tests for Architecture Decision Agent – Milestone 3 (RAG Evidence Retrieval).

Strategy
--------
All 9 tests use a STUB embedding provider (StubEmbeddingProvider) that
generates deterministic pseudo-embeddings from keyword matching — no model
download required, tests run in milliseconds.

The stub embeddings are designed so that:
  • "Scalability" / "Microservices" terms produce vectors that score highly
    against KB items tagged with those attributes.
  • "Maintainability" / "Modular Monolith" / "Layered" terms produce vectors
    that score highly against those items.

This keeps the tests fully deterministic while exercising the real retrieval
pipeline (knowledge loader, vector store, cosine similarity, schema validation).

Run all tests:
    cd d:\\4thYEAR\\Research\\DesignTraceAI\\backend
    pytest tests/ -v
"""

from __future__ import annotations

import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List

import pytest

from modules.architecture_design.retrieval.knowledge_loader import (
    KnowledgeItem,
    get_knowledge_items,
    load_knowledge,
)
from modules.architecture_design.retrieval.embedding_provider import (
    BaseEmbeddingProvider,
)
from modules.architecture_design.retrieval.vector_store import (
    InMemoryVectorStore,
)
from modules.architecture_design.retrieval.retriever import (
    ArchitectureRetriever,
    build_query,
)
from modules.architecture_design.schemas import (
    ASRBatch,
    ASRInput,
    RetrievalOutput,
    RetrievedEvidence,
)
from modules.architecture_design.service import ArchitectureDesignService


# ===========================================================================
# Stub embedding provider (deterministic, no model download)
# ===========================================================================

# Keyword vocabulary — each position in the embedding vector represents
# one keyword.  The score for a text is how many keywords it contains.
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
_DIM = len(_VOCAB)


def _text_to_vec(text: str) -> List[float]:
    """Convert text to a keyword-frequency vector (deterministic)."""
    lower = text.lower()
    vec = [1.0 if kw in lower else 0.0 for kw in _VOCAB]
    # L2-normalise
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class StubEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic embedding provider for tests. No network, no file I/O."""

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [_text_to_vec(t) for t in texts]


# ===========================================================================
# Shared fixtures
# ===========================================================================

@pytest.fixture(scope="module")
def knowledge_items() -> List[KnowledgeItem]:
    return get_knowledge_items()


@pytest.fixture(scope="module")
def retriever(knowledge_items: List[KnowledgeItem]) -> ArchitectureRetriever:
    return ArchitectureRetriever(
        embedding_provider=StubEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
        knowledge_items=knowledge_items,
    )


@pytest.fixture(scope="module")
def service(knowledge_items: List[KnowledgeItem]) -> ArchitectureDesignService:
    return ArchitectureDesignService(
        embedding_provider=StubEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
    )


@pytest.fixture
def sample_batch() -> ASRBatch:
    return ASRBatch(
        project_id="P001",
        asrs=[
            ASRInput(
                requirement_id="REQ-001",
                statement="Patient information shall be protected from unauthorized access.",
            ),
            ASRInput(
                requirement_id="REQ-002",
                statement="The system shall support 500 concurrent users with acceptable response time.",
            ),
            ASRInput(
                requirement_id="REQ-003",
                statement="The system shall remain operational even if one service fails.",
            ),
        ],
    )


# ===========================================================================
# Test 1 – Knowledge base loads and has the expected number of items
# ===========================================================================

def test_knowledge_base_loads(knowledge_items: List[KnowledgeItem]) -> None:
    assert len(knowledge_items) >= 20, (
        f"Expected at least 20 knowledge items, got {len(knowledge_items)}"
    )
    for item in knowledge_items:
        assert item.knowledge_id.startswith("KB-")
        assert item.title
        assert item.content
        assert item.source_type == "internal_seed"


# ===========================================================================
# Test 2 – Embeddings are generated for all items (correct count and shape)
# ===========================================================================

def test_embeddings_generated_for_all_items(
    knowledge_items: List[KnowledgeItem],
) -> None:
    provider = StubEmbeddingProvider()
    texts  = [item.content for item in knowledge_items]
    vecs   = provider.embed(texts)

    assert len(vecs) == len(knowledge_items), (
        "Expected one embedding per knowledge item"
    )
    first_dim = len(vecs[0])
    for i, vec in enumerate(vecs):
        assert len(vec) == first_dim, f"Inconsistent embedding dimension at item {i}"
        assert first_dim > 0


# ===========================================================================
# Test 3 – Retrieval returns at least one result
# ===========================================================================

def test_retrieval_returns_at_least_one_result(
    retriever: ArchitectureRetriever,
) -> None:
    results = retriever.retrieve("scalability microservices", top_k=5)
    assert len(results) >= 1, "Expected at least one retrieval result"
    assert isinstance(results[0], RetrievedEvidence)


# ===========================================================================
# Test 4 – top_k is respected
# ===========================================================================

def test_top_k_respected(retriever: ArchitectureRetriever) -> None:
    for k in [1, 3, 5]:
        results = retriever.retrieve("architecture scalability", top_k=k)
        assert len(results) <= k, f"top_k={k} violated: got {len(results)} results"


# ===========================================================================
# Test 5 – Evidence is ordered by descending relevance score
# ===========================================================================

def test_evidence_ordered_by_relevance(retriever: ArchitectureRetriever) -> None:
    results = retriever.retrieve("scalability microservices event driven", top_k=10)
    scores  = [ev.relevance_score for ev in results]
    assert scores == sorted(scores, reverse=True), (
        "Evidence is not ordered by descending relevance score"
    )


# ===========================================================================
# Test 6 – Scalability-heavy query returns Microservices or Event-Driven evidence
# ===========================================================================

def test_scalability_query_retrieves_microservices_or_event_driven_evidence(
    retriever: ArchitectureRetriever,
) -> None:
    results = retriever.retrieve(
        "scalability scale horizontal independent microservices service",
        top_k=5,
    )
    assert len(results) > 0

    target_styles = {"Microservices", "Event-Driven Architecture"}
    hit = any(
        bool(set(ev.architecture_styles) & target_styles)
        for ev in results
    )
    assert hit, (
        "Scalability-heavy query did not retrieve any Microservices or "
        f"Event-Driven evidence. Got: {[ev.title for ev in results]}"
    )


# ===========================================================================
# Test 7 – Maintainability-heavy query returns Modular Monolith or Layered evidence
# ===========================================================================

def test_maintainability_query_retrieves_modular_or_layered_evidence(
    retriever: ArchitectureRetriever,
) -> None:
    results = retriever.retrieve(
        "maintainability modular module refactor testable layered",
        top_k=5,
    )
    assert len(results) > 0

    target_styles = {"Modular Monolith", "Layered Architecture"}
    hit = any(
        bool(set(ev.architecture_styles) & target_styles)
        for ev in results
    )
    assert hit, (
        "Maintainability-heavy query did not retrieve Modular Monolith or "
        f"Layered evidence. Got: {[ev.title for ev in results]}"
    )


# ===========================================================================
# Test 8 – RetrievalOutput is Pydantic-valid and JSON round-trips
# ===========================================================================

def test_retrieval_output_pydantic_validation(
    service: ArchitectureDesignService,
    sample_batch: ASRBatch,
) -> None:
    output = service.retrieve_evidence(sample_batch, top_k=5)

    assert isinstance(output, RetrievalOutput)
    assert output.project_id == "P001"
    assert isinstance(output.query, str)
    assert len(output.query) > 0
    assert isinstance(output.top_architectures, list)
    assert isinstance(output.evidence, list)

    # Relevance scores in [0, 1]
    for ev in output.evidence:
        assert 0.0 <= ev.relevance_score <= 1.0

    # JSON round-trip
    json_str  = output.model_dump_json(indent=2)
    recovered = RetrievalOutput.model_validate_json(json_str)
    assert recovered.project_id == output.project_id
    assert len(recovered.evidence) == len(output.evidence)


# ===========================================================================
# Test 9 – M1 and M2 pipelines still work correctly (regression guard)
# ===========================================================================

def test_m1_and_m2_pipelines_unaffected(
    service: ArchitectureDesignService,
    sample_batch: ASRBatch,
) -> None:
    # M1
    m1 = service.run(sample_batch)
    assert m1.project_id == "P001"
    assert len(m1.classifications) == 3

    # M2
    m2 = service.evaluate(sample_batch)
    assert m2.project_id == "P001"
    assert len(m2.architecture_evaluations) == 5
    ranks = sorted(ev.rank for ev in m2.architecture_evaluations)
    assert ranks == [1, 2, 3, 4, 5]
