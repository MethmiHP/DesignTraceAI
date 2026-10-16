import json

from modules.adr.adr_generator import ADRGenerator
from modules.adr.adr_validator import ADRValidator
from modules.adr.evidence_aggregator import ADREvidenceAggregator
from modules.adr.schemas import ADRGenerationRequest
from modules.adr.significance_detector import ADRSignificanceDetector


def load_mock_decisions():
    with open(
        "datasets/adr/mock_design_decisions.json",
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return ADRGenerationRequest(**data)


def build_test_adr():
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

    return decision, adr


def test_valid_generated_adr():
    decision, adr = build_test_adr()

    validator = ADRValidator()

    result = validator.validate(
        adr,
        decision,
    )

    assert result.valid is True
    assert result.errors == []

    assert result.completeness_score > 0.80


def test_modified_decision_is_rejected():
    decision, adr = build_test_adr()

    modified_adr = adr.model_copy(
        update={
            "decision": (
                "Use a completely different architecture."
            )
        }
    )

    validator = ADRValidator()

    result = validator.validate(
        modified_adr,
        decision,
    )

    assert result.valid is False

    assert any(
        "does not match" in error
        for error in result.errors
    )


def test_missing_traceability_generates_warning():
    decision, adr = build_test_adr()

    updated_traceability = (
        adr.traceability.model_copy(
            update={
                "requirement_ids": []
            }
        )
    )

    modified_adr = adr.model_copy(
        update={
            "traceability": updated_traceability
        }
    )

    validator = ADRValidator()

    result = validator.validate(
        modified_adr,
        decision,
    )

    assert result.valid is True

    assert len(result.warnings) > 0

    assert any(
        "requirement" in warning.lower()
        for warning in result.warnings
    )