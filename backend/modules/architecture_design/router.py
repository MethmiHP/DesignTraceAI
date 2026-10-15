"""
FastAPI Router for Architecture Decision Agent – Milestone 7.3.

M1-M4 endpoints accept ASRBatch.

M5 design and full analysis accept ArchitectureProjectInput
because complete high-level design generation requires all
architecture-relevant requirements together with identified ASRs.
"""

from __future__ import annotations

import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from .dependencies import (
    get_architecture_service,
)
from .service import (
    ArchitectureDesignService,
)
from .llm.provider import (
    ExternalModelProviderError,
)

from .schemas import (
    ASRBatch,
    ArchitectureProjectInput,
    ClassificationOutput,
    ScoringOutput,
    RetrievalOutput,
    RecommendationOutput,
    ArchitectureDesignOutput,
    ArchitectureAnalysisOutput,
)


logger = logging.getLogger(
    __name__
)


router = APIRouter(
    prefix="/architecture",
    tags=[
        "Architecture Decision"
    ],
)


def _validate_asr_batch(
    batch: ASRBatch,
) -> None:

    if not batch.asrs:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail={
                "error":
                    "EMPTY_ASR_BATCH",

                "message":
                    (
                        "At least one "
                        "Architecturally Significant "
                        "Requirement is required."
                    ),
            },
        )


def _validate_project_input(
    project: ArchitectureProjectInput,
) -> None:

    if not project.requirements:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail={
                "error":
                    "EMPTY_REQUIREMENT_SET",

                "message":
                    (
                        "At least one "
                        "architecture-relevant "
                        "requirement is required."
                    ),
            },
        )

    if not project.asrs:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail={
                "error":
                    "EMPTY_ASR_BATCH",

                "message":
                    (
                        "At least one "
                        "Architecturally Significant "
                        "Requirement is required."
                    ),
            },
        )


def _handle_pipeline_exception(
    exc: Exception,
    operation_name: str,
) -> None:
    """
    Convert internal errors to safe HTTP responses.

    No API keys, prompts, stack traces, or provider
    response bodies are returned to the frontend.
    """

    if isinstance(
        exc,
        HTTPException,
    ):
        raise exc

    exc_type_name = (
        type(exc).__name__
    )

    logger.error(
        "Error during %s: %s",
        operation_name,
        exc_type_name,
    )

    # -----------------------------------------------------
    # Gemini/external model temporary failure
    # -----------------------------------------------------

    if isinstance(
        exc,
        ExternalModelProviderError,
    ):
        logger.error(
            "External model provider unavailable. "
            "operation=%s provider_status=%s",
            operation_name,
            exc.status_code,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail={
                "error":
                    "EXTERNAL_MODEL_PROVIDER_ERROR",

                "message":
                    (
                        "The AI model provider is "
                        "temporarily unavailable. "
                        "Please retry the analysis."
                    ),

                "provider_status":
                    exc.status_code,
            },
        )

    # -----------------------------------------------------
    # Invalid application data
    # -----------------------------------------------------

    if isinstance(
        exc,
        ValueError,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail={
                "error":
                    "INVALID_REQUEST_DATA",

                "message":
                    str(exc),
            },
        )

    upper_type = (
        exc_type_name.upper()
    )

    # -----------------------------------------------------
    # Authentication/configuration problems
    # -----------------------------------------------------

    if (
        "API_KEY" in upper_type
        or "AUTHENTICATION"
        in upper_type
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "error":
                    "EXTERNAL_SERVICE_UNAVAILABLE",

                "message":
                    (
                        "External model service "
                        "authentication or access "
                        "is currently unavailable."
                    ),
            },
        )

    # -----------------------------------------------------
    # Fallback recognition of external SDK errors
    # -----------------------------------------------------

    if any(
        token in upper_type
        for token in (
            "GENAI",
            "MODEL",
            "CONNECTION",
            "SERVER",
            "CLIENTERROR",
            "SERVICEUNAVAILABLE",
            "RESOURCEEXHAUSTED",
        )
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail={
                "error":
                    "EXTERNAL_MODEL_PROVIDER_ERROR",

                "message":
                    (
                        "External AI provider failed "
                        f"during {operation_name}. "
                        "Please retry."
                    ),
            },
        )

    # -----------------------------------------------------
    # Unexpected internal problem
    # -----------------------------------------------------

    raise HTTPException(
        status_code=(
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ),
        detail={
            "error":
                "INTERNAL_PIPELINE_ERROR",

            "message":
                (
                    "An unexpected error occurred "
                    f"while executing {operation_name}."
                ),
        },
    )


