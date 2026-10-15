from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from modules.traceability.router import (
    router as traceability_router,
)


app = FastAPI(
    title="DesignTrace AI",
    description="Multi-Agent AI Framework for SDLC Design Automation",
    version="0.1.0",
)


# CORS

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)



# TRACEABILITY ROUTER

app.include_router(
    traceability_router
)


# BASIC ENDPOINTS

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