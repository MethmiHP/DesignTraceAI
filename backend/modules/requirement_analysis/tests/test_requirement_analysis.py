# Tests the Requirement Analysis Service by sending a sample project description
# and verifying that requirements are generated, IDs are assigned correctly,
# and the final output passes validation.

import pytest
from shared.llm.mock_client import MockLLMClient

from modules.requirement_analysis.schemas import (
    RequirementAnalysisRequest,
    ProjectContext
)

from modules.requirement_analysis.service import (
    RequirementAnalysisService
)


@pytest.mark.asyncio
async def test_requirement_analysis():

    service = RequirementAnalysisService(
    llm=MockLLMClient()
    )

    request = RequirementAnalysisRequest(

        project_id="TEST-001",

        raw_description=(
            "Patients should be able to register. "
            "Patient information must be secure."
        ),

        project_context=ProjectContext(
            domain="Healthcare",
            system_type="Web Application",
            primary_users=[
                "Patients"
            ]
        )
    )

    result = await service.analyze(
        request
    )

    assert result.project_id == "TEST-001"

    assert len(
        result.requirements
    ) > 0

    assert (
        result.requirements[0]
        .requirement_id
        == "REQ-001"
    )

    assert result.validation.valid is True

@pytest.mark.asyncio
async def test_simple_fr():

    service = RequirementAnalysisService(
    llm=MockLLMClient()
    )

    request = RequirementAnalysisRequest(
        project_id="TEST-FR",
        raw_description="Users shall log in.",
        project_context=ProjectContext()
    )

    result = await service.analyze(request)

    assert result.requirements[0].requirement_type == "FR"

@pytest.mark.asyncio
async def test_security_nfr():

    service = RequirementAnalysisService(
    llm=MockLLMClient()
    )

    request = RequirementAnalysisRequest(
        project_id="TEST-SEC",
        raw_description="User data must be secure.",
        project_context=ProjectContext()
    )

    result = await service.analyze(request)

    req = result.requirements[0]

    assert req.requirement_type == "NFR"
    assert req.quality_attribute == "Security"

@pytest.mark.asyncio
async def test_performance_nfr():

    service = RequirementAnalysisService(
    llm=MockLLMClient()
    )

    request = RequirementAnalysisRequest(
        project_id="TEST-PERF",
        raw_description="The system shall respond within 2 seconds.",
        project_context=ProjectContext()
    )

    result = await service.analyze(request)

    req = result.requirements[0]

    assert req.requirement_type == "NFR"
    assert req.quality_attribute == "Performance"
    assert req.asr is True

@pytest.mark.asyncio
async def test_ambiguous_requirement():

    service = RequirementAnalysisService(
    llm=MockLLMClient()
    )

    request = RequirementAnalysisRequest(
        project_id="TEST-AMB",
        raw_description="The system should be fast.",
        project_context=ProjectContext()
    )

    result = await service.analyze(request)

    req = result.requirements[0]

    assert req.requirement_type == "NFR"
    assert req.quality_issues.ambiguous is True

@pytest.mark.asyncio
async def test_asr_requirement():

    service = RequirementAnalysisService(
    llm=MockLLMClient()
    )

    request = RequirementAnalysisRequest(
        project_id="TEST-ASR",
        raw_description="The system shall support 10,000 concurrent users.",
        project_context=ProjectContext()
    )

    result = await service.analyze(request)

    req = result.requirements[0]

    assert req.asr is True