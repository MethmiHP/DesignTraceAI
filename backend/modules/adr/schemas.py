"""
Pydantic schemas for the Architecture Decision Records (ADR) module.

The ADR module receives design decisions from other DesignTrace AI modules,
identifies significant decisions, gathers supporting evidence, generates
structured Architecture Decision Records, maintains traceability, and
supports the ADR lifecycle.
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class DecisionSource(str, Enum):
    """DesignTrace AI module that produced the decision."""

    ARCHITECTURE_DECISION = "architecture_decision"
    DATABASE_DESIGN = "database_design"
    API_COMPONENT_DESIGN = "api_component_design"
    QUALITY_EVALUATION = "quality_evaluation"
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    TRACEABILITY = "traceability"
    MANUAL = "manual"


class ADRStatus(str, Enum):
    """Lifecycle status of an Architecture Decision Record."""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"


class ADRGenerationMethod(str, Enum):
    """Method used to generate ADR content."""

    LLM = "llm"
    DETERMINISTIC = "deterministic"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"


# ---------------------------------------------------------------------------
# Input decision schemas
# ---------------------------------------------------------------------------


class DesignDecision(BaseModel):
    """
    Normalized design decision received from another DesignTrace AI module.
    """

    decision_id: str = Field(
        ...,
        min_length=1,
        description="Stable unique identifier of the source design decision.",
    )

    project_id: str = Field(
        ...,
        min_length=1,
        description="Project to which the decision belongs.",
    )

    source_module: DecisionSource = Field(
        ...,
        description="Module that produced the decision.",
    )

    title: str = Field(
        ...,
        min_length=3,
        description="Short human-readable title of the decision.",
    )

    decision: str = Field(
        ...,
        min_length=5,
        description="Selected design option or decision.",
    )

    context: str = Field(
        ...,
        min_length=5,
        description="Problem or context that caused the decision.",
    )

    rationale: str | None = Field(
        default=None,
        description="Reason why the selected option was chosen.",
    )

    alternatives: list[str] = Field(
        default_factory=list,
        description="Alternative solutions considered.",
    )

    rejected_alternative_reasons: list[str] = Field(
        default_factory=list,
        description="Reasons for rejecting alternative solutions.",
    )

    decision_criteria: list[str] = Field(
        default_factory=list,
        description="Criteria used when comparing available options.",
    )

    benefits: list[str] = Field(
        default_factory=list,
        description="Expected benefits of the decision.",
    )

    risks: list[str] = Field(
        default_factory=list,
        description="Potential risks introduced by the decision.",
    )

    consequences: list[str] = Field(
        default_factory=list,
        description="Expected consequences of applying the decision.",
    )

    trade_offs: list[str] = Field(
        default_factory=list,
        description="Trade-offs associated with the selected option.",
    )

    requirement_ids: list[str] = Field(
        default_factory=list,
        description="Requirement identifiers related to the decision.",
    )

    design_element_ids: list[str] = Field(
        default_factory=list,
        description="Design artifact or element identifiers affected.",
    )

    evidence: list[str] = Field(
        default_factory=list,
        description="Evidence supporting the decision.",
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional confidence associated with the source decision.",
    )


# ---------------------------------------------------------------------------
# Significance detection schemas
# ---------------------------------------------------------------------------


class SignificanceCriteria(BaseModel):
    """
    Criteria used to determine whether a design decision deserves an ADR.
    """

    architecture_impact: bool = False
    quality_attribute_impact: bool = False
    cross_component_impact: bool = False
    long_term_impact: bool = False
    difficult_to_reverse: bool = False
    contains_trade_offs: bool = False
    security_or_compliance_impact: bool = False


class SignificanceResult(BaseModel):
    """Result produced by the ADR significance detector."""

    decision_id: str

    significant: bool

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calculated decision significance score.",
    )

    criteria: SignificanceCriteria

    reasons: list[str] = Field(
        default_factory=list,
        description="Explainable reasons supporting the significance result.",
    )


# ---------------------------------------------------------------------------
# ADR traceability
# ---------------------------------------------------------------------------


class ADRTraceability(BaseModel):
    """
    Traceability links maintained by the ADR.
    """

    requirement_ids: list[str] = Field(default_factory=list)

    design_element_ids: list[str] = Field(default_factory=list)

    source_decision_ids: list[str] = Field(default_factory=list)

    source_modules: list[DecisionSource] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Generated ADR schema
# ---------------------------------------------------------------------------


class ADRRecord(BaseModel):
    """Complete structured Architecture Decision Record."""

    adr_id: str

    project_id: str

    title: str

    status: ADRStatus = ADRStatus.PROPOSED

    generation_method: ADRGenerationMethod = (
        ADRGenerationMethod.DETERMINISTIC
    )

    context: str

    decision: str

    rationale: str

    alternatives: list[str] = Field(default_factory=list)

    rejected_alternative_reasons: list[str] = Field(default_factory=list)

    decision_criteria: list[str] = Field(default_factory=list)

    benefits: list[str] = Field(default_factory=list)

    risks: list[str] = Field(default_factory=list)

    consequences: list[str] = Field(default_factory=list)

    trade_offs: list[str] = Field(default_factory=list)

    evidence: list[str] = Field(default_factory=list)

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    traceability: ADRTraceability

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    supersedes: str | None = None

    superseded_by: str | None = None


# ---------------------------------------------------------------------------
# API request / response schemas
# ---------------------------------------------------------------------------


class ADRGenerationRequest(BaseModel):
    """
    Input sent to the ADR module through the Coordinator.
    """

    project_id: str = Field(
        ...,
        min_length=1,
    )

    decisions: list[DesignDecision] = Field(
        ...,
        min_length=1,
    )


class ADRGenerationResult(BaseModel):
    """
    Result for an individual source design decision.
    """

    decision: DesignDecision

    significance: SignificanceResult

    adr: ADRRecord | None = None


class ADRGenerationResponse(BaseModel):
    """
    Complete response returned by the ADR module.
    """

    project_id: str

    results: list[ADRGenerationResult]

    generated_adr_count: int = 0

    skipped_decision_count: int = 0