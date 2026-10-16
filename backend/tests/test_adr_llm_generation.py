import json
from typing import Any

import pytest

from modules.adr.evidence_aggregator import ADREvidenceAggregator
from modules.adr.llm.llm_adr_generator import LLMADRGenerator
from modules.adr.schemas import ADRGenerationRequest, ADRStatus
from modules.adr.significance_detector import ADRSignificanceDetector
from shared.llm.base import LLMProvider


class FakeADRLLMProvider(LLMProvider):
    """
    Controlled fake LLM provider used only for ADR generator tests.
    """

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        return "Unused in this test."

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        return {
            "title": "Adopt Microservices Architecture",
            "context": (
                "The banking platform requires scalable, available "
                "and independently deployable services."
            ),
            "decision": (
                "Use Microservices as the primary architecture style."
            ),
            "rationale": (
                "Microservices were preferred because they provide "
                "independent deployment, scaling and fault isolation."
            ),
            "alternatives": [
                "Layered Architecture",
                "Modular Monolith",
                "Event-Driven Architecture",
            ],
            "rejected_alternative_reasons": [
                (
                    "Layered Architecture provides limited "
                    "independent scalability."
                ),
                (
                    "Modular Monolith provides weaker "
                    "service-level isolation."
                ),
                (
                    "Event-Driven Architecture was not selected "
                    "as the primary architecture style."
                ),
            ],
            "decision_criteria": [
                "Scalability",
                "Availability",
                "Fault isolation",
                "Maintainability",
                "Independent deployment",
            ],
            "benefits": [
                "Independent service scaling",
                "Improved fault isolation",
                "Independent deployment",
            ],
            "risks": [
                "Higher operational complexity",
                "Distributed system failures",
            ],
            "consequences": [
                (
                    "The platform must manage communication "
                    "between distributed services."
                )
            ],
            "trade_offs": [
                (
                    "Additional operational complexity is accepted "
                    "in exchange for scalability and service independence."
                )
            ],
        }


class MaliciousDecisionLLMProvider(FakeADRLLMProvider):
    """
    Simulates an LLM attempting to modify the source decision.
    """

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        result = await super().generate_structured(
            prompt=prompt,
            response_schema=response_schema,
            temperature=temperature,
        )

        result["decision"] = (
            "Use a monolithic architecture instead."
        )

        return result


def load_mock_decisions() -> ADRGenerationRequest:
    """
    Load the mock DesignTrace AI source-agent decisions.
    """

    with open(
        "datasets/adr/mock_design_decisions.json",
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return ADRGenerationRequest(**data)


def build_evidence():
    """
    Build ADR evidence from the first mock architecture decision.
    """

    request = load_mock_decisions()

    decision = request.decisions[0]

    detector = ADRSignificanceDetector()

    significance = detector.evaluate(
        decision
    )

    aggregator = ADREvidenceAggregator()

    evidence = aggregator.aggregate(
        decision,
        significance,
    )

    return decision, evidence


@pytest.mark.anyio
async def test_llm_adr_generator():
    decision, evidence = build_evidence()

    provider = FakeADRLLMProvider()

    generator = LLMADRGenerator(
        provider=provider
    )

    adr = await generator.generate(
        evidence=evidence,
        adr_number=1,
    )

    assert (
        adr.adr_id
        == "BANKING-ADR-001-ADR-001"
    )

    assert (
        adr.status
        == ADRStatus.PROPOSED
    )

    assert (
        adr.title
        == "Adopt Microservices Architecture"
    )

    assert (
        "independent deployment"
        in adr.rationale.lower()
    )

    assert len(adr.benefits) > 0
    assert len(adr.risks) > 0
    assert len(adr.trade_offs) > 0

    assert (
        adr.traceability.requirement_ids
        == decision.requirement_ids
    )

    assert (
        adr.traceability.design_element_ids
        == decision.design_element_ids
    )

    assert (
        adr.traceability.source_decision_ids
        == [decision.decision_id]
    )

    assert (
        adr.traceability.source_modules
        == [decision.source_module]
    )

    # The original source decision must remain authoritative.
    assert (
        adr.decision
        == decision.decision
    )


@pytest.mark.anyio
async def test_llm_cannot_change_source_decision():
    decision, evidence = build_evidence()

    provider = MaliciousDecisionLLMProvider()

    generator = LLMADRGenerator(
        provider=provider
    )

    adr = await generator.generate(
        evidence=evidence,
        adr_number=1,
    )

    # The ADR generator must keep the original decision.
    assert (
        adr.decision
        == decision.decision
    )

    assert (
        adr.decision
        != "Use a monolithic architecture instead."
    )