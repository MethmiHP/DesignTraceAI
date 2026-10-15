"""
Unit and Integration Tests for Semantic QA Classifier – Milestone 7.

Validates:
1. BaseClassifier conformance.
2. Label space constraint: strictly six supported QAs.
3. Multi-label classification capability.
4. Semantic phrasing recognition without exact keyword overlap.
5. Unrelated statement rejection (confidence below threshold).
6. Deterministic output for identical inputs.
7. Configurable threshold behaviour.
8. Keyword baseline remains untouched.
9. Classifier runtime selection via configuration.
10. Downstream pipeline compatibility (M2–M6).
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from modules.architecture_design.schemas import (
    ASRBatch,
    ASRInput,
    QualityAttribute,
    QualityHit,
)
from modules.architecture_design.quality_classifier import (
    BaseClassifier,
    KeywordClassifier,
    SemanticQualityClassifier,
    _normalize,
    _dot_product,
)
from modules.architecture_design.retrieval.embedding_provider import (
    BaseEmbeddingProvider,
    StubEmbeddingProvider,
)
from modules.architecture_design.retrieval.vector_store import InMemoryVectorStore
from modules.architecture_design.llm.provider import StubLLMProvider
from modules.architecture_design.service import ArchitectureDesignService
from modules.architecture_design.config import ArchitectureConfig
from modules.architecture_design.dependencies import get_architecture_service


# ===========================================================================
# Deterministic Offline Mock Embedding Provider
# ===========================================================================

class DeterministicSemanticEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic mock provider assigning orthogonal / high-overlap vectors
    based on semantic concept clusters, enabling fully offline, fast test runs.
    """

    # 6 concept axes for the 6 quality attributes:
    # 0: Security, 1: Scalability, 2: Performance, 3: Reliability, 4: Maintainability, 5: Availability
    # 6: Unrelated / noise axis (orthogonal to all QAs)
    DIM = 7

    def __init__(self, model_name: str = "mock-semantic-model") -> None:
        self.model_name = model_name

    def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            t = text.lower()
            vec = [0.0] * self.DIM

            # Security semantic cues
            if any(w in t for w in ["security", "confidential", "cipher", "rbac", "tamper", "hipaa", "audit trail"]):
                vec[0] += 1.0
            # Scalability semantic cues
            if any(w in t for w in ["scalab", "throughput", "concurrency", "shard", "burst", "events per second"]):
                vec[1] += 1.0
            # Performance semantic cues
            if any(w in t for w in ["performance", "latency", "sub-second", "milliseconds", "fast", "under 100ms"]):
                vec[2] += 1.0
            # Reliability semantic cues
            if any(w in t for w in ["reliab", "fault", "circuit breaker", "resilient", "isolated", "rollback"]):
                vec[3] += 1.0
            # Maintainability semantic cues
            if any(w in t for w in ["maintain", "modular", "clean architecture", "decouple", "developer team"]):
                vec[4] += 1.0
            # Availability semantic cues
            if any(w in t for w in ["availab", "uptime", "failover", "zero-downtime", "99.999%"]):
                vec[5] += 1.0

            # If no concept detected (unrelated), return zero vector
            if sum(vec[:6]) == 0.0:
                results.append([0.0] * self.DIM)
            else:
                results.append(_normalize(vec))
        return results


# ===========================================================================
# 1. Interface & Label Space Tests
# ===========================================================================

def test_semantic_classifier_is_subclass_of_base():
    assert issubclass(SemanticQualityClassifier, BaseClassifier)
    assert issubclass(KeywordClassifier, BaseClassifier)


def test_semantic_classifier_only_outputs_valid_six_qas():
    provider = DeterministicSemanticEmbeddingProvider()
    classifier = SemanticQualityClassifier(embedding_provider=provider, threshold=0.30)

    statement = "The system must ensure high throughput and cryptographic tamper protection."
    hits = classifier.classify(statement)

    valid_names = {qa.value for qa in QualityAttribute}
    for hit in hits:
        assert hit.name in valid_names
        assert isinstance(hit.confidence, float)
        assert 0.0 <= hit.confidence <= 1.0


# ===========================================================================
# 2. Multi-label and Semantic Phrasing Recognition
# ===========================================================================

def test_semantic_phrasing_without_exact_keywords():
    """
    Statement uses concepts ('cipher', 'audit trail') that match semantic prototypes
    even if the exact keyword 'security' or 'authentication' isn't explicitly used.
    """
    provider = DeterministicSemanticEmbeddingProvider()
    classifier = SemanticQualityClassifier(embedding_provider=provider, threshold=0.50)

    # Phrasing with semantic cues matching Security prototype
    statement = "The system must protect user records using end-to-end cipher policies and audit trail tracking."
    hits = classifier.classify(statement)

    hit_names = [h.name for h in hits]
    assert "Security" in hit_names


