#what the module receives from the Coordinator Agent and what it returns

from typing import Optional
from pydantic import BaseModel, Field

from shared.models.common import ValidationResult



# INPUT MODELS
class FunctionalRequirement(BaseModel):
    requirement_id: str
    statement: str
    priority: Optional[str] = None


class NonFunctionalRequirement(BaseModel):
    requirement_id: str
    statement: str
    category: Optional[str] = None


class ArchitectureElement(BaseModel):
    element_id: str
    name: str
    type: str
    main_responsibility: str


class ArchitectureDesign(BaseModel):
    architecture_id: Optional[str] = None
    selected_architecture: Optional[str] = None
    elements: list[ArchitectureElement]


class DatabaseEntity(BaseModel):
    entity_id: Optional[str] = None
    name: str
    attributes: list[str]

    primary_key: Optional[str] = None
    foreign_keys: list[str] = Field(default_factory=list)

    constraints: list[str] = Field(default_factory=list)


class DatabaseDesign(BaseModel):
    entities: list[DatabaseEntity]

    relationships: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class APIComponentDesignRequest(BaseModel):
    project_id: str

    functional_requirements: list[FunctionalRequirement]

    architecture: ArchitectureDesign

    database: DatabaseDesign

    # Optional because your main API-design inputs are
    # FR + Architecture + Database.
    non_functional_requirements: list[NonFunctionalRequirement] = Field(
        default_factory=list
    )



# INTERNAL / OUTPUT MODELS

class SemanticExtraction(BaseModel):
    requirement_id: str

    actor: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None

    confidence: Optional[float] = None


class ResponsibilityDesign(BaseModel):
    requirement_id: str

    element_id: str
    element_name: str

    detailed_responsibility: str

    mapping_reason: Optional[str] = None


class APIOperation(BaseModel):
    operation_id: str

    requirement_id: str
    element_id: str

    method: str
    path: str

    request_schema: dict = Field(default_factory=dict)
    response_schema: dict = Field(default_factory=dict)

    error_responses: dict = Field(default_factory=dict)


class RequirementAPIMapping(BaseModel):
    requirement_id: str
    operation_id: str


class APIComponentDesignResponse(BaseModel):
    project_id: str

    semantic_extractions: list[SemanticExtraction]

    responsibilities: list[ResponsibilityDesign]

    api_operations: list[APIOperation]

    requirement_to_api_mapping: list[
        RequirementAPIMapping
    ]

    openapi_document: dict = Field(
        default_factory=dict
    )

    validation: ValidationResult

    