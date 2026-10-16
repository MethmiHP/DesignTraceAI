"""
Deterministic Architecture Decision Record generation.

This generator acts as the baseline ADR generator and as a safe fallback
when the external LLM provider is unavailable.
"""

from datetime import datetime, timezone

from modules.adr.evidence_aggregator import ADREvidencePackage
from modules.adr.schemas import (
    ADRGenerationMethod,
    ADRRecord,
    ADRStatus,
    ADRTraceability,
)


class ADRGenerator:
    """
    Generates a structured ADR directly from aggregated evidence.
    """

    def generate(
        self,
        evidence: ADREvidencePackage,
        adr_number: int,
    ) -> ADRRecord:
        """
        Generate a deterministic ADR using available source evidence.
        """

        adr_id = self._build_adr_id(
            project_id=evidence.project_id,
            adr_number=adr_number,
        )

        rationale = evidence.rationale or (
            "The selected option was chosen based on the available "
            "design evidence and decision criteria."
        )

        traceability = ADRTraceability(
            requirement_ids=evidence.requirement_ids,
            design_element_ids=evidence.design_element_ids,
            source_decision_ids=[
                evidence.decision_id
            ],
            source_modules=[
                evidence.source_module
            ],
        )

        now = datetime.now(
            timezone.utc
        )

        return ADRRecord(
            adr_id=adr_id,
            project_id=evidence.project_id,
            title=evidence.title,
            status=ADRStatus.PROPOSED,
            generation_method=ADRGenerationMethod.DETERMINISTIC,
            context=evidence.context,
            decision=evidence.selected_decision,
            rationale=rationale,
            alternatives=evidence.alternatives,
            rejected_alternative_reasons=(
                evidence.rejected_alternative_reasons
            ),
            decision_criteria=evidence.decision_criteria,
            benefits=evidence.benefits,
            risks=evidence.risks,
            consequences=evidence.consequences,
            trade_offs=evidence.trade_offs,
            evidence=evidence.supporting_evidence,
            confidence=evidence.source_confidence,
            traceability=traceability,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _build_adr_id(
        project_id: str,
        adr_number: int,
    ) -> str:
        """
        Build a stable project-specific ADR identifier.
        """

        if adr_number < 1:
            raise ValueError(
                "ADR number must be greater than zero."
            )

        normalized_project_id = (
            project_id
            .strip()
            .upper()
            .replace(" ", "-")
        )

        return (
            f"{normalized_project_id}"
            f"-ADR-{adr_number:03d}"
        )