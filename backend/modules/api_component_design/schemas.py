#what the module receives from the Coordinator Agent and what it returns

from typing import Literal, Optional
from pydantic import BaseModel, Field, HttpUrl, model_validator

from shared.models.common import ValidationResult



# INPUT MODELS
class OAuthFlow(BaseModel):
    authorizationUrl: HttpUrl | None = None
    tokenUrl: HttpUrl | None = None
    refreshUrl: HttpUrl | None = None
    scopes: dict[str, str]


class SecurityPolicy(BaseModel):
    authentication: Literal["unspecified", "none", "bearer", "basic", "api_key", "oauth2", "openid_connect", "mutual_tls", "custom"] = "unspecified"
    api_key_name: str = Field(default="X-API-Key", min_length=1, pattern=r"^[A-Za-z0-9_-]+$")
    api_key_location: Literal["header", "query", "cookie"] = "header"
    roles: list[str] = Field(default_factory=list)
    access_rules: list[str] = Field(default_factory=list)
    oauth_flows: dict[Literal["implicit", "password", "clientCredentials", "authorizationCode"], OAuthFlow] = Field(default_factory=dict)
    openid_connect_url: HttpUrl | None = None
    custom_description: str | None = None

    @model_validator(mode="after")
    def validate_oauth_flows(self):
        for name, flow in self.oauth_flows.items():
            if name in {"implicit", "authorizationCode"} and not flow.authorizationUrl:
                raise ValueError(f"{name} requires authorizationUrl")
            if name != "implicit" and not flow.tokenUrl:
                raise ValueError(f"{name} requires tokenUrl")
        return self


class FunctionalRequirement(BaseModel):
    requirement_id: str
    statement: str
    priority: Optional[str] = None
    security: Optional[SecurityPolicy] = None


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
    security: SecurityPolicy = Field(default_factory=SecurityPolicy)
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


class APIParameter(BaseModel):
    name: str = Field(min_length=1)
    location: Literal["path", "query", "header"]
    type: Literal["string", "uuid", "integer", "number", "boolean"] = "string"
    required: bool = False
    description: str = ""


class APIOperation(BaseModel):
    security: SecurityPolicy = Field(default_factory=SecurityPolicy)
    generation_source: Optional[Literal["gemini", "groq", "rule-based", "llm"]] = None
    operation_id: str

    requirement_id: str
    element_id: str

    method: str
    path: str

    request_schema: dict = Field(default_factory=dict)
    response_schema: dict = Field(default_factory=dict)

    error_responses: dict = Field(default_factory=dict)
    parameters: list[APIParameter] = Field(default_factory=list)


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

    
