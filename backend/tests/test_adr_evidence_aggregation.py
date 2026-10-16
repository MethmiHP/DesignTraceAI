import json

import pytest

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


def test_evidence_aggregation_for_significant_decision():
    request = load_mock_decisions()

    decision = request.decisions[0]

    detector = ADRSignificanceDetector()
    significance = detector.evaluate(decision)

    aggregator = ADREvidenceAggregator()

    evidence = aggregator.aggregate(
        decision,
        significance,
    )

    assert evidence.decision_id == decision.decision_id
    assert evidence.project_id == decision.project_id
    assert evidence.selected_decision == decision.decision

    assert len(evidence.requirement_ids) > 0
    assert len(evidence.design_element_ids) > 0
    assert len(evidence.trade_offs) > 0

    assert evidence.significance_score >= (
        detector.SIGNIFICANCE_THRESHOLD
    )


def test_non_significant_decision_is_rejected():
    request = load_mock_decisions()

    minor_decision = request.decisions[0].model_copy(
        update={
            "decision_id": "MINOR-DEC-002",
            "source_module": "manual",
            "title": "Rename local variable",
            "decision": "Rename temp to result.",
            "context": "Improve readability.",
            "rationale": "The new variable name is clearer.",
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
    significance = detector.evaluate(minor_decision)

    aggregator = ADREvidenceAggregator()

    with pytest.raises(ValueError):
        aggregator.aggregate(
            minor_decision,
            significance,
        )