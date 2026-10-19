import logging

from .output_store import save_report

from fastapi import (
    APIRouter,
    HTTPException,
)

from .schemas import (
    QualityEvaluationRequest,
    QualityEvaluationResponse,
)
from .service import (
    QualityEvaluationService,
)


router = APIRouter(
    prefix="/quality-evaluation",
    tags=[
        "Quality Evaluation"
    ],
)


service = QualityEvaluationService()


@router.post(
    "/evaluate",
    response_model=(
        QualityEvaluationResponse
    ),
)
def evaluate_quality(
    request: QualityEvaluationRequest,
):
    response = service.evaluate(request)
    try:
        save_report(response)
    except OSError as error:
        logging.getLogger(__name__).exception('Could not save quality evaluation report')
        raise HTTPException(
            status_code=500,
            detail='Evaluation completed, but the report could not be saved. Please retry.',
        ) from error
    return response