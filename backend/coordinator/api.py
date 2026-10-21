"""
DesignTrace AI - Coordinator API

Neon-backed workflow tracking and LangGraph checkpoints.
Mock Modules remain enabled for PP1.
"""

from threading import Lock
from uuid import uuid4, UUID

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field
from langgraph.types import Command
from sqlalchemy import select

from coordinator.module_execution_store import (
    save_module_executions,
)

from coordinator.langgraph_workflow import (
    MODULE_ORDER,
    OUTPUT_DIR,
)
from coordinator.state_manager import create_initial_project_state
from shared.models.project import ProjectInput, Requirement
from mocks.mock_modules import REQUIREMENTS

from database.connection import SessionLocal
from database.models import Project, WorkflowRun, ReviewDecision, ArtifactVersion, ModuleExecution, WorkflowEvent


router = APIRouter(
    prefix="/api/coordinator",
    tags=["Coordinator Agent"],
)

workflow_lock = Lock()


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: str = Field(default="", max_length=5000)


def serialize_project(project):
    return {
        "project_id": str(project.id),
        "name": project.name,
        "description": project.description or "",
        "status": project.status,
        "created_at": (
            project.created_at.isoformat()
            if project.created_at else None
        ),
        "mock_outputs": True,
    }


@router.post("/projects", status_code=201)
def create_project(payload: CreateProjectRequest):
    """
    Save actual project metadata in Neon PostgreSQL.
    Module outputs remain predefined PP1 mocks.
    """
    with SessionLocal.begin() as session:
        project = Project(
            name=payload.name.strip(),
            description=payload.description.strip(),
            input_data={
                "source": "user_created",
                "mock_outputs": True,
            },
            status="created",
        )

        if len(project.name) < 2:
            raise HTTPException(
                status_code=422,
                detail="Project name must contain at least two characters.",
            )

        session.add(project)
        session.flush()
        session.refresh(project)

        return serialize_project(project)


@router.get("/projects")
def list_projects():
    with SessionLocal() as session:
        projects = session.scalars(
            select(Project).order_by(Project.created_at.desc())
        ).all()

        return {
            "projects": [
                serialize_project(project)
                for project in projects
            ]
        }


class ReviewRequest(BaseModel):
    decision: str = Field(
        ...,
        description="approve or reject",
    )
    feedback: str = ""


def create_demo_project():
    return ProjectInput(
        project_id="MOCK-LIBRARY-001",
        project_name="Library Management System",
        project_description=(
            "A system for managing books, members "
            "and borrowing records."
        ),
        requirements=[
            Requirement(**item)
            for item in REQUIREMENTS
        ],
    )


def get_graph(request: Request):
    graph = getattr(
        request.app.state,
        "coordinator_graph",
        None,
    )

    if graph is None:
        raise HTTPException(
            status_code=503,
            detail="Coordinator graph is not initialized.",
        )

    return graph


def get_config(thread_id):
    # Validate against persistent Neon records.
    with SessionLocal() as session:
        run = session.scalar(
            select(WorkflowRun).where(
                WorkflowRun.thread_id == thread_id
            )
        )

        if run is None:
            raise HTTPException(
                status_code=404,
                detail="Workflow not found.",
            )

    return {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": 100,
    }


def get_pending_review(snapshot):
    for pending in snapshot.interrupts:
        return pending.value

    return None


