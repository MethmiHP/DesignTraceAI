from pydantic import BaseModel, Field


class ExtractedConcepts(BaseModel):
    entities: list[str] = Field(default_factory=list)
    attributes: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
