from fastapi import (
    APIRouter,
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
    return service.evaluate(
        request
    )