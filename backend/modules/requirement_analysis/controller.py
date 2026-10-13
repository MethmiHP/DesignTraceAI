# Defines the FastAPI endpoint for requirement analysis,
# receives the request, calls the RequirementAnalysisService,
# and returns the analyzed requirement response to the client.

from fastapi import APIRouter, HTTPException

from modules.requirement_analysis.schemas import (
    RequirementAnalysisRequest,
    RequirementAnalysisResponse
)

from modules.requirement_analysis.service import (
    RequirementAnalysisService
)


router = APIRouter(
    prefix="/requirements",
    tags=["Requirement Analysis"]
)


service = RequirementAnalysisService()


@router.post(
    "/analyze",
    response_model=RequirementAnalysisResponse
)
async def analyze_requirements(
    request: RequirementAnalysisRequest
):

    try:

        result = await service.analyze(
            request
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Requirement analysis failed: {str(exc)}"
        )