from typing import Literal

from pydantic import BaseModel, Field


class LLMQualityAssessment(BaseModel):
    status: Literal[
        "PASS",
        "FAIL",
        "SKIPPED",
    ]

    evidence: list[str] = Field(
        default_factory=list
    )

    rationale: str

    affected_nfr_ids: list[str] = Field(
        default_factory=list
    )

    confidence: float | None = None

    recommendation: str | None = None