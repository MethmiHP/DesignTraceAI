import json

import pytest

from modules.adr.adr_generator import ADRGenerator
from modules.adr.evidence_aggregator import ADREvidenceAggregator
from modules.adr.repository import ADRRepository
from modules.adr.schemas import (
    ADRGenerationRequest,
    ADRStatus,
)
from modules.adr.significance_detector import ADRSignificanceDetector


def load_mock_decisions():
    with open(
        "datasets/adr/mock_design_decisions.json",
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return ADRGenerationRequest(**data)


def build_adr(
    decision_index: int,
    adr_number: int,
):
    request = load_mock_decisions()

    decision = request.decisions[
        decision_index
    ]

    detector = ADRSignificanceDetector()

    significance = detector.evaluate(
        decision
    )

    aggregator = ADREvidenceAggregator()

    evidence = aggregator.aggregate(
        decision,
        significance,
    )

    generator = ADRGenerator()

    return generator.generate(
        evidence=evidence,
        adr_number=adr_number,
    )


def test_save_and_retrieve_adr():
    repository = ADRRepository()

    adr = build_adr(
        decision_index=0,
        adr_number=1,
    )

    repository.save(adr)

    stored = repository.get(
        adr.adr_id
    )

    assert stored.adr_id == adr.adr_id
    assert stored.status == ADRStatus.PROPOSED


def test_accept_proposed_adr():
    repository = ADRRepository()

    adr = build_adr(
        decision_index=0,
        adr_number=1,
    )

    repository.save(adr)

    accepted = repository.change_status(
        adr.adr_id,
        ADRStatus.ACCEPTED,
    )

    assert (
        accepted.status
        == ADRStatus.ACCEPTED
    )


def test_invalid_lifecycle_transition():
    repository = ADRRepository()

    adr = build_adr(
        decision_index=0,
        adr_number=1,
    )

    repository.save(adr)

    with pytest.raises(ValueError):
        repository.change_status(
            adr.adr_id,
            ADRStatus.SUPERSEDED,
        )


def test_supersede_accepted_adr():
    repository = ADRRepository()

    old_adr = build_adr(
        decision_index=0,
        adr_number=1,
    )

    new_adr = build_adr(
        decision_index=1,
        adr_number=2,
    )

    repository.save(old_adr)
    repository.save(new_adr)

    repository.change_status(
        old_adr.adr_id,
        ADRStatus.ACCEPTED,
    )

    old_updated, new_updated = (
        repository.supersede(
            old_adr.adr_id,
            new_adr.adr_id,
        )
    )

    assert (
        old_updated.status
        == ADRStatus.SUPERSEDED
    )

    assert (
        old_updated.superseded_by
        == new_adr.adr_id
    )

    assert (
        new_updated.supersedes
        == old_adr.adr_id
    )


def test_list_adrs_by_project():
    repository = ADRRepository()

    adr1 = build_adr(
        decision_index=0,
        adr_number=1,
    )

    adr2 = build_adr(
        decision_index=1,
        adr_number=2,
    )

    repository.save(adr1)
    repository.save(adr2)

    results = repository.list_by_project(
        adr1.project_id
    )

    assert len(results) == 2