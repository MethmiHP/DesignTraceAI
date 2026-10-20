"""
FastAPI routes for the Architecture Decision Records module.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from modules.adr.repository import ADRRepository
from modules.adr.report_generator import ADRReportGenerator
from modules.adr.schemas import (
    ADRGenerationRequest,
    ADRGenerationResponse,
    ADRRecord,
    ADRStatus,
)
from modules.adr.service import ADRService
from shared.llm.factory import get_llm_provider


router = APIRouter(
    prefix="/api/adr",
    tags=["Architecture Decision Records"],
)


# backend directory
BACKEND_DIR = Path(
    __file__
).resolve().parents[2]


# Persistent ADR repository:
#
# backend/
# └── outputs/
#     └── adr/
#         └── <project-id>/
#             └── <adr-id>.json
ADR_STORAGE_DIR = (
    BACKEND_DIR
    / "outputs"
    / "adr"
)


repository = ADRRepository(
    storage_dir=ADR_STORAGE_DIR
)


service = ADRService(
    repository=repository,
    llm_provider=get_llm_provider(),
    use_llm=True,
)


report_generator = ADRReportGenerator()


@router.post(
    "/generate",
    response_model=ADRGenerationResponse,
)
async def generate_adrs(
    request: ADRGenerationRequest,
):
    """
    Generate ADRs from design decisions received from
    other DesignTrace AI modules.

    Significant decisions are converted into validated ADRs.
    Generated ADRs are persisted in the ADR repository.
    """

    try:
        return await service.generate_adrs(
            request
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get(
    "/project/{project_id}",
    response_model=list[ADRRecord],
)
async def get_project_adrs(
    project_id: str,
):
    """
    Return all ADRs generated for a project.
    """

    return repository.list_by_project(
        project_id
    )


@router.get(
    "/project/{project_id}/report",
)
async def export_project_adr_report(
    project_id: str,
):
    """
    Generate and download a PDF report containing
    all ADRs stored for a project.
    """

    adrs = repository.list_by_project(
        project_id
    )

    if not adrs:
        raise HTTPException(
            status_code=404,
            detail=(
                "No ADRs found for project "
                f"'{project_id}'."
            ),
        )

    try:
        pdf_buffer = (
            report_generator.generate_project_report(
                project_id=project_id,
                adrs=adrs,
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to generate ADR report."
            ),
        ) from exc


    filename = (
        f"{project_id}_ADR_Report.pdf"
    )


    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )


@router.get(
    "/{adr_id}",
    response_model=ADRRecord,
)
async def get_adr(
    adr_id: str,
):
    """
    Return one ADR by identifier.
    """

    try:
        return repository.get(
            adr_id
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{adr_id}/status/{status}",
    response_model=ADRRecord,
)
async def update_adr_status(
    adr_id: str,
    status: ADRStatus,
):
    """
    Update the lifecycle status of an ADR.

    The updated ADR is also persisted to disk.
    """

    try:
        return repository.change_status(
            adr_id,
            status,
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post(
    "/{old_adr_id}/supersede/{new_adr_id}",
)
async def supersede_adr(
    old_adr_id: str,
    new_adr_id: str,
):
    """
    Supersede one accepted ADR with another ADR.

    Both ADR documents are updated in persistent storage.
    """

    try:
        old_adr, new_adr = (
            repository.supersede(
                old_adr_id,
                new_adr_id,
            )
        )

        return {
            "superseded_adr": old_adr,
            "replacement_adr": new_adr,
        }

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc