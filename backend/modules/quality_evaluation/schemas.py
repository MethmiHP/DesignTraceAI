from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from .module_artifacts import ModuleArtifact, HighLevelDesign, DatabaseModuleDesign, RequirementAnalysisArtifact, DatabaseColumn


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


class ArchitectureElement(ModuleArtifact):
    requirement_ids: list[str] = Field(default_factory=list)
    element_id: str
    name: str
    type: str
    main_responsibility: str


class ArchitectureDesign(ModuleArtifact):
    project_id: str | None = Field(default=None, exclude=True)
    high_level_design: HighLevelDesign | None = Field(default=None, exclude=True)
    relationships: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode='after')
    def adapt_module_output(self):
        if self.high_level_design is not None:
            self.selected_architecture = self.high_level_design.architecture_style
            self.relationships = self.high_level_design.relationships
            self.elements = [ArchitectureElement(
                element_id=component.component_id,
                name=component.name,
                type=component.type,
                main_responsibility='; '.join(component.responsibilities),
                requirement_ids=component.requirement_ids,
            ) for component in self.high_level_design.components]
        return self

    architecture_id: Optional[str] = None
    selected_architecture: Optional[str] = None
    elements: list[ArchitectureElement] = Field(
        default_factory=list
    )


class DatabaseEntity(ModuleArtifact):
    columns: list[DatabaseColumn] = Field(default_factory=list)
    source_requirement_ids: list[str] = Field(default_factory=list)
    purpose: str | None = None
    entity_id: Optional[str] = None
    name: str
    attributes: list[str] = Field(
        default_factory=list
    )

    primary_key: str | list[str] | None = None

    foreign_keys: list[str] = Field(
        default_factory=list
    )

    constraints: list[str] = Field(
        default_factory=list
    )


class DatabaseDesign(ModuleArtifact):
    project_id: str | None = Field(default=None, exclude=True)
    design: DatabaseModuleDesign | None = Field(default=None, exclude=True)

    @model_validator(mode='after')
    def adapt_module_output(self):
        if self.design is not None:
            entities = []
            for table in self.design.tables:
                keys = [column.name for column in table.columns if column.primary_key]
                entities.append(DatabaseEntity(
                    name=table.table_name,
                    attributes=[column.name for column in table.columns],
                    primary_key=keys[0] if len(keys) == 1 else keys or None,
                    foreign_keys=[
                        f'{column.name} -> {column.foreign_key.table}.{column.foreign_key.column}'
                        for column in table.columns if column.foreign_key is not None
                    ],
                    constraints=[
                        f'UNIQUE ({column.name})' for column in table.columns if column.unique
                    ] + [
                        f'{column.name} NOT NULL' for column in table.columns if not column.nullable
                    ],
                    columns=[column.model_dump(mode='json') for column in table.columns],
                    source_requirement_ids=table.source_requirement_ids,
                    purpose=table.purpose,
                ))
            self.entities = entities
            self.relationships = self.design.relationships
            self.constraints = self.design.constraints
        return self

    entities: list[DatabaseEntity] = Field(
        default_factory=list
    )

    relationships: list[str | dict[str, Any]] = Field(
        default_factory=list
    )

    constraints: list[str] = Field(
        default_factory=list
    )


class ComponentResponsibility(ModuleArtifact):
    requirement_id: Optional[str] = None

    element_id: str
    element_name: Optional[str] = None

    detailed_responsibility: str

    mapping_reason: Optional[str] = None


class APIOperationArtifact(ModuleArtifact):
    security: dict[str, Any] | None = None
    parameters: list[dict[str, Any]] = Field(default_factory=list)

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


class APIComponentArtifact(ModuleArtifact):
    project_id: str | None = Field(default=None, exclude=True)
    requirement_to_api_mapping: list[dict[str, Any]] = Field(default_factory=list)

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
    requirement_analysis: RequirementAnalysisArtifact | None = Field(default=None, exclude=True)

    @model_validator(mode='after')
    def adapt_requirement_analysis(self):
        analysis = self.requirement_analysis
        if analysis is None:
            return self
        if analysis.project_id.strip() != self.project_id.strip():
            raise ValueError('requirement_analysis.project_id must match the evaluation project_id')
        functional, non_functional = [], []
        seen = set()
        categories = {category.value.casefold(): category for category in NFRCategory}
        for requirement in analysis.requirements:
            identifier = requirement.requirement_id.strip()
            statement = requirement.normalized_statement.strip()
            if not identifier or not statement:
                raise ValueError('Analyzed requirements must have a non-empty ID and normalized_statement')
            if identifier in seen:
                raise ValueError(f'Duplicate analyzed requirement ID: {identifier}')
            seen.add(identifier)
            if requirement.requirement_type == 'FR':
                functional.append(FunctionalRequirement(requirement_id=identifier, statement=statement))
            else:
                category = categories.get((requirement.quality_attribute or '').strip().casefold())
                if category is None:
                    raise ValueError(
                        f'{identifier}: NFR quality_attribute must be a supported category; '
                        f'received {requirement.quality_attribute!r}. Supported: '
                        + ', '.join(category.value for category in NFRCategory)
                    )
                non_functional.append(NonFunctionalRequirement(
                    requirement_id=identifier, statement=statement, category=category,
                ))
        for field, derived in [('functional_requirements', functional), ('non_functional_requirements', non_functional)]:
            if field in self.model_fields_set and getattr(self, field) != derived:
                raise ValueError(f'Supply requirement_analysis or matching {field}, not conflicting requirement sources')
            setattr(self, field, derived)
        return self

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

    @model_validator(mode='after')
    def consistent_project_ids(self):
        for field in ('architecture', 'database', 'api_component_design'):
            artifact = getattr(self, field)
            if artifact.project_id is not None and artifact.project_id.strip() != self.project_id.strip():
                raise ValueError(f'{field}.project_id must match the evaluation project_id')
        return self


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
    applicability_handler: str | None = None

    check_type: CheckType

    handler: Optional[str] = None
    semantic_instruction: Optional[str] = None

    severity_default: Severity

    evidence_required: bool = True

    recommendation_template: str

    always_apply: bool = False

    # Optional key used to group related findings
    finding_group: str | None = None


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

    recommendation: str | None = None


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

    quality_pass_percentage: float | None = None

    applicable_nfrs: int
    evaluated_nfrs: int

    nfr_coverage_percentage: float | None = None

    category_summaries: list[
        CategoryQualitySummary
    ] = Field(
        default_factory=list
    )

class QualityFindingGroup(BaseModel):
    group_id: str
    group_key: str
    title: str
    quality_attribute: str
    severity: Severity
    finding_ids: list[str]
    rule_ids: list[str]
    affected_nfr_ids: list[str]
    recommendations: list[str]
    summary: str


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

    finding_groups: list[QualityFindingGroup] = Field(
    default_factory=list
)

