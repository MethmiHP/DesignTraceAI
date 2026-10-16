"""
DesignTrace AI - Coordinator API

PP1 demonstration:
- Start a LangGraph workflow with mock Module outputs
- Inspect pending human reviews
- Approve or reject outputs
- Retrieve the final report

Run FastAPI from the backend directory.
"""

from threading import Lock
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from langgraph.types import Command

from coordinator.langgraph_workflow import (
    build_coordinator_graph,
    MODULE_ORDER,
    OUTPUT_DIR,
)
from coordinator.state_manager import create_initial_project_state
from shared.models.project import ProjectInput, Requirement
from mocks.mock_modules import REQUIREMENTS


router = APIRouter(
    prefix="/api/coordinator",
    tags=["Coordinator Agent"],
)

# IMPORTANT:
# Keep one graph instance alive so its InMemorySaver retains checkpoints.
graph = build_coordinator_graph()

# Track workflow IDs created through this API.
active_threads = set()

# Protect the shared in-memory graph from overlapping API operations.
workflow_lock = Lock()


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


def get_config(thread_id):
    if thread_id not in active_threads:
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
    """
    Read the actual LangGraph interrupt from the saved checkpoint.
    """
    for pending in snapshot.interrupts:
        return pending.value

    return None


def get_workflow_response(thread_id):
    config = get_config(thread_id)
    snapshot = graph.get_state(config)

    values = snapshot.values or {}

    project_state = values.get("project_state")
    pending_review = get_pending_review(snapshot)

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
def start_workflow():
    with workflow_lock:
        project = create_demo_project()

        project_state = create_initial_project_state(project)

        thread_id = str(uuid4())

        active_threads.add(thread_id)

        config = get_config(thread_id)

        initial_state = {
            "project_state": project_state,
            "current_module": "",
            "next_module": "",
            "events": [],
            "final_report": {},
        }

        graph.invoke(
            initial_state,
            config=config,
        )

        return get_workflow_response(thread_id)


@router.get("/{thread_id}/status")
def workflow_status(thread_id: str):
    with workflow_lock:
        return get_workflow_response(thread_id)


@router.post("/{thread_id}/review")
def submit_review(
    thread_id: str,
    review: ReviewRequest,
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

        return get_workflow_response(thread_id)


@router.get("/{thread_id}/report")
def get_final_report(thread_id: str):
    with workflow_lock:
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