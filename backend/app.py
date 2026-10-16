from fastapi import FastAPI
from modules.adr.router import router as adr_router

app = FastAPI(
    title="DesignTrace AI",
    description="Multi-Agent AI Framework for SDLC Design Automation",
    version="0.1.0"
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

app.include_router(adr_router)