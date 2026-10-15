"""

Pydantic schemas for the Architecture Decision Agent – Milestones 1–7.2.



Milestone 1 input/output:

  Input  : ASRBatch   (project_id + list of ASRInput)

  Output : ClassificationOutput  (per-ASR labels + project QualityProfile)



Milestone 2 output:

  Output : ScoringOutput  (QualityProfile + ranked ArchitectureEvaluation list)

"""



from __future__ import annotations



from enum import Enum

from typing import List



from pydantic import BaseModel, Field, field_validator, model_validator





# ---------------------------------------------------------------------------

# Quality Attribute Enum

# ---------------------------------------------------------------------------



class QualityAttribute(str, Enum):

    SECURITY        = "Security"

    SCALABILITY     = "Scalability"

    PERFORMANCE     = "Performance"

    RELIABILITY     = "Reliability"

    MAINTAINABILITY = "Maintainability"

    AVAILABILITY    = "Availability"





# ---------------------------------------------------------------------------

# Input schemas

# ---------------------------------------------------------------------------



class ASRInput(BaseModel):

    """A single Architecturally Significant Requirement (already identified)."""



    requirement_id: str = Field(..., description="Unique identifier for the ASR (e.g. 'REQ-001')")

    statement: str      = Field(..., description="Natural-language text of the requirement")





class ASRBatch(BaseModel):

    """A project-level batch of ASRs passed to the Architecture Decision Agent."""



    project_id: str              = Field(..., description="Unique project identifier")

    asrs: List[ASRInput]         = Field(..., min_length=1, description="One or more ASRs")





class RequirementType(str, Enum):

    """Requirement categories supplied by the Requirement Analysis Module."""

    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    CONSTRAINT = "constraint"
    OTHER = "other"


class RequirementInput(BaseModel):

    """A project requirement used to generate the complete high-level design."""

    requirement_id: str = Field(..., description="Unique requirement identifier")
    statement: str = Field(..., min_length=1, description="Natural-language requirement statement")
    requirement_type: RequirementType = Field(RequirementType.OTHER, description="Requirement category")


class ArchitectureProjectInput(BaseModel):

    """Complete project context for design generation and full analysis."""

    project_id: str = Field(..., description="Unique project identifier")
    requirements: List[RequirementInput] = Field(
        ...,
        min_length=1,
        description="All architecture-relevant requirements supplied by Requirement Analysis / Coordinator",
    )
    asrs: List[ASRInput] = Field(
        ...,
        min_length=1,
        description="Identified ASRs used for architecture decision-making",
    )

    @model_validator(mode="after")
    def validate_requirement_relationships(self):
        requirement_ids = [item.requirement_id for item in self.requirements]
        asr_ids = [item.requirement_id for item in self.asrs]

        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError("Requirement IDs must be unique.")
        if len(asr_ids) != len(set(asr_ids)):
            raise ValueError("ASR IDs must be unique.")

        missing_asrs = sorted(set(asr_ids) - set(requirement_ids))
        if missing_asrs:
            raise ValueError(
                "Every ASR must reference a requirement present in 'requirements'. "
                f"Missing IDs: {missing_asrs}"
            )
        return self

    def to_asr_batch(self) -> ASRBatch:
        return ASRBatch(project_id=self.project_id, asrs=self.asrs)


# ---------------------------------------------------------------------------

# Classification result schemas

# ---------------------------------------------------------------------------



class QualityHit(BaseModel):

    """A single quality-attribute match for an ASR, with a confidence score."""



    name:       QualityAttribute = Field(..., description="The matched quality attribute")

    confidence: float            = Field(..., ge=0.0, le=1.0, description="Match confidence [0, 1]")





class ASRClassification(BaseModel):

    """Classification result for a single ASR – may carry multiple labels."""



    requirement_id:     str              = Field(..., description="The ASR identifier")

    quality_attributes: List[QualityHit] = Field(

        default_factory=list,

        description="Matched quality attributes, ordered by descending confidence"

    )





# ---------------------------------------------------------------------------

# Quality profile schema

# ---------------------------------------------------------------------------



