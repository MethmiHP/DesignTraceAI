from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class NFRCategory(str, Enum):
    AVAILABILITY = "Availability"
    FAULT_TOLERANCE = "Fault Tolerance"
    LEGAL = "Legal"
    LOOK_AND_FEEL = "Look and Feel"
    MAINTAINABILITY = "Maintainability"
    OPERATIONAL = "Operational"
    PERFORMANCE = "Performance"
    PORTABILITY = "Portability"
    SCALABILITY = "Scalability"
    SECURITY = "Security"
    USABILITY = "Usability"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CheckType(str, Enum):
    DETERMINISTIC = "deterministic"
    SEMANTIC = "semantic"


class RuleStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


# Coordinator input models

class FunctionalRequirement(BaseModel):
    requirement_id: str
    statement: str
    priority: Optional[str] = None


class NonFunctionalRequirement(BaseModel):
    requirement_id: str
    statement: str
    category: NFRCategory
    priority: Optional[str] = None


class ArchitectureElement(BaseModel):
    element_id: str
    name: str
    type: str
    main_responsibility: str


class ArchitectureDesign(BaseModel):
    architecture_id: Optional[str] = None
    selected_architecture: Optional[str] = None
    elements: list[ArchitectureElement] = Field(
        default_factory=list
    )


class DatabaseEntity(BaseModel):
    entity_id: Optional[str] = None
    name: str
    attributes: list[str] = Field(
        default_factory=list
    )

    primary_key: Optional[str] = None

    foreign_keys: list[str] = Field(
        default_factory=list
    )

    constraints: list[str] = Field(
        default_factory=list
    )


class DatabaseDesign(BaseModel):
    entities: list[DatabaseEntity] = Field(
        default_factory=list
    )

    relationships: list[str] = Field(
        default_factory=list
    )

    constraints: list[str] = Field(
        default_factory=list
    )


class ComponentResponsibility(BaseModel):
    requirement_id: Optional[str] = None

    element_id: str
    element_name: Optional[str] = None

    detailed_responsibility: str

    mapping_reason: Optional[str] = None


class APIOperationArtifact(BaseModel):
    operation_id: str

    requirement_id: Optional[str] = None
    element_id: Optional[str] = None

    method: str
    path: str

    request_schema: dict[str, Any] = Field(
        default_factory=dict
    )

    response_schema: dict[str, Any] = Field(
        default_factory=dict
    )

    error_responses: dict[str, Any] = Field(
        default_factory=dict
    )


class APIComponentArtifact(BaseModel):
    responsibilities: list[
        ComponentResponsibility
    ] = Field(
        default_factory=list
    )

    api_operations: list[
        APIOperationArtifact
    ] = Field(
        default_factory=list
    )

    openapi_document: dict[str, Any] = Field(
        default_factory=dict
    )


class QualityEvaluationRequest(BaseModel):
    project_id: str

    functional_requirements: list[
        FunctionalRequirement
    ] = Field(
        default_factory=list
    )

    non_functional_requirements: list[
        NonFunctionalRequirement
    ] = Field(
        default_factory=list
    )

    architecture: ArchitectureDesign

    database: DatabaseDesign

    api_component_design: APIComponentArtifact


# Knowledge-base models

class QualityRule(BaseModel):
    rule_id: str
    title: str

    source: str

    artifact_types: list[str] = Field(
        default_factory=list
    )

    quality_attribute: NFRCategory

    nfr_categories: list[NFRCategory] = Field(
        default_factory=list
    )

    applicability: str

    check_type: CheckType

    handler: Optional[str] = None
    semantic_instruction: Optional[str] = None

    severity_default: Severity

    evidence_required: bool = True

    recommendation_template: str

    always_apply: bool = False


# Evaluation models

class RuleEvaluationResult(BaseModel):
    rule_id: str

    quality_attribute: NFRCategory

    check_type: CheckType

    status: RuleStatus

    evidence: list[str] = Field(
        default_factory=list
    )

    rationale: str

    affected_nfr_ids: list[str] = Field(
        default_factory=list
    )

    confidence: Optional[float] = None

    provider: Optional[str] = None


class QualityFinding(BaseModel):
    finding_id: str

    rule_id: str

    artifact_type: str

    quality_attribute: NFRCategory

    check_type: CheckType

    severity: Severity

    affected_nfr_ids: list[str] = Field(
        default_factory=list
    )

    evidence: list[str] = Field(
        default_factory=list
    )

    rationale: str

    recommendation: str


class CategoryQualitySummary(BaseModel):
    category: NFRCategory

    applicable_rules: int
    passed_rules: int
    failed_rules: int
    skipped_rules: int

    pass_percentage: Optional[float] = None

    applicable_nfrs: int
    evaluated_nfrs: int

    nfr_coverage_percentage: Optional[float] = None


class QualityMetrics(BaseModel):
    total_applicable_rules: int

    passed_rules: int
    failed_rules: int
    skipped_rules: int

    quality_pass_percentage: float

    applicable_nfrs: int
    evaluated_nfrs: int

    nfr_coverage_percentage: float

    category_summaries: list[
        CategoryQualitySummary
    ] = Field(
        default_factory=list
    )


class QualityEvaluationResponse(BaseModel):
    project_id: str
    evaluation_id: str

    applicable_rule_ids: list[str]

    rule_results: list[
        RuleEvaluationResult
    ]

    findings: list[
        QualityFinding
    ]

    metrics: QualityMetrics

    summary: str

    generated_at: str