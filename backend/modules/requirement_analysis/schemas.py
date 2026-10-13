# Defines the input and output data structures used by the Requirement Analysis Module
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


# INPUT MODELS
class ProjectContext(BaseModel):
    domain: Optional[str] = None
    system_type: Optional[str] = None

    primary_users: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    technology_preferences: list[str] = Field(default_factory=list)


class RequirementAnalysisRequest(BaseModel):
    project_id: str = Field(..., min_length=1)

    raw_description: str = Field(
        ...,
        min_length=10,
        description="Raw natural-language project description"
    )

    project_context: ProjectContext = Field(
        default_factory=ProjectContext
    )


# QUALITY ISSUE MODELS
class RequirementQualityIssues(BaseModel):
    ambiguous: bool = False
    incomplete: bool = False
    conflicting: bool = False
    potentially_missing: bool = False


class IssueDetail(BaseModel):
    issue_type: Literal[
        "ambiguity",
        "incompleteness",
        "conflict",
        "potentially_missing"
    ]

    evidence: Optional[str] = None
    rationale: str
    recommendation: Optional[str] = None



# REQUIREMENT MODEL
class AnalyzedRequirement(BaseModel):

    requirement_id: str

    original_text: str

    normalized_statement: str

    requirement_type: Literal["FR", "NFR"]

    quality_attribute: Optional[str] = None

    asr: bool = False

    quality_issues: RequirementQualityIssues = Field(
        default_factory=RequirementQualityIssues
    )

    issue_details: list[IssueDetail] = Field(
        default_factory=list
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    @field_validator("quality_attribute")
    @classmethod
    def validate_quality_attribute(cls, value):
        if value is None:
            return value

        value = value.strip()

        return value if value else None



# SUMMARY
class RequirementSummary(BaseModel):

    total_requirements: int = 0

    functional_requirements: int = 0

    non_functional_requirements: int = 0

    asr_count: int = 0

    ambiguous_count: int = 0

    incomplete_count: int = 0

    conflict_count: int = 0

    potentially_missing_count: int = 0



# VALIDATION
class RequirementValidationResult(BaseModel):

    valid: bool

    issues: list[str] = Field(default_factory=list)



# FINAL RESPONSE
class RequirementAnalysisResponse(BaseModel):

    project_id: str

    requirements: list[AnalyzedRequirement]

    summary: RequirementSummary

    generated_srs: str

    validation: RequirementValidationResult