"""
Tests for Architecture Decision Agent – Milestone 4 (LLM Recommendation).

Strategy:
----------
Use the `StubLLMProvider` to inject pre-canned `ArchitectureRecommendation` objects,
returning instantly without making real Gemini API calls.

Validates the critical "Deterministic Guardrails":
1. Rank 1 override if the LLM hallucinates another style.
2. Rank 1 score override if the LLM invents a new score.
3. Filtering of hallucinated rejected alternatives.
4. Filtering of hallucinated evidence IDs.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List
import pytest

from modules.architecture_design.schemas import (
    ASRBatch,
    ASRInput,
    ArchitectureRecommendation,
    RejectedAlternative,
    RecommendationOutput,
)
from modules.architecture_design.service import ArchitectureDesignService
from modules.architecture_design.llm.provider import StubLLMProvider
from tests.test_architecture_retrieval import StubEmbeddingProvider
from modules.architecture_design.retrieval.vector_store import InMemoryVectorStore


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def sample_batch() -> ASRBatch:
    # A batch heavy on Scalability and Reliability (Microservices normally wins this in M2)
    return ASRBatch(
        project_id="P004",
        asrs=[
            ASRInput(requirement_id="REQ-1", statement="The system must scale to 10M concurrent users."),
            ASRInput(requirement_id="REQ-2", statement="Microservices must fail independently without bringing down the system."),
        ],
    )


def build_service(mock_llm_response: ArchitectureRecommendation) -> ArchitectureDesignService:
    """Helper to build a service with a mocked LLM that returns a specific response."""
    return ArchitectureDesignService(
        embedding_provider=StubEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
        llm_provider=StubLLMProvider(canned_response=mock_llm_response),
    )


# ===========================================================================
# Tests
# ===========================================================================

def test_recommendation_pydantic_validation(sample_batch: ASRBatch) -> None:
    # The default StubLLMProvider uses basic regex to find the right Rank 1 style and score
    # from the prompt text, then returns a generic valid payload.
    svc = ArchitectureDesignService(
        embedding_provider=StubEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
        llm_provider=StubLLMProvider(),
    )
    result = svc.recommend(sample_batch)
    assert isinstance(result, RecommendationOutput)
    assert isinstance(result.recommendation, ArchitectureRecommendation)
    assert result.project_id == "P004"


def test_guardrail_enforces_rank_1_style_and_score(sample_batch: ASRBatch) -> None:
    # 1. Run M1/M2 manually just to see what the true Rank 1 is
    svc_temp = ArchitectureDesignService()
    scoring_out = svc_temp.evaluate(sample_batch)
    true_rank_1 = sorted(scoring_out.architecture_evaluations, key=lambda e: e.rank)[0]
    
    assert true_rank_1.style.value != "Modular Monolith", "Sanity check: true rank 1 cannot be Modular Monolith for this batch."

    # 2. Inject an LLM response that maliciously hallucinates a different style
    malicious_rec = ArchitectureRecommendation(
        selected_style="Modular Monolith", # Hallucinated (probably rank 3 or 4)
        score=99.9,                        # Hallucinated score
        rationale="Because I, the LLM, said so.",
        key_quality_attributes=[],
        strengths=[],
        weaknesses=[],
        tradeoffs=[],
        rejected_alternatives=[],
        evidence_ids=[],
        review_required=False,
    )
    
    svc = build_service(malicious_rec)
    result = svc.recommend(sample_batch)
    
    # 3. Guardrail should have patched the output back to the true Rank 1
    rec = result.recommendation
    assert rec.selected_style == true_rank_1.style.value, "Guardrail failed to restore Rank 1 style."
    assert rec.score == true_rank_1.normalized_score, "Guardrail failed to restore Rank 1 score."
    assert rec.rationale == "Because I, the LLM, said so.", "Rationale should remain intact."


def test_guardrail_filters_invalid_rejected_alternatives(sample_batch: ASRBatch) -> None:
    rec_with_bad_alts = ArchitectureRecommendation(
        selected_style="Event-Driven Architecture", # Correct Rank 1
        score=0.0,
        rationale="Test",
        rejected_alternatives=[
            RejectedAlternative(style="Microservices", score=0, reason="Valid style but missed Rank 1"),
            RejectedAlternative(style="Blockchain Architecture", score=100, reason="Hallucinated style!"),
        ],
    )
    
    svc = build_service(rec_with_bad_alts)
    result = svc.recommend(sample_batch)
    rec = result.recommendation
    
    # Blockchain Architecture should be stripped entirely
    alt_names = [a.style for a in rec.rejected_alternatives]
    assert "Blockchain Architecture" not in alt_names, "Hallucinated alternative wasn't stripped."
    assert "Microservices" in alt_names, "Valid alternative was incorrectly stripped."
    
    # Valid alternatives should have their scores patched to the real deterministic score
    for alt in rec.rejected_alternatives:
        if alt.style == "Microservices":
            assert alt.score > 0, "Guardrail failed to patch alternative score."


def test_guardrail_filters_invalid_evidence_ids(sample_batch: ASRBatch) -> None:
    rec_test = ArchitectureRecommendation(
        selected_style="Microservices",
        score=0,
        rationale="Test",
        # KB-019 actually exists in the KB. KB-999 is totally hallucinated.
        evidence_ids=["KB-019", "KB-999"], 
    )
    
    svc = build_service(rec_test)
    result = svc.recommend(sample_batch)
    rec = result.recommendation
    
    assert "KB-999" not in rec.evidence_ids, "Hallucinated evidence ID wasn't stripped."


def test_m1_m2_m3_pipelines_unaffected(sample_batch: ASRBatch) -> None:
    """Ensure adding M4 didn't accidentally pollute the earlier pipelnes on the service."""
    svc = ArchitectureDesignService()
    
    m1 = svc.run(sample_batch)
    assert m1.project_id == "P004"
    
    m2 = svc.evaluate(sample_batch)
    assert m2.project_id == "P004"
    assert len(m2.architecture_evaluations) == 5
    
    # The retriever lazy loads on M3 calling. Since we haven't loaded google-genai, 
    # but the M3 tests already do it anyway.
    pass


def test_guardrails_handle_rank_1_ties_properly(sample_batch: ASRBatch) -> None:
    # 1. Force a scenario where two styles tie for Rank 1.
    # To do this, we can inject a mock eval into the service.
    # For now, let's just intercept `evaluate` in the service to return a tied ScoringOutput
    svc_temp = ArchitectureDesignService()
    scoring_out = svc_temp.evaluate(sample_batch)
    
    # Manually patch scoring_out to have a tie
    evals = sorted(scoring_out.architecture_evaluations, key=lambda e: e.rank)
    evals[0].normalized_score = 100.0
    evals[0].rank = 1
    evals[1].normalized_score = 100.0
    evals[1].rank = 1
    
    class TieMockService(ArchitectureDesignService):
        def evaluate(self, batch):
            return scoring_out
            
    # Case A: LLM picks one but doesn't set tie_resolved or provide a reason.
    malicious_rec = ArchitectureRecommendation(
        selected_style=evals[1].style.value, # It picked the second tied candidate
        score=100.0,
        rationale="I picked it.",
        tied_candidates=[evals[0].style.value, evals[1].style.value],
        tie_resolved=False, # Did not properly resolve
        tie_resolution_reason=None,
    )
    
    svc = TieMockService(
        embedding_provider=StubEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
        llm_provider=StubLLMProvider(canned_response=malicious_rec)
    )
    result = svc.recommend(sample_batch)
    assert result.recommendation.review_required is True, "Guardrail must flag review when tie is unresolved"
    assert result.recommendation.tie_resolved is False
    
    # Case B: LLM picks one AND gives a valid reason
    good_rec = ArchitectureRecommendation(
        selected_style=evals[1].style.value,
        score=100.0,
        rationale="I picked it.",
        tied_candidates=[evals[0].style.value, evals[1].style.value],
        tie_resolved=True,
        tie_resolution_reason="Requirements demand async, favoring this style.",
    )
    
    svc_good = TieMockService(
        embedding_provider=StubEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
        llm_provider=StubLLMProvider(canned_response=good_rec)
    )
    result_good = svc_good.recommend(sample_batch)
    assert result_good.recommendation.review_required is False
    assert result_good.recommendation.tie_resolved is True
    assert result_good.recommendation.selected_style == evals[1].style.value
