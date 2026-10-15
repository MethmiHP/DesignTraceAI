# from fastapi import FastAPI

# app = FastAPI(
#     title="DesignTrace AI",
#     description="Multi-Agent AI Framework for SDLC Design Automation",
#     version="0.1.0"
# )


# @app.get("/")
# def root():
#     return {
#         "message": "DesignTrace AI Backend is running"
#     }


# @app.get("/health")
# def health_check():
#     return {
#         "status": "healthy"
#     }


# # Register Architecture Decision Agent router
# from modules.architecture_design.router import router as architecture_router

# app.include_router(architecture_router, prefix="/api")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="DesignTrace AI",
    description="Multi-Agent AI Framework for SDLC Design Automation",
    version="0.1.0",
)


# ---------------------------------------------------------
# CORS configuration
# Allows the React/Vite frontend to call the FastAPI backend
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Register Architecture Decision Agent router
# ---------------------------------------------------------

from modules.architecture_design.router import (
    router as architecture_router,
)

app.include_router(
    architecture_router,
    prefix="/api",
)