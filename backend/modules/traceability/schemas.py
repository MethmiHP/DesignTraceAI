#Defines the input, output, trace-link, coverage, and validation
#schemas used by the Traceability Module.

from typing import List, Optional, Literal

from pydantic import BaseModel, Field



# REQUIREMENT INPUT

class TraceabilityRequirement(BaseModel):
    """
    Structured requirement received from the
    Requirement Analysis module.
    """

    requirement_id: str
    statement: str
    requirement_type: Literal["FR", "NFR"]
    asr: bool = False



# ARCHITECTURE ARTIFACT

class ArchitectureArtifact(BaseModel):
    artifact_id: str
    name: str
    type: str
    description: str


class ArchitectureInput(BaseModel):
    elements: List[ArchitectureArtifact] = Field(
        default_factory=list
    )



# DATABASE ARTIFACT

class DatabaseArtifact(BaseModel):
    artifact_id: str
    name: str
    description: str


class DatabaseInput(BaseModel):
    entities: List[DatabaseArtifact] = Field(
        default_factory=list
    )



# API ARTIFACT

class APIArtifact(BaseModel):
    artifact_id: str
    method: str
    path: str
    description: str


class APIInput(BaseModel):
    operations: List[APIArtifact] = Field(
        default_factory=list
    )



# SOFTWARE COMPONENT ARTIFACT

class ComponentArtifact(BaseModel):
    artifact_id: str
    name: str
    description: str



# TRACEABILITY REQUEST

class TraceabilityRequest(BaseModel):
    """
    Complete input for the Traceability module.
    """

    project_id: str

    requirements: List[
        TraceabilityRequirement
    ]

    architecture: ArchitectureInput = Field(
        default_factory=ArchitectureInput
    )

    database: DatabaseInput = Field(
        default_factory=DatabaseInput
    )

    api: APIInput = Field(
        default_factory=APIInput
    )

    components: List[
        ComponentArtifact
    ] = Field(
        default_factory=list
    )



# NORMALIZED DESIGN ARTIFACT

class NormalizedArtifact(BaseModel):
    """
    Common representation used internally before
    SBERT embedding generation.
    """

    artifact_id: str

    artifact_type: Literal[
        "architecture",
        "database",
        "api",
        "component"
    ]

    name: str

    description: str

    normalized_text: str



# CANDIDATE TRACE LINK

class CandidateTraceLink(BaseModel):
    """
    Candidate produced by SBERT + cosine similarity.
    """

    requirement_id: str

    artifact_id: str

    artifact_type: Literal[
        "architecture",
        "database",
        "api",
        "component"
    ]

    semantic_similarity: float


# FINAL VALIDATED TRACE LINK

class TraceLink(BaseModel):
    """
    Final requirement-to-design trace link.
    """

    requirement_id: str

    artifact_id: str

    artifact_type: Literal[
        "architecture",
        "database",
        "api",
        "component"
    ]

    link_valid: bool

    semantic_similarity: float

    confidence: float

    rationale: str



# TRACEABILITY MATRIX ROW

class TraceabilityMatrixRow(BaseModel):
    requirement_id: str

    architecture_links: List[str] = Field(
        default_factory=list
    )

    database_links: List[str] = Field(
        default_factory=list
    )

    api_links: List[str] = Field(
        default_factory=list
    )

    component_links: List[str] = Field(
        default_factory=list
    )

    coverage_status: Literal[
        "FULLY_COVERED",
        "PARTIALLY_COVERED",
        "UNCOVERED"
    ]



# COVERAGE SUMMARY

class CoverageSummary(BaseModel):
    
    # Summarizes two different kinds of traceability coverage:

    # 1. Requirement coverage:
    #    Whether each requirement has at least one valid design trace.

    # 2. Artifact-category coverage:
    #    How many of the four design artifact categories
    #    (architecture, database, API, component)
    #    are represented for each requirement.
    

    total_requirements: int = 0

    # Requirement-level coverage
    requirements_with_links: int = 0

    requirements_without_links: int = 0

    requirement_coverage_percentage: float = 0.0


    # Artifact-category coverage
    fully_covered: int = 0

    partially_covered: int = 0

    uncovered: int = 0

    average_artifact_category_coverage_percentage: float = 0.0



# EVALUATION METRICS

class TraceabilityEvaluation(BaseModel):
    """
    Filled when predicted links are compared against
    human-reviewed gold links.
    """

    precision: Optional[float] = None

    recall: Optional[float] = None

    f1_score: Optional[float] = None



# VALIDATION RESULT

class TraceabilityValidationResult(BaseModel):
    valid: bool

    issues: List[str] = Field(
        default_factory=list
    )


# TRACEABILITY RESPONSE

class TraceabilityResponse(BaseModel):
    project_id: str

    trace_links: List[
        TraceLink
    ] = Field(
        default_factory=list
    )

    traceability_matrix: List[
        TraceabilityMatrixRow
    ] = Field(
        default_factory=list
    )

    coverage_summary: CoverageSummary

    evaluation: Optional[
        TraceabilityEvaluation
    ] = None

    validation: TraceabilityValidationResult