class QualityProfile(BaseModel):

    """

    Project-level quality profile.



    Each key is a QualityAttribute name; the value is the number of ASRs

    that mapped to that attribute.  All six attributes are always present

    (count = 0 when unmatched).

    """



    Security:        int = 0

    Scalability:     int = 0

    Performance:     int = 0

    Reliability:     int = 0

    Maintainability: int = 0

    Availability:    int = 0





# ---------------------------------------------------------------------------

# Final output schema

# ---------------------------------------------------------------------------



class ClassificationOutput(BaseModel):

    """

    Complete output of the Architecture Decision Agent – Milestone 1.

    Ready for serialisation to JSON and downstream consumption.

    """



    project_id:      str                     = Field(..., description="Project identifier, echoed from input")

    classifications: List[ASRClassification] = Field(default_factory=list)

    quality_profile: QualityProfile          = Field(default_factory=QualityProfile)





# ===========================================================================

# Milestone 2 schemas – Architecture Evaluation

# ===========================================================================



# ---------------------------------------------------------------------------

# Architecture style enum

# ---------------------------------------------------------------------------



class ArchitectureStyle(str, Enum):

    LAYERED          = "Layered Architecture"

    MVC              = "MVC"

    MODULAR_MONOLITH = "Modular Monolith"

    MICROSERVICES    = "Microservices"

    EVENT_DRIVEN     = "Event-Driven Architecture"





# ---------------------------------------------------------------------------

# Per-style scoring schemas

# ---------------------------------------------------------------------------



class QualityContributions(BaseModel):

    """

    Per-quality-attribute contribution to an architecture style's raw score.

    contribution[attr] = weight[attr] × support_score[attr]

    """

    Security:        float = 0.0

    Scalability:     float = 0.0

    Performance:     float = 0.0

    Reliability:     float = 0.0

    Maintainability: float = 0.0

    Availability:    float = 0.0





class ArchitectureEvaluation(BaseModel):

    """

    Scoring result for a single architecture style.

    Includes the numeric scores, rank, per-quality breakdown,

    and qualitative information from the knowledge base.

    """

    style:                 ArchitectureStyle   = Field(..., description="Architecture style name")

    raw_score:             float               = Field(..., description="Weighted sum score before normalisation")

    normalized_score:      float               = Field(..., ge=0.0, le=100.0, description="Score on a 0–100 scale")

    rank:                  int                 = Field(..., ge=1, description="Rank among evaluated styles (1 = best fit)")

    is_tied:               bool                = Field(default=False, description="True if this style has the exact same normalized score as another style")

    tied_with:             List[str]           = Field(default_factory=list, description="Names of other architecture styles with the same score")

    quality_contributions: QualityContributions = Field(default_factory=QualityContributions)

    strengths:             List[str]           = Field(default_factory=list)

    weaknesses:            List[str]           = Field(default_factory=list)

    tradeoffs:             List[str]           = Field(default_factory=list)





# ---------------------------------------------------------------------------

# Top-level Milestone 2 output schema

# ---------------------------------------------------------------------------



class ScoringOutput(BaseModel):

    """

    Complete output of the Architecture Decision Agent – Milestone 2.

    Combines the quality profile with ranked architecture evaluations.

    """

    project_id:               str                        = Field(..., description="Project identifier")

    quality_profile:           QualityProfile             = Field(...)

    architecture_evaluations:  List[ArchitectureEvaluation] = Field(default_factory=list)





# ===========================================================================

# Milestone 3 schemas – RAG Evidence Retrieval

# ===========================================================================



class RetrievedEvidence(BaseModel):

    """

    A single piece of architecture knowledge retrieved by the RAG layer.



    relevance_score is the cosine similarity between the retrieval query and

    this item's content embedding.  Range [0, 1] where 1 = identical.

    """

    knowledge_id:        str       = Field(..., description="Unique knowledge item identifier (e.g. KB-001)")

    title:               str       = Field(..., description="Short human-readable title")

    content:             str       = Field(..., description="Full knowledge text")

    source:              str       = Field(..., description="Origin of this knowledge item")

    relevance_score:     float     = Field(..., ge=0.0, le=1.0, description="Cosine similarity score [0, 1]")

    architecture_styles: List[str] = Field(default_factory=list)

    quality_attributes:  List[str] = Field(default_factory=list)





class RetrievalOutput(BaseModel):

    """

    Complete output of the Architecture Decision Agent – Milestone 3.

    Returned by ArchitectureDesignService.retrieve_evidence().

    """

    project_id:        str                   = Field(..., description="Project identifier")

    query:             str                   = Field(..., description="Retrieval query built from the project's ASRs and active quality attributes")

    top_architectures: List[str]             = Field(default_factory=list, description="Top-ranked architecture style names from M2 scoring")

    evidence:          List[RetrievedEvidence] = Field(default_factory=list, description="Retrieved evidence items, ordered by descending relevance_score")





# ===========================================================================

# Milestone 4 schemas – LLM-Based Explainable Architecture Recommendation

# ===========================================================================



class RejectedAlternative(BaseModel):

    """An architecture style that was evaluated but not selected."""

    style:  str = Field(..., description="Name of the rejected architecture style")

    score:  float = Field(..., description="Its deterministic evaluation score")

    reason: str = Field(..., description="Explanation of why this style was not selected, citing trade-offs or weaknesses")





class ArchitectureRecommendation(BaseModel):

    """The structured LLM explanation for the architecture decision."""

    selected_style:         str                       = Field(..., description="The recommended architecture style (must match M2 Rank 1)")

    score:                  float                     = Field(..., description="The deterministic score from M2")

    rationale:              str                       = Field(..., description="Detailed explanation of why this style is the best fit, citing the retrieved evidence")

    key_quality_attributes: List[str]                 = Field(default_factory=list, description="The primary quality attributes driving this decision")

    strengths:              List[str]                 = Field(default_factory=list, description="Key strengths of the chosen style in this context")

    weaknesses:             List[str]                 = Field(default_factory=list, description="Accepted weaknesses or risks of the chosen style")

    tradeoffs:              List[str]                 = Field(default_factory=list, description="Trade-offs accepted by this decision")

    rejected_alternatives:  List[RejectedAlternative] = Field(default_factory=list, description="Explanation for styles that ranked highly but were not chosen")

    evidence_ids:           List[str]                 = Field(default_factory=list, description="List of RAG Knowledge Item IDs used to support this recommendation")

    tied_candidates:        List[str]                 = Field(default_factory=list, description="If multiple architectures shared Rank 1, list them here.")

    tie_resolved:           bool                      = Field(default=False, description="Did the LLM successfully resolve the tie using only project information?")

    tie_resolution_reason:  str | None                = Field(None, description="Explanation for how the tie was resolved.")

    review_required:        bool                      = Field(default=False, description="Flag indicating human review is needed (e.g. if a tie was unresolved).")





class RecommendationOutput(BaseModel):

    """

    Complete output of the Architecture Decision Agent – Milestone 4.

    Returned by ArchitectureDesignService.recommend().

    """

    project_id:     str                        = Field(..., description="Project identifier")

    recommendation: ArchitectureRecommendation = Field(...)





# ===========================================================================

# Milestone 5 schemas – High-Level Architecture Design & PlantUML Generate

# ===========================================================================



from typing import List, Optional, Literal



class ArchitectureComponent(BaseModel):

    """A logical building block of the system design."""

    component_id:               str       = Field(..., description="Unique robust identifier for the component (e.g. 'gateway', 'user_db')")

    name:                       str       = Field(..., description="Human-readable name")

    responsibility:             str       = Field(..., description="A concise explanation of what this component does")

    component_type:             str       = Field(..., description="Type classifying the component (e.g. 'database', 'service', 'queue', 'gateway', 'client')")

    grounding_type:             Literal["requirement_derived", "architecture_structural"] = Field(..., description="Is this component derived from business ASRs, or because the architecture style demands it structurally?")

    related_requirements:       List[str] = Field(default_factory=list, description="Project requirement IDs mapped to this component")

    related_quality_attributes: List[QualityAttribute] = Field(default_factory=list, description="Quality Attributes that govern this component")





class ArchitectureConnection(BaseModel):

    """A relationship or data flow between two components."""

    source:                str  = Field(..., description="The component_id of the origin")

    target:                str  = Field(..., description="The component_id of the destination")

    relationship:          str  = Field(..., description="Explanation of the interaction (e.g., 'reads from', 'sends events to')")

    protocol_or_mechanism: str | None = Field(None, description="Technical protocol (e.g., 'HTTP/REST', 'AMQP', 'gRPC')")