def test_multi_label_classification():
    """A statement expressing multiple quality concerns should produce multiple hits."""
    provider = DeterministicSemanticEmbeddingProvider()
    classifier = SemanticQualityClassifier(embedding_provider=provider, threshold=0.50)

    # Expresses both Security and Scalability
    statement = "High throughput checkout events per second must enforce cipher verification."
    hits = classifier.classify(statement)

    hit_names = [h.name for h in hits]
    assert "Security" in hit_names
    assert "Scalability" in hit_names
    assert len(hits) >= 2


def test_unrelated_statement_rejected_below_threshold():
    """Unrelated statement should not produce blind quality attribute hits."""
    provider = DeterministicSemanticEmbeddingProvider()
    classifier = SemanticQualityClassifier(embedding_provider=provider, threshold=0.50)

    unrelated = "The primary UI button should be corporate navy blue with rounded corners."
    hits = classifier.classify(unrelated)
    assert len(hits) == 0


def test_deterministic_output_for_identical_input():
    provider = DeterministicSemanticEmbeddingProvider()
    classifier = SemanticQualityClassifier(embedding_provider=provider, threshold=0.50)

    statement = "The telemetry pipeline must ingest time-series packets with under 100ms latency."
    hits1 = classifier.classify(statement)
    hits2 = classifier.classify(statement)

    assert [(h.name, h.confidence) for h in hits1] == [(h.name, h.confidence) for h in hits2]


# ===========================================================================
# 3. Threshold Configuration Tests
# ===========================================================================

def test_configurable_threshold_behaviour():
    provider = DeterministicSemanticEmbeddingProvider()

    # Very strict threshold (0.95)
    strict_classifier = SemanticQualityClassifier(embedding_provider=provider, threshold=0.95)
    # Lenient threshold (0.20)
    lenient_classifier = SemanticQualityClassifier(embedding_provider=provider, threshold=0.20)

    statement = "The system must ingest bursts of events per second with low latency."
    strict_hits = strict_classifier.classify(statement)
    lenient_hits = lenient_classifier.classify(statement)

    assert len(lenient_hits) >= len(strict_hits)


# ===========================================================================
# 4. Keyword Baseline Preservation
# ===========================================================================

def test_keyword_classifier_baseline_remains_unchanged():
    kw = KeywordClassifier()
    hits = kw.classify("The system must remain operational and resilient during peak load.")
    hit_names = [h.name for h in hits]

    assert "Reliability" in hit_names
    assert "Scalability" in hit_names
    # Check that confidence scale is heuristic
    assert any(h.confidence > 0.0 for h in hits)


# ===========================================================================
# 5. Dependency Injection & Service Integration
# ===========================================================================

def test_service_with_semantic_classifier_executes_m2_to_m6(monkeypatch):
    """Verify entire pipeline (M1 -> M2 -> M3 -> M4 -> M5) functions with SemanticQualityClassifier."""
    provider = DeterministicSemanticEmbeddingProvider()
    semantic_classifier = SemanticQualityClassifier(
        embedding_provider=provider,
        threshold=0.30,
    )

    service = ArchitectureDesignService(
        classifier=semantic_classifier,
        embedding_provider=StubEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
        llm_provider=StubLLMProvider(),
    )

    batch = ASRBatch(
        project_id="PROJ-SEM",
        asrs=[
            ASRInput(
                requirement_id="REQ-1",
                statement="All patient transactions must maintain cryptographic tamper protection and audit trail.",
            )
        ],
    )

    # Test M1
    m1_out = service.run(batch)
    assert m1_out.quality_profile.Security >= 1

    # Test M2
    m2_out = service.evaluate(batch)
    assert len(m2_out.architecture_evaluations) > 0

    # Test M6 analyze with metadata
    res = service.analyze(batch)
    assert res.metadata.classifier_name == "SemanticQualityClassifier"
    assert res.result.recommendation is not None
    assert res.result.design is not None


def test_dependency_injection_selects_configured_classifier(monkeypatch):
    """Verify get_architecture_service respects ARCHITECTURE_QA_CLASSIFIER."""
    monkeypatch.setenv("ARCHITECTURE_USE_STUB_LLM", "true")
    monkeypatch.setenv("ARCHITECTURE_QA_CLASSIFIER", "semantic")
    from modules.architecture_design import config
    monkeypatch.setattr(config.architecture_config, "use_stub_llm", True)
    monkeypatch.setattr(config.architecture_config, "qa_classifier", "semantic")

    # Patch SentenceTransformer to use offline mock
    monkeypatch.setattr(
        "modules.architecture_design.dependencies.SentenceTransformerEmbeddingProvider",
        DeterministicSemanticEmbeddingProvider,
    )

    get_architecture_service.cache_clear()
    svc = get_architecture_service()
    assert isinstance(svc._classifier, SemanticQualityClassifier)

    # Reset to keyword and clear cache
    monkeypatch.setattr(config.architecture_config, "qa_classifier", "keyword")
    get_architecture_service.cache_clear()
    svc_kw = get_architecture_service()
    assert isinstance(svc_kw._classifier, KeywordClassifier)

    get_architecture_service.cache_clear()
