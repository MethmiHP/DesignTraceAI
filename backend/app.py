from fastapi import FastAPI
from modules.adr.router import router as adr_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="DesignTrace AI",
    description="Multi-Agent AI Framework for SDLC Design Automation",
    version="0.1.0"
)

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

app.include_router(adr_router)