from pathlib import Path
from fastapi import HTTPException, Path as PathParameter
from fastapi.responses import PlainTextResponse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from fastapi.middleware.cors import CORSMiddleware

from shared.models.project import (
    ProjectInput,
    ArchitectureContext,
)
from modules.database_design.design_pipeline import (
    run_complete_database_design,
)


app = FastAPI(
    title="DesignTrace AI",
    description=(
        "Coordinator-Orchestrated Framework for "
        "Requirement-to-Design Automation"
    ),
    version="0.2.0",
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



# SQL artifacts are stored inside the backend outputs directory.
# Locate the backend directory using this file's parent directories.

def find_backend_directory() -> Path:
    current = Path(__file__).resolve().parent

    for directory in (current, *current.parents):
        if directory.name.lower() == "backend":
            return directory

    raise RuntimeError("Could not locate the backend directory")


BACKEND_DIR = find_backend_directory()

ARTIFACTS_DIR = (
    BACKEND_DIR
    / "outputs"
    / "database_designs"
    / "artifacts"
)


@app.get(
    "/api/database-design/artifacts/{project_id}/sql",
    response_class=PlainTextResponse,
    tags=["Database Design"],
)
def get_database_sql(
    project_id: str = PathParameter(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
):
    sql_file = ARTIFACTS_DIR / f"{project_id}_database_design.sql"

    if not sql_file.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"SQL artifact not found for project: {project_id}",
        )

    try:
        sql_content = sql_file.read_text(encoding="utf-8")
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Could not read the SQL artifact",
        )

    return PlainTextResponse(
        content=sql_content,
        media_type="text/plain; charset=utf-8",
    )
class DatabaseDesignRequest(BaseModel):
    project: ProjectInput

    # Architecture context is supplied separately by the frontend.
    architecture_context: ArchitectureContext | None = None

    generation_method: Literal[
        "deterministic",
        "gemini",
    ] = "deterministic"

    # Optional manually supplied NLP concepts.
    extracted_concepts: dict | None = None


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

@app.post("/api/database-design/generate")
def generate_database_design(request: DatabaseDesignRequest):
    """
    Generate a database design draft.

    The Database Design Module performs generation and
    validation. The Coordinator Agent manages approval.
    """

    try:
        project = request.project

        # The frontend supplies architecture_context
        # as a top-level field, separate from project.
        #
        # Attach it to a copy of the ProjectInput object
        # before calling the database design pipeline.
        if request.architecture_context is not None:
            project = project.model_copy(
                update={
                    "architecture_context": (
                        request.architecture_context
                    )
                }
            )

        print("\n========== API INPUT DEBUG ==========")
        print("Project ID:", project.project_id)

        if project.architecture_context is not None:
            print(
                "Architecture context received:",
                project.architecture_context.model_dump(),
            )
        else:
            print("Architecture context: None")

        print("=====================================\n")

        result = run_complete_database_design(
            project=project,
            generation_method=request.generation_method,
            extracted_concepts=request.extracted_concepts,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc