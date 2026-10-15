from typing import Optional
from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: str = "ERROR"
    field: Optional[str] = None


class ValidationResult(BaseModel):
    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)


class ArtifactMetadata(BaseModel):
    project_id: str
    artifact_id: str
    source_module: str
    source_requirement_ids: list[str] = Field(default_factory=list)


class ModelMetadata(BaseModel):
    provider: Optional[str] = None
    model_name: Optional[str] = None
    confidence: Optional[float] = None