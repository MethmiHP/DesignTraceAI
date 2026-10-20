from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool
import asyncio
from .jobs import DesignJobs

from .schemas import (
    APIComponentDesignRequest,
    APIComponentDesignResponse,
)

from .service import APIComponentDesignService


router = APIRouter(
    prefix="/api-component",
    tags=["API & Component Design"],
)


service = APIComponentDesignService()
jobs = DesignJobs(service.design)


@router.post("/jobs", status_code=202)
def start_design(request: APIComponentDesignRequest):
    try:
        return jobs.submit(request)
    except ValueError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@router.get("/jobs/{job_id}")
def get_design(job_id: str):
    record = jobs.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Job expired or backend restarted. Generate the design again.")
    return record


@router.post(
    "/design",
    response_model=APIComponentDesignResponse,
)
async def design_api_and_components(
    request: APIComponentDesignRequest,
):

    return await run_in_threadpool(lambda: asyncio.run(service.design(request)))