@router.post(
    "/classify",
    response_model=ClassificationOutput,
    summary=(
        "M1: Quality Attribute Classification"
    ),
)
def classify_requirements(
    batch: ASRBatch,
    service: ArchitectureDesignService = Depends(
        get_architecture_service
    ),
) -> ClassificationOutput:

    _validate_asr_batch(
        batch
    )

    try:
        return service.run(
            batch
        )

    except Exception as exc:
        _handle_pipeline_exception(
            exc,
            "quality attribute classification",
        )


@router.post(
    "/evaluate",
    response_model=ScoringOutput,
    summary=(
        "M2: Architecture Scoring and Ranking"
    ),
)
def evaluate_architectures(
    batch: ASRBatch,
    service: ArchitectureDesignService = Depends(
        get_architecture_service
    ),
) -> ScoringOutput:

    _validate_asr_batch(
        batch
    )

    try:
        return service.evaluate(
            batch
        )

    except Exception as exc:
        _handle_pipeline_exception(
            exc,
            "architecture evaluation and scoring",
        )


@router.post(
    "/retrieve",
    response_model=RetrievalOutput,
    summary=(
        "M3: Evidence Retrieval"
    ),
)
def retrieve_evidence(
    batch: ASRBatch,

    top_k: int = Query(
        5,
        ge=1,
        le=20,
    ),

    service: ArchitectureDesignService = Depends(
        get_architecture_service
    ),
) -> RetrievalOutput:

    _validate_asr_batch(
        batch
    )

    try:
        return service.retrieve_evidence(
            batch,
            top_k=top_k,
        )

    except Exception as exc:
        _handle_pipeline_exception(
            exc,
            "evidence retrieval",
        )


@router.post(
    "/recommend",
    response_model=RecommendationOutput,
    summary=(
        "M4: Explainable Architecture Recommendation"
    ),
)
def recommend_architecture(
    batch: ASRBatch,

    top_k: int = Query(
        5,
        ge=1,
        le=20,
    ),

    service: ArchitectureDesignService = Depends(
        get_architecture_service
    ),
) -> RecommendationOutput:

    _validate_asr_batch(
        batch
    )

    try:
        return service.recommend(
            batch,
            top_k=top_k,
        )

    except Exception as exc:
        _handle_pipeline_exception(
            exc,
            "architecture recommendation",
        )


@router.post(
    "/design",
    response_model=ArchitectureDesignOutput,
    summary=(
        "M5: Full-Requirement High-Level Architecture Design"
    ),
)
def generate_architecture_design(
    project: ArchitectureProjectInput,

    top_k: int = Query(
        5,
        ge=1,
        le=20,
    ),

    service: ArchitectureDesignService = Depends(
        get_architecture_service
    ),
) -> ArchitectureDesignOutput:

    _validate_project_input(
        project
    )

    try:
        return service.generate_design(
            project,
            top_k=top_k,
        )

    except Exception as exc:
        _handle_pipeline_exception(
            exc,
            "architecture design generation",
        )


@router.post(
    "/analyze",
    response_model=ArchitectureAnalysisOutput,
    summary=(
        "Full Architecture Decision Pipeline"
    ),
)
def analyze_architecture(
    project: ArchitectureProjectInput,

    top_k: int = Query(
        5,
        ge=1,
        le=20,
    ),

    service: ArchitectureDesignService = Depends(
        get_architecture_service
    ),
) -> ArchitectureAnalysisOutput:

    _validate_project_input(
        project
    )

    try:
        return service.analyze(
            project,
            top_k=top_k,
        )

    except Exception as exc:
        _handle_pipeline_exception(
            exc,
            "full architecture analysis",
        )