def get_workflow_response(request: Request, thread_id: str):
    config = get_config(thread_id)
    graph = get_graph(request)

    snapshot = graph.get_state(config)
    values = snapshot.values or {}

    project_state = values.get("project_state")
    pending_review = get_pending_review(snapshot)

    save_module_executions(
        thread_id=thread_id,
        project_state=project_state,
        module_execution_inputs=values.get(
            "module_execution_inputs", {}
        ),
        events=values.get("events", []),
    )

    module_statuses = {}

    if project_state is not None:
        for name in MODULE_ORDER:
            module_state = project_state.module_states[name]

            module_statuses[name] = {
                "status": module_state.status.value,
                "version": module_state.version,
                "retry_count": module_state.retry_count,
                "validation_passed": module_state.validation_passed,
                "human_feedback": module_state.human_feedback,
            }

    final_report = values.get("final_report") or {}

    if final_report:
        workflow_status = "COMPLETED"
    elif pending_review:
        workflow_status = "WAITING_FOR_REVIEW"
    elif snapshot.next:
        workflow_status = "RUNNING"
    else:
        workflow_status = "STOPPED"

    # Keep the workflow_runs table synchronized.
    with SessionLocal.begin() as session:
        run = session.scalar(
            select(WorkflowRun).where(
                WorkflowRun.thread_id == thread_id
            )
        )

        if run is not None:
            run.status = workflow_status
            run.current_module = (
                values.get("current_module") or None
            )

    return {
        "thread_id": thread_id,
        "workflow_status": workflow_status,
        "current_module": values.get("current_module", ""),
        "pending_review": pending_review,
        "module_statuses": module_statuses,
        "events": values.get("events", []),
        "report_available": bool(final_report),
    }


@router.post("/start")

@router.post("/start")
def start_workflow(
    request: Request,
    project_id: UUID | None = Query(default=None),
):
    with workflow_lock:
        graph = get_graph(request)

        # Existing predefined Library Management mock data
        project = create_demo_project()
        thread_id = str(uuid4())

        with SessionLocal.begin() as session:

            if project_id is None:
                # Preserve the original PP1 workflow behavior
                db_project = Project(
                    name=project.project_name,
                    description=project.project_description,
                    input_data=project.model_dump(mode="json"),
                    status="created",
                )

                session.add(db_project)
                session.flush()

            else:
                # Use the selected saved project
                db_project = session.get(Project, project_id)

                if db_project is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Project not found.",
                    )

                # Update project metadata only.
                # Requirements and module outputs stay mocked.
                project = project.model_copy(
                    update={
                        "project_id": str(db_project.id),
                        "project_name": db_project.name,
                        "project_description": (
                            db_project.description or ""
                        ),
                    }
                )

            run = WorkflowRun(
                project_id=db_project.id,
                thread_id=thread_id,
                status="RUNNING",
            )

            session.add(run)

        project_state = create_initial_project_state(project)
        config = get_config(thread_id)

        initial_state = {
            "project_state": project_state,
            "current_module": "",
            "next_module": "",
            "events": [],
            "final_report": {},
            "module_execution_inputs": {},
        }

        try:
            graph.invoke(
                initial_state,
                config=config,
            )

        except Exception:
            with SessionLocal.begin() as session:
                run = session.scalar(
                    select(WorkflowRun).where(
                        WorkflowRun.thread_id == thread_id
                    )
                )

                if run is not None:
                    run.status = "FAILED"

            raise

        return get_workflow_response(request, thread_id)


@router.get("/{thread_id}/status")
def workflow_status(thread_id: str, request: Request):
    with workflow_lock:
        return get_workflow_response(request, thread_id)


