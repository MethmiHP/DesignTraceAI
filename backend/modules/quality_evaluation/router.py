import logging

from .output_store import save_report
from .jobs import EvaluationJobs, QueueFullError

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

# Keep /evaluate available for existing integrations. The frontend uses jobs.

jobs = EvaluationJobs()


@router.post('/jobs', status_code=202)
def start_evaluation(request: QualityEvaluationRequest):
    try:
        return jobs.submit(request)
    except QueueFullError as error:
        raise HTTPException(status_code=429, detail=str(error)) from error


@router.get('/jobs/{job_id}')
def evaluation_status(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail='Evaluation job expired or the backend restarted. Submit the evaluation again.')
    return job
