"""
LLM-assisted Architecture Decision Record generation.

The LLM improves explanatory ADR content while deterministic code retains
control over source decisions, identifiers, lifecycle state, traceability,
timestamps, and other system-managed metadata.
"""

from datetime import datetime, timezone
from typing import Any

from modules.adr.evidence_aggregator import ADREvidencePackage
from modules.adr.llm.prompt import build_adr_generation_prompt
from modules.adr.schemas import (
    ADRGenerationMethod,
    ADRRecord,
    ADRStatus,
    ADRTraceability,
)
from shared.llm.base import LLMProvider


ADR_LLM_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
        },
        "context": {
            "type": "string",
        },
        "decision": {
            "type": "string",
        },
        "rationale": {
            "type": "string",
        },
        "alternatives": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "rejected_alternative_reasons": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "decision_criteria": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "benefits": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "risks": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "consequences": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "trade_offs": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
    },
    "required": [
        "title",
        "context",
        "decision",
        "rationale",
        "alternatives",
        "rejected_alternative_reasons",
        "decision_criteria",
        "benefits",
        "risks",
        "consequences",
        "trade_offs",
    ],
}


class LLMADRGenerator:
    """
    Generates ADR explanatory content using a shared LLM provider.
    """

    def __init__(
        self,
        provider: LLMProvider,
    ):
        self.provider = provider

    async def generate(
        self,
        evidence: ADREvidencePackage,
        adr_number: int,
    ) -> ADRRecord:
        """
        Generate an ADR using LLM-assisted explanatory content.
        """

        prompt = build_adr_generation_prompt(
            evidence
        )

        generated = await self.provider.generate_structured(
            prompt=prompt,
            response_schema=ADR_LLM_RESPONSE_SCHEMA,
            temperature=0.0,
        )

        adr_id = self._build_adr_id(
            project_id=evidence.project_id,
            adr_number=adr_number,
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
            title=self._get_text(
                generated,
                "title",
                evidence.title,
            ),
            status=ADRStatus.PROPOSED,
            generation_method=ADRGenerationMethod.LLM,
            context=self._get_text(
                generated,
                "context",
                evidence.context,
            ),

            # The source decision remains authoritative.
            # The LLM may explain it but cannot modify it.
            decision=evidence.selected_decision,

            rationale=self._get_text(
                generated,
                "rationale",
                evidence.rationale
                or "Decision selected based on available evidence.",
            ),
            alternatives=self._get_list(
                generated,
                "alternatives",
                evidence.alternatives,
            ),
            rejected_alternative_reasons=self._get_list(
                generated,
                "rejected_alternative_reasons",
                evidence.rejected_alternative_reasons,
            ),
            decision_criteria=self._get_list(
                generated,
                "decision_criteria",
                evidence.decision_criteria,
            ),
            benefits=self._get_list(
                generated,
                "benefits",
                evidence.benefits,
            ),
            risks=self._get_list(
                generated,
                "risks",
                evidence.risks,
            ),
            consequences=self._get_list(
                generated,
                "consequences",
                evidence.consequences,
            ),
            trade_offs=self._get_list(
                generated,
                "trade_offs",
                evidence.trade_offs,
            ),
            evidence=evidence.supporting_evidence,
            confidence=evidence.source_confidence,
            traceability=traceability,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _get_text(
        generated: dict[str, Any],
        field: str,
        fallback: str,
    ) -> str:
        """
        Return a generated string or deterministic fallback.
        """

        value = generated.get(field)

        if (
            isinstance(value, str)
            and value.strip()
        ):
            return value.strip()

        return fallback

    @staticmethod
    def _get_list(
        generated: dict[str, Any],
        field: str,
        fallback: list[str],
    ) -> list[str]:
        """
        Return a generated string list or deterministic fallback.
        """

        value = generated.get(field)

        if not isinstance(value, list):
            return fallback

        cleaned = [
            item.strip()
            for item in value
            if (
                isinstance(item, str)
                and item.strip()
            )
        ]

        if not cleaned:
            return fallback

        return cleaned

    @staticmethod
    def _build_adr_id(
        project_id: str,
        adr_number: int,
    ) -> str:
        """
        Generate a deterministic project-specific ADR ID.
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