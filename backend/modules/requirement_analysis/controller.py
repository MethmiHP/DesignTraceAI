# Defines the FastAPI endpoint for requirement analysis,
# receives the request, calls the RequirementAnalysisService,
# and returns the analyzed requirement response to the client.

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Form,
)

from modules.requirement_analysis.schemas import (
    RequirementAnalysisRequest,
    RequirementAnalysisResponse,
    ProjectContext,
)

from modules.requirement_analysis.service import (
    RequirementAnalysisService,
)

from modules.requirement_analysis.document_parser import (
    extract_document_text,
    DocumentParsingError,
)


router = APIRouter(
    prefix="/requirements",
    tags=["Requirement Analysis"],
)


service = RequirementAnalysisService()


# MANUAL / RAW TEXT ANALYSIS

@router.post(
    "/analyze",
    response_model=RequirementAnalysisResponse,
)
async def analyze_requirements(
    request: RequirementAnalysisRequest,
):

    try:

        result = await service.analyze(
            request
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Requirement analysis failed: "
                f"{str(exc)}"
            ),
        ) from exc


# DOCUMENT ANALYSIS

@router.post(
    "/analyze-document",
    response_model=RequirementAnalysisResponse,
)
async def analyze_requirement_document(

    project_id: str = Form(...),

    file: UploadFile = File(...),

    domain: str | None = Form(None),

    system_type: str | None = Form(None),

):

    try:

        # VALIDATE PROJECT ID

        project_id = (
            project_id
            .strip()
        )


        if not project_id:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Project ID is required."
                ),
            )


        # READ UPLOADED FILE

        file_bytes = await file.read()


        # EXTRACT TEXT

        extracted_text = (
            extract_document_text(

                filename=
                    file.filename
                    or "",

                file_bytes=
                    file_bytes,
            )
        )


        # BUILD NORMAL REQUIREMENT ANALYSIS REQUEST

        request = (
            RequirementAnalysisRequest(

                project_id=
                    project_id,

                raw_description=
                    extracted_text,

                project_context=
                    ProjectContext(

                        domain=(
                            domain.strip()
                            if domain
                            else None
                        ),

                        system_type=(
                            system_type.strip()
                            if system_type
                            else None
                        ),
                    ),
            )
        )


        # USE THE SAME EXISTING ANALYSIS SERVICE

        result = await service.analyze(
            request
        )


        return result


    except DocumentParsingError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        ) from exc


    except HTTPException:

        raise


    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Document requirement analysis failed: "
                f"{str(exc)}"
            ),
        ) from exc