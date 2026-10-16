import json

from modules.adr.adr_generator import ADRGenerator
from modules.adr.evidence_aggregator import (
    ADREvidenceAggregator,
)
from modules.adr.repository import ADRRepository
from modules.adr.schemas import (
    ADRGenerationRequest,
    ADRStatus,
)
from modules.adr.significance_detector import (
    ADRSignificanceDetector,
)


def load_mock_decisions():
    with open(
        "datasets/adr/mock_design_decisions.json",
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return ADRGenerationRequest(
        **data
    )


def create_test_adr():
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

    generator = ADRGenerator()

    return generator.generate(
        evidence=evidence,
        adr_number=1,
    )


def test_adr_is_persisted_to_json(
    tmp_path,
):
    repository = ADRRepository(
        storage_dir=tmp_path
    )

    adr = create_test_adr()

    repository.save(
        adr
    )

    expected_file = (
        tmp_path
        / adr.project_id
        / f"{adr.adr_id}.json"
    )

    assert expected_file.exists()

    stored_data = json.loads(
        expected_file.read_text(
            encoding="utf-8"
        )
    )

    assert (
        stored_data["adr_id"]
        == adr.adr_id
    )

    assert (
        stored_data["decision"]
        == adr.decision
    )


def test_repository_restores_saved_adrs(
    tmp_path,
):
    first_repository = ADRRepository(
        storage_dir=tmp_path
    )

    adr = create_test_adr()

    first_repository.save(
        adr
    )

    second_repository = ADRRepository(
        storage_dir=tmp_path
    )

    restored = second_repository.get(
        adr.adr_id
    )

    assert (
        restored.adr_id
        == adr.adr_id
    )

    assert (
        restored.decision
        == adr.decision
    )

    assert (
        restored.traceability
        == adr.traceability
    )


def test_status_change_is_persisted(
    tmp_path,
):
    repository = ADRRepository(
        storage_dir=tmp_path
    )

    adr = create_test_adr()

    repository.save(
        adr
    )

    repository.change_status(
        adr.adr_id,
        ADRStatus.ACCEPTED,
    )

    restarted_repository = ADRRepository(
        storage_dir=tmp_path
    )

    restored = restarted_repository.get(
        adr.adr_id
    )

    assert (
        restored.status
        == ADRStatus.ACCEPTED
    )