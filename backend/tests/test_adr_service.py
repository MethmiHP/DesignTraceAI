import json

import pytest

from modules.adr.schemas import ADRGenerationRequest
from modules.adr.service import ADRService


def load_mock_decisions():
    with open(
        "datasets/adr/mock_design_decisions.json",
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return ADRGenerationRequest(**data)


@pytest.mark.anyio
async def test_generate_adrs_end_to_end():
    request = load_mock_decisions()

    service = ADRService()

    response = await service.generate_adrs(
        request
    )

    assert (
        response.project_id
        == request.project_id
    )

    assert (
        response.generated_adr_count
        == 4
    )

    assert (
        response.skipped_decision_count
        == 0
    )

    assert len(response.results) == 4

    for result in response.results:
        assert (
            result.significance.significant
            is True
        )

        assert result.adr is not None

        stored = service.repository.get(
            result.adr.adr_id
        )

        assert (
            stored.adr_id
            == result.adr.adr_id
        )


@pytest.mark.anyio
async def test_service_skips_minor_decision():
    request = load_mock_decisions()

    minor_decision = (
        request.decisions[0].model_copy(
            update={
                "decision_id": "MINOR-DEC-003",
                "source_module": "manual",
                "title": "Rename helper variable",
                "decision": "Rename temp to result.",
                "context": "Improve local readability.",
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
    )

    updated_request = request.model_copy(
        update={
            "decisions": [
                minor_decision
            ]
        }
    )

    service = ADRService()

    response = await service.generate_adrs(
        updated_request
    )

    assert (
        response.generated_adr_count
        == 0
    )

    assert (
        response.skipped_decision_count
        == 1
    )

    assert len(response.results) == 1

    result = response.results[0]

    assert (
        result.significance.significant
        is False
    )

    assert result.adr is None


@pytest.mark.anyio
async def test_duplicate_source_decision_is_not_regenerated():
    request = load_mock_decisions()

    service = ADRService()

    first_response = (
        await service.generate_adrs(
            request
        )
    )

    assert (
        first_response.generated_adr_count
        == 4
    )

    second_response = (
        await service.generate_adrs(
            request
        )
    )

    assert (
        second_response.generated_adr_count
        == 0
    )

    assert (
        second_response.skipped_decision_count
        == 4
    )

    assert len(
        service.repository.list_by_project(
            request.project_id
        )
    ) == 4