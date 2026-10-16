import json

from modules.adr.adr_generator import ADRGenerator
from modules.adr.evidence_aggregator import ADREvidenceAggregator
from modules.adr.schemas import ADRGenerationRequest, ADRStatus
from modules.adr.significance_detector import ADRSignificanceDetector


def load_mock_decisions():
    with open(
        "datasets/adr/mock_design_decisions.json",
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return ADRGenerationRequest(**data)


def test_generate_structured_adr():
    request = load_mock_decisions()

    decision = request.decisions[0]

    detector = ADRSignificanceDetector()
    significance = detector.evaluate(decision)

    aggregator = ADREvidenceAggregator()
    evidence = aggregator.aggregate(
        decision,
        significance,
    )

    generator = ADRGenerator()

    adr = generator.generate(
        evidence=evidence,
        adr_number=1,
    )

    assert adr.adr_id == "BANKING-ADR-001-ADR-001"
    assert adr.project_id == decision.project_id
    assert adr.title == decision.title
    assert adr.status == ADRStatus.PROPOSED

    assert adr.context == decision.context
    assert adr.decision == decision.decision
    assert adr.rationale == decision.rationale

    assert adr.alternatives == decision.alternatives

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


def test_generate_unique_adr_ids():
    request = load_mock_decisions()

    detector = ADRSignificanceDetector()
    aggregator = ADREvidenceAggregator()
    generator = ADRGenerator()

    generated_ids = []

    for index, decision in enumerate(
        request.decisions,
        start=1,
    ):
        significance = detector.evaluate(decision)

        evidence = aggregator.aggregate(
            decision,
            significance,
        )

        adr = generator.generate(
            evidence=evidence,
            adr_number=index,
        )

        generated_ids.append(adr.adr_id)

    assert len(generated_ids) == 4
    assert len(set(generated_ids)) == 4

    assert generated_ids == [
        "BANKING-ADR-001-ADR-001",
        "BANKING-ADR-001-ADR-002",
        "BANKING-ADR-001-ADR-003",
        "BANKING-ADR-001-ADR-004",
    ]