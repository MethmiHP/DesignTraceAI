from fastapi import FastAPI

from coordinator.api import router as coordinator_router


app = FastAPI(
    title="DesignTrace AI",
    description=(
        "Coordinator-Orchestrated Framework for "
        "Software Design Automation"
    ),
    version="0.1.0",
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


app.include_router(coordinator_router)