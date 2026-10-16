import json
from typing import Any

import pytest

from modules.adr.schemas import (
    ADRGenerationMethod,
    ADRGenerationRequest,
)
from modules.adr.service import ADRService
from shared.llm.base import LLMProvider


class FailingLLMProvider(LLMProvider):
    """
    Simulates an unavailable or failing external LLM provider.
    """

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        raise RuntimeError(
            "Simulated LLM failure"
        )

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        raise RuntimeError(
            "Simulated LLM failure"
        )


def load_mock_decisions():
    """
    Load mock decisions representing outputs from other
    DesignTrace AI modules.
    """

    with open(
        "datasets/adr/mock_design_decisions.json",
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return ADRGenerationRequest(**data)


@pytest.mark.anyio
async def test_llm_failure_uses_deterministic_fallback():
    """
    Verify that an external model failure does not stop ADR generation.
    """

    request = load_mock_decisions()

    service = ADRService(
        llm_provider=FailingLLMProvider(),
        use_llm=True,
    )

    response = await service.generate_adrs(
        request
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
        assert result.adr is not None

        assert (
            result.significance.significant
            is True
        )

        assert (
            result.adr.generation_method
            == ADRGenerationMethod.DETERMINISTIC_FALLBACK
        )

        # Original upstream decision must still be preserved.
        assert (
            result.adr.decision
            == result.decision.decision
        )

        # Traceability must also remain available.
        assert len(
            result.adr.traceability.source_decision_ids
        ) > 0