from fastapi import FastAPI

from modules.quality_evaluation.router import (
    router as quality_evaluation_router,
)

app = FastAPI(
    title="DesignTrace AI",
    description="Multi-Agent AI Framework for SDLC Design Automation",
    version="0.1.0"
)

app.include_router(
    quality_evaluation_router
)


@app.get("/")
def root():
    return {
        "message": "DesignTrace AI Backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }