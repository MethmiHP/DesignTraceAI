# Initializes the DesignTrace AI FastAPI backend,
# configures CORS, registers the Requirement Analysis routes,
# and provides root and health-check endpoints.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from modules.requirement_analysis.controller import (
    router as requirement_analysis_router
)


app = FastAPI(
    title="DesignTrace AI",
    description=(
        "Coordinator-Orchestrated Framework "
        "for Requirement-to-Design Automation"
    ),
    version="0.1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    requirement_analysis_router
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