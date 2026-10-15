"""
Tests for Architecture Decision Agent – Milestone 1.

Pipeline under test:
    ASRBatch  →  ArchitectureDesignService.run()  →  ClassificationOutput

Run with:
    cd d:/4thYEAR/Research/DesignTraceAI/backend
    pytest tests/test_architecture_design.py -v
"""

from __future__ import annotations

import json
import sys
import os

# Make sure the backend/ directory is on sys.path so imports work
# whether pytest is run from backend/ or from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from modules.architecture_design.schemas import (
    ASRBatch,
    ASRInput,
    ClassificationOutput,
    QualityAttribute,
)
from modules.architecture_design.service import ArchitectureDesignService


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service() -> ArchitectureDesignService:
    return ArchitectureDesignService()


@pytest.fixture
def sample_batch() -> ASRBatch:
    """The three sample ASRs from the milestone spec."""
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


# ---------------------------------------------------------------------------
# Test 1 – REQ-001 maps to Security
# ---------------------------------------------------------------------------

def test_security_classification(service: ArchitectureDesignService) -> None:
    batch = ASRBatch(
        project_id="P001",
        asrs=[
            ASRInput(
                requirement_id="REQ-001",
                statement="Patient information shall be protected from unauthorized access.",
            )
        ],
    )
    result = service.run(batch)

    assert len(result.classifications) == 1
    cls = result.classifications[0]
    assert cls.requirement_id == "REQ-001"

    attr_names = [hit.name for hit in cls.quality_attributes]
    assert QualityAttribute.SECURITY in attr_names, (
        f"Expected Security in classifications, got {attr_names}"
    )

    # Security should be the top-ranked attribute for this statement
    assert cls.quality_attributes[0].name == QualityAttribute.SECURITY

    # Confidence should be a meaningful score
    sec_hit = next(h for h in cls.quality_attributes if h.name == QualityAttribute.SECURITY)
    assert sec_hit.confidence > 0.5, (
        f"Expected confidence > 0.5 for Security, got {sec_hit.confidence}"
    )


# ---------------------------------------------------------------------------
# Test 2 – REQ-002 maps to Scalability AND Performance
# ---------------------------------------------------------------------------

def test_scalability_and_performance_classification(service: ArchitectureDesignService) -> None:
    batch = ASRBatch(
        project_id="P001",
        asrs=[
            ASRInput(
                requirement_id="REQ-002",
                statement="The system shall support 500 concurrent users with acceptable response time.",
            )
        ],
    )
    result = service.run(batch)

    cls = result.classifications[0]
    attr_names = [hit.name for hit in cls.quality_attributes]

    assert QualityAttribute.SCALABILITY in attr_names, (
        f"Expected Scalability, got {attr_names}"
    )
    assert QualityAttribute.PERFORMANCE in attr_names, (
        f"Expected Performance, got {attr_names}"
    )


# ---------------------------------------------------------------------------
# Test 3 – REQ-003 maps to Reliability
# ---------------------------------------------------------------------------

def test_reliability_classification(service: ArchitectureDesignService) -> None:
    batch = ASRBatch(
        project_id="P001",
        asrs=[
            ASRInput(
                requirement_id="REQ-003",
                statement="The system shall remain operational even if one service fails.",
            )
        ],
    )
    result = service.run(batch)

    cls = result.classifications[0]
    attr_names = [hit.name for hit in cls.quality_attributes]

    assert QualityAttribute.RELIABILITY in attr_names, (
        f"Expected Reliability, got {attr_names}"
    )

    rel_hit = next(h for h in cls.quality_attributes if h.name == QualityAttribute.RELIABILITY)
    assert rel_hit.confidence > 0.3


# ---------------------------------------------------------------------------
# Test 4 – Quality profile counts are correct for the full sample batch
# ---------------------------------------------------------------------------

def test_quality_profile_counts(
    service: ArchitectureDesignService, sample_batch: ASRBatch
) -> None:
    result = service.run(sample_batch)
    profile = result.quality_profile

    # All 6 keys must always exist
    assert hasattr(profile, "Security")
    assert hasattr(profile, "Scalability")
    assert hasattr(profile, "Performance")
    assert hasattr(profile, "Reliability")
    assert hasattr(profile, "Maintainability")
    assert hasattr(profile, "Availability")

    # REQ-001 → Security
    assert profile.Security >= 1, f"Security count should be ≥1, got {profile.Security}"
    # REQ-002 → Scalability + Performance
    assert profile.Scalability >= 1, f"Scalability count should be ≥1, got {profile.Scalability}"
    assert profile.Performance >= 1, f"Performance count should be ≥1, got {profile.Performance}"
    # REQ-003 → Reliability
    assert profile.Reliability >= 1, f"Reliability count should be ≥1, got {profile.Reliability}"
    # Maintainability should be 0 (no keywords matched)
    assert profile.Maintainability == 0, (
        f"Maintainability should be 0, got {profile.Maintainability}"
    )


# ---------------------------------------------------------------------------
# Test 5 – Output is Pydantic-validated and JSON round-trips correctly
# ---------------------------------------------------------------------------

def test_output_is_pydantic_validated_and_serialisable(
    service: ArchitectureDesignService, sample_batch: ASRBatch
) -> None:
    result = service.run(sample_batch)

    # Must be a ClassificationOutput instance
    assert isinstance(result, ClassificationOutput)

    # model_dump() must be a plain dict
    data = result.model_dump()
    assert isinstance(data, dict)
    assert data["project_id"] == "P001"
    assert len(data["classifications"]) == 3

    # Round-trip through JSON must not raise
    json_str = result.model_dump_json(indent=2)
    recovered = ClassificationOutput.model_validate_json(json_str)
    assert recovered.project_id == result.project_id
    assert len(recovered.classifications) == len(result.classifications)