@router.post("/{thread_id}/review")
def submit_review(
    thread_id: str,
    review: ReviewRequest,
    request: Request,
):
    decision = review.decision.strip().lower()
    feedback = review.feedback.strip()

    if decision not in ("approve", "reject"):
        raise HTTPException(
            status_code=422,
            detail="Decision must be approve or reject.",
        )

    if decision == "reject" and not feedback:
        raise HTTPException(
            status_code=422,
            detail="Rejection feedback is required.",
        )

    with workflow_lock:
        graph = get_graph(request)
        config = get_config(thread_id)

        snapshot = graph.get_state(config)
        pending_review = get_pending_review(snapshot)

        if pending_review is None:
            raise HTTPException(
                status_code=409,
                detail="No Module is waiting for human review.",
            )

        decision_data = {
            "decision": decision,
        }

        if decision == "reject":
            decision_data["feedback"] = feedback

        try:
            graph.invoke(
                Command(resume=decision_data),
                config=config,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        response = get_workflow_response(request, thread_id)
        # Record the human decision against the exact reviewed version.
        reviewed_module = pending_review.get("module_name")
        reviewed_version = pending_review.get("version")
        with SessionLocal.begin() as session:
            run = session.scalar(select(WorkflowRun).where(
                WorkflowRun.thread_id == thread_id
            ))
            artifact = session.scalar(select(ArtifactVersion).where(
                ArtifactVersion.workflow_run_id == run.id,
                ArtifactVersion.artifact_key == reviewed_module,
                ArtifactVersion.version_number == reviewed_version,
            ))
            session.add(ReviewDecision(
                workflow_run_id=run.id,
                artifact_version_id=artifact.id if artifact else None,
                module_name=reviewed_module,
                decision=decision.upper(),
                feedback=feedback or None,
                reviewer="PP1_HUMAN_REVIEWER",
            ))
            if artifact is not None:
                artifact.approval_status = (
                    "APPROVED" if decision == "approve" else "REJECTED"
                )
            execution = session.scalar(select(ModuleExecution).where(
                ModuleExecution.workflow_run_id == run.id,
                ModuleExecution.module_name == reviewed_module,
                ModuleExecution.attempt_number == reviewed_version,
            ))
            if execution is not None:
                execution.status = (
                    "APPROVED" if decision == "approve" else "REJECTED"
                )
        return response


@router.get("/{thread_id}/history")
def get_workflow_history(thread_id: str):
    get_config(thread_id)
    with SessionLocal() as session:
        run = session.scalar(select(WorkflowRun).where(
            WorkflowRun.thread_id == thread_id
        ))
        reviews = session.scalars(select(ReviewDecision).where(
            ReviewDecision.workflow_run_id == run.id
        ).order_by(ReviewDecision.created_at)).all()
        artifacts = session.scalars(select(ArtifactVersion).where(
            ArtifactVersion.workflow_run_id == run.id
        ).order_by(ArtifactVersion.created_at)).all()
        executions = session.scalars(select(ModuleExecution).where(
            ModuleExecution.workflow_run_id == run.id
        ).order_by(ModuleExecution.created_at)).all()
        return {
            "thread_id": thread_id,
            "reviews": [{"module": r.module_name, "decision": r.decision,
                         "feedback": r.feedback, "artifact_version_id": str(r.artifact_version_id) if r.artifact_version_id else None}
                        for r in reviews],
            "artifacts": [{"module": a.module_name, "version": a.version_number,
                           "status": a.approval_status, "content": a.content}
                          for a in artifacts],
            "executions": [{"module": e.module_name, "attempt": e.attempt_number,
                            "status": e.status, "input": e.input_data,
                            "output": e.output_data}
                           for e in executions],
        }


@router.get("/{thread_id}/report")
def get_final_report(
    thread_id: str,
    request: Request,
):
    with workflow_lock:
        graph = get_graph(request)
        config = get_config(thread_id)

        snapshot = graph.get_state(config)
        values = snapshot.values or {}

        report = values.get("final_report") or {}

        if not report:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Final report is not available. "
                    "Approve all Modules first."
                ),
            )

        run_id = report.get("run_id")
        project_id = report.get("project_id")

        if not run_id or not project_id:
            raise HTTPException(
                status_code=500,
                detail="Final report metadata is incomplete.",
            )

        markdown_path = (
            OUTPUT_DIR
            / f"{project_id}_{run_id}_final_report.md"
        )

        json_path = (
            OUTPUT_DIR
            / f"{project_id}_{run_id}_final_report.json"
        )

        return {
            "thread_id": thread_id,
            "workflow_status": "COMPLETED",
            "report": report,
            "markdown_report_path": str(markdown_path),
            "json_report_path": str(json_path),
            "markdown_exists": markdown_path.is_file(),
            "json_exists": json_path.is_file(),
        }
