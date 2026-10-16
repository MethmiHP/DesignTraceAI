import json

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


def test_mock_design_decisions_are_significant():
    request = load_mock_decisions()

    detector = ADRSignificanceDetector()

    results = [
        detector.evaluate(decision)
        for decision in request.decisions
    ]

    assert len(results) == 4

    for result in results:
        assert result.significant is True
        assert result.score >= detector.SIGNIFICANCE_THRESHOLD
        assert len(result.reasons) > 0


def test_minor_decision_is_not_significant():
    request = load_mock_decisions()

    minor_decision = request.decisions[0].model_copy(
        update={
            "decision_id": "MINOR-DEC-001",
            "source_module": "manual",
            "title": "Rename helper variable",
            "decision": "Rename temp_value to calculated_value.",
            "context": "Improve local variable readability.",
            "rationale": "The new name is clearer.",
            "alternatives": [],
            "rejected_alternative_reasons": [],
            "decision_criteria": [],
            "benefits": [],
            "risks": [],
            "consequences": [],
            "trade_offs": [],
            "requirement_ids": [],
            "design_element_ids": [],
            "evidence": [],
            "confidence": None,
        }
    )

    detector = ADRSignificanceDetector()

    result = detector.evaluate(minor_decision)

    assert result.significant is False
    assert result.score < detector.SIGNIFICANCE_THRESHOLD