# Defines the FastAPI endpoint for the Traceability Module.
# The endpoint accepts traceability input, runs the complete
# requirement-to-design analysis pipeline, and returns the structured result.

from fastapi import APIRouter, HTTPException

from modules.traceability.schemas import (
    TraceabilityRequest,
    TraceabilityResponse,
)

from modules.traceability.traceability_service import (
    get_traceability_service,
)


router = APIRouter(
    prefix="/traceability",
    tags=["Traceability"],
)


@router.post(
    "/analyze",
    response_model=TraceabilityResponse,
)
def analyze_traceability(
    request: TraceabilityRequest,
):
    """
    Runs the complete requirement-to-design
    traceability analysis pipeline.
    """

    try:
        service = (
            get_traceability_service()
        )

        response = (
            service.analyze(
                request
            )
        )

        return response

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Traceability analysis failed: "
                f"{str(error)}"
            ),
        ) from error