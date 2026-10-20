"""Upstream architecture and database contracts used by quality input adapters."""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class ModuleArtifact(BaseModel):
    # Ignore unrelated upstream metadata; keep only explicitly declared fields.
    model_config = ConfigDict(extra='ignore')


class ArchitectureComponent(ModuleArtifact):
    component_id: str
    name: str
    type: str
    responsibilities: list[str]
    requirement_ids: list[str] = Field(default_factory=list)


class HighLevelDesign(ModuleArtifact):
    architecture_style: str
    components: list[ArchitectureComponent]
    relationships: list[dict[str, Any]] = Field(default_factory=list)


class ForeignKeyReference(ModuleArtifact):
    table: str
    column: str


class DatabaseColumn(ModuleArtifact):
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    foreign_key: ForeignKeyReference | None = None
    source_requirement_ids: list[str] = Field(default_factory=list)


class DatabaseTable(ModuleArtifact):
    table_name: str
    purpose: str | None = None
    columns: list[DatabaseColumn]
    source_requirement_ids: list[str] = Field(default_factory=list)


class DatabaseModuleDesign(ModuleArtifact):
    tables: list[DatabaseTable]
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class AnalyzedRequirement(ModuleArtifact):
    requirement_id: str = Field(min_length=1)
    normalized_statement: str = Field(min_length=1)
    requirement_type: Literal['FR', 'NFR']
    quality_attribute: str | None = None


class RequirementAnalysisArtifact(ModuleArtifact):
    project_id: str
    requirements: list[AnalyzedRequirement]
