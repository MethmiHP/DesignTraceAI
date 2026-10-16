"""
Evidence aggregation for Architecture Decision Record generation.

This module converts a significant design decision into a structured
evidence package that can be used by the ADR generator.
"""

from pydantic import BaseModel, Field

from modules.adr.schemas import (
    DesignDecision,
    DecisionSource,
    SignificanceResult,
)


class ADREvidencePackage(BaseModel):
    """
    Structured evidence collected for ADR generation.
    """

    decision_id: str

    project_id: str

    source_module: DecisionSource

    title: str

    context: str

    selected_decision: str

    rationale: str | None = None

    alternatives: list[str] = Field(default_factory=list)

    rejected_alternative_reasons: list[str] = Field(
        default_factory=list
    )

    decision_criteria: list[str] = Field(default_factory=list)

    benefits: list[str] = Field(default_factory=list)

    risks: list[str] = Field(default_factory=list)

    consequences: list[str] = Field(default_factory=list)

    trade_offs: list[str] = Field(default_factory=list)

    requirement_ids: list[str] = Field(default_factory=list)

    design_element_ids: list[str] = Field(default_factory=list)

    supporting_evidence: list[str] = Field(default_factory=list)

    source_confidence: float | None = None

    significance_score: float

    significance_reasons: list[str] = Field(default_factory=list)


class ADREvidenceAggregator:
    """
    Collects ADR-relevant evidence from a significant source decision.
    """

    def aggregate(
        self,
        decision: DesignDecision,
        significance: SignificanceResult,
    ) -> ADREvidencePackage:
        """
        Build a structured evidence package for ADR generation.
        """

        if decision.decision_id != significance.decision_id:
            raise ValueError(
                "Decision ID and significance result ID do not match."
            )

        if not significance.significant:
            raise ValueError(
                "Evidence should only be aggregated for "
                "significant design decisions."
            )

        return ADREvidencePackage(
            decision_id=decision.decision_id,
            project_id=decision.project_id,
            source_module=decision.source_module,
            title=decision.title,
            context=decision.context,
            selected_decision=decision.decision,
            rationale=decision.rationale,
            alternatives=self._unique(decision.alternatives),
            rejected_alternative_reasons=self._unique(
                decision.rejected_alternative_reasons
            ),
            decision_criteria=self._unique(
                decision.decision_criteria
            ),
            benefits=self._unique(decision.benefits),
            risks=self._unique(decision.risks),
            consequences=self._unique(decision.consequences),
            trade_offs=self._unique(decision.trade_offs),
            requirement_ids=self._unique(
                decision.requirement_ids
            ),
            design_element_ids=self._unique(
                decision.design_element_ids
            ),
            supporting_evidence=self._unique(
                decision.evidence
            ),
            source_confidence=decision.confidence,
            significance_score=significance.score,
            significance_reasons=self._unique(
                significance.reasons
            ),
        )

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        """
        Remove duplicates while preserving the original order.
        """

        seen = set()
        unique_values = []

        for value in values:
            normalized = value.strip()

            if not normalized:
                continue

            key = normalized.lower()

            if key not in seen:
                seen.add(key)
                unique_values.append(normalized)

        return unique_values