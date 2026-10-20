import logging
from pathlib import Path
from dotenv import load_dotenv

# Show module activity in the terminal without enabling verbose SDK/network logs.
quality_logger = logging.getLogger('modules.quality_evaluation')
quality_logger.setLevel(logging.INFO)
if not any(getattr(handler, '_quality_console', False) for handler in quality_logger.handlers):
    console = logging.StreamHandler()
    console._quality_console = True
    console.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S'))
    quality_logger.addHandler(console)
quality_logger.propagate = False

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

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