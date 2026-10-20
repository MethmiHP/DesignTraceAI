from dotenv import load_dotenv
import logging

load_dotenv()

api_logger = logging.getLogger("modules.api_component_design")
api_logger.setLevel(logging.INFO)
if not any(getattr(handler, "_api_console", False) for handler in api_logger.handlers):
    handler = logging.StreamHandler()
    handler._api_console = True
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S",
    ))
    api_logger.addHandler(handler)
api_logger.propagate = False


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
