"""
Tests for Architecture Decision Agent – Milestone 2.

Pipeline under test:
    ASRBatch  →  ArchitectureDesignService.evaluate()  →  ScoringOutput

Run ALL tests (M1 + M2) with:
    cd d:/4thYEAR/Research/DesignTraceAI/backend
    pytest tests/ -v
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.architecture_design.schemas import (
    ASRBatch,
    ASRInput,
    ArchitectureStyle,
    ScoringOutput,
    QualityProfile,
)
from modules.architecture_design.service import ArchitectureDesignService
from modules.architecture_design.knowledge.architecture_scorer import score as _score


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service() -> ArchitectureDesignService:
    return ArchitectureDesignService()


@pytest.fixture
def sample_batch() -> ASRBatch:
    """Three-ASR sample from the milestone spec."""
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


@pytest.fixture
def sample_output(service: ArchitectureDesignService, sample_batch: ASRBatch) -> ScoringOutput:
    return service.evaluate(sample_batch)


# ---------------------------------------------------------------------------
# Test 1 – All five architecture styles are present in the evaluations
# ---------------------------------------------------------------------------

def test_all_five_styles_present(sample_output: ScoringOutput) -> None:
    styles_returned = {ev.style for ev in sample_output.architecture_evaluations}
    expected_styles = set(ArchitectureStyle)
    assert styles_returned == expected_styles, (
        f"Missing styles: {expected_styles - styles_returned}"
    )


# ---------------------------------------------------------------------------
# Test 2 – Ranks are 1–5 with no gaps or duplicates
# ---------------------------------------------------------------------------

def test_rank_ordering(sample_output: ScoringOutput) -> None:
    ranks = sorted(ev.rank for ev in sample_output.architecture_evaluations)
    assert ranks == [1, 2, 3, 4, 5], f"Unexpected ranks: {ranks}"

    # Also verify that rank 1 has the highest normalized score
    evals = sample_output.architecture_evaluations
    rank1 = next(ev for ev in evals if ev.rank == 1)
    for ev in evals:
        assert rank1.normalized_score >= ev.normalized_score, (
            f"Rank-1 style {rank1.style} has lower score than {ev.style}"
        )


# ---------------------------------------------------------------------------
# Test 3 – All normalized scores are within [0, 100]
# ---------------------------------------------------------------------------

def test_normalized_score_in_range(sample_output: ScoringOutput) -> None:
    for ev in sample_output.architecture_evaluations:
        assert 0.0 <= ev.normalized_score <= 100.0, (
            f"{ev.style} normalized score {ev.normalized_score} out of range"
        )


# ---------------------------------------------------------------------------
# Test 4 – Zero-weight attributes contribute 0.0 to every style's score
# ---------------------------------------------------------------------------

def test_zero_weight_attributes_contribute_zero(sample_output: ScoringOutput) -> None:
    profile = sample_output.quality_profile
    zero_attrs = [
        attr for attr in ("Security", "Scalability", "Performance",
                          "Reliability", "Maintainability", "Availability")
        if getattr(profile, attr) == 0
    ]
    for ev in sample_output.architecture_evaluations:
        contrib = ev.quality_contributions.model_dump()
        for attr in zero_attrs:
            assert contrib[attr] == 0.0, (
                f"{ev.style}: {attr} has count 0 but contribution {contrib[attr]}"
            )


# ---------------------------------------------------------------------------
# Test 5 – Scoring is deterministic (same input → same output across calls)
# ---------------------------------------------------------------------------

def test_scoring_is_deterministic(
    service: ArchitectureDesignService, sample_batch: ASRBatch
) -> None:
    out1 = service.evaluate(sample_batch)
    out2 = service.evaluate(sample_batch)
    assert out1.model_dump_json() == out2.model_dump_json(), (
        "Two identical calls returned different results — scorer is not deterministic"
    )


# ---------------------------------------------------------------------------
# Test 6 – ScoringOutput is Pydantic-validated and JSON round-trips correctly
# ---------------------------------------------------------------------------

def test_output_is_pydantic_validated_and_serialisable(
    sample_output: ScoringOutput,
) -> None:
    assert isinstance(sample_output, ScoringOutput)

    data = sample_output.model_dump()
    assert isinstance(data, dict)
    assert data["project_id"] == "P001"
    assert len(data["architecture_evaluations"]) == 5

    json_str = sample_output.model_dump_json(indent=2)
    recovered = ScoringOutput.model_validate_json(json_str)
    assert recovered.project_id == sample_output.project_id
    assert len(recovered.architecture_evaluations) == 5


# ---------------------------------------------------------------------------
# Test 7 – Given a pure-scalability profile, Microservices ranks #1
# ---------------------------------------------------------------------------

def test_microservices_ranks_first_on_scalability_profile() -> None:
    """
    A profile with only Scalability active should favour architectures
    with the highest Scalability support score.  Microservices has support=5.
    """
    profile = QualityProfile(
        Security=0, Scalability=3, Performance=0,
        Reliability=0, Maintainability=0, Availability=0,
    )
    evaluations = _score(profile)
    rank1 = next(ev for ev in evaluations if ev.rank == 1)
    assert rank1.style in (ArchitectureStyle.MICROSERVICES, ArchitectureStyle.EVENT_DRIVEN), (
        f"Expected Microservices or Event-Driven at rank 1, got {rank1.style}"
    )