class HighLevelArchitectureDesign(BaseModel):

    """The generated architecture structure."""

    style:            str                        = Field(..., description="The finalized Architecture Style name (must match M4 recommendation)")

    components:       List[ArchitectureComponent]  = Field(default_factory=list)

    connections:      List[ArchitectureConnection] = Field(default_factory=list)

    design_rationale: str                        = Field(..., description="Explanation of the generated structure.")

    evidence_ids:     List[str]                  = Field(default_factory=list, description="RAG evidence used to justify the design.")





class ArchitectureDesignOutput(BaseModel):

    """Total output wrapper for M5 containing the recommendation, structured design, and PlantUML."""

    project_id:     str                         = Field(...)

    recommendation: ArchitectureRecommendation  = Field(...)

    design:         HighLevelArchitectureDesign = Field(...)

    plantuml:       str                         = Field(..., description="Deterministically generated PlantUML string representation of the design")





# ===========================================================================

# Milestone 7.3 schemas – Full-Requirement Design Context, Execution Metadata, and Evaluation

# ===========================================================================



class ExecutionMetadata(BaseModel):

    """Metadata tracking agent pipeline execution for scientific reproducibility."""

    pipeline_version:  str            = Field("M7.3", description="Agent pipeline version")

    classifier_name:   str            = Field(..., description="Name of the quality classifier used")

    embedding_model:   str | None     = Field(None, description="Embedding model identifier")

    llm_provider:      str | None     = Field(None, description="LLM provider name")

    llm_model:         str | None     = Field(None, description="LLM model name")

    retrieval_top_k:   int | None     = Field(None, description="Number of knowledge items retrieved")

    execution_time_ms: float          = Field(..., description="Total wall-clock execution duration in milliseconds")





class ArchitectureAnalysisOutput(BaseModel):

    """
    Complete Architecture Decision Agent pipeline output.

    Exposes the intermediate results required for explainability,
    traceability, API consumption, and the Architecture Decision UI.
    """

    project_id: str

    classification: ClassificationOutput

    scoring: ScoringOutput

    retrieval: RetrievalOutput

    result: ArchitectureDesignOutput

    metadata: ExecutionMetadata



class BenchmarkCase(BaseModel):

    """Individual benchmark test case for offline research evaluation."""

    case_id:                     str       = Field(...)

    project_id:                  str       = Field(...)

    title:                       str | None = Field(None)

    status:                      str | None = Field(None)

    asrs:                        List[ASRInput]

    expected_quality_attributes: List[str]

    expected_preferred_styles:   List[str]

    notes:                       str | None = Field(None)



    @field_validator("expected_quality_attributes")

    @classmethod

    def validate_quality_attributes(cls, v: List[str]) -> List[str]:

        valid_qas = {qa.value for qa in QualityAttribute}

        for qa_name in v:

            if qa_name not in valid_qas:

                raise ValueError(

                    f"Unsupported quality attribute: '{qa_name}'. "

                    f"Supported attributes are: {sorted(valid_qas)}"

                )

        return v





class LabelClassificationMetrics(BaseModel):

    """Per-quality-attribute classification performance metrics."""

    precision: float = 0.0

    recall:    float = 0.0

    f1:        float = 0.0

    support:   int   = 0





class ClassificationMetrics(BaseModel):

    """Aggregated multi-label quality attribute classification metrics."""

    micro_precision: float

    micro_recall:    float

    micro_f1:        float

    macro_f1:        float

    per_label:       dict[str, LabelClassificationMetrics] = Field(default_factory=dict)





class RankingMetrics(BaseModel):

    """Architecture ranking performance metrics against acceptable styles."""

    top1_hit_rate:        float

    top3_hit_rate:        float

    mean_reciprocal_rank: float





class StructuralMetrics(BaseModel):

    """Objective structural validity metrics of generated architecture models."""

    requirement_traceability_ratio: float

    qa_traceability_ratio:          float

    valid_connection_ratio:         float

    unsupported_component_count:    int





class EvaluationReport(BaseModel):

    """Complete research evaluation summary report."""

    total_cases:            int

    classification_metrics: ClassificationMetrics

    ranking_metrics:        RankingMetrics

    structural_metrics:     StructuralMetrics | None = None

    pipeline_version:       str = "M7.3"


