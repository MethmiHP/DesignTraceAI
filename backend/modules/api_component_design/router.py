from fastapi import APIRouter

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


@router.post(
    "/design",
    response_model=APIComponentDesignResponse,
)
async def design_api_and_components(
    request: APIComponentDesignRequest,
):

    return await service.design(request)