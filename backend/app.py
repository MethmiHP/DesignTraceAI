from fastapi import FastAPI

from modules.api_component_design.router import (
    router as api_component_router,
)


app = FastAPI(
    title="DesignTrace AI",
    version="0.1.0",
)


app.include_router(api_component_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "application": "DesignTrace AI",
    }