"""
DesignTrace AI - LangGraph Coordinator PP1 Demo

Runs all seven Modules with mock data, dependency checking,
output validation, simulated human review, retry/versioning,
and final report generation.

Run from the backend directory:
    python -m coordinator.langgraph_workflow
"""

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

from shared.models.project import ProjectInput, Requirement
from shared.models.workflow import WorkflowStatus

from coordinator.state_manager import (
    ProjectState,
    create_initial_project_state,
)
from coordinator.dependency_manager import (
    MODULE_DEPENDENCIES,
    check_dependencies,
)
from coordinator.review_manager import (
    request_human_review,
    approve_module_output,
    request_module_retry,
)

from mocks.mock_modules import REQUIREMENTS, execute_mock_module


MODULE_ORDER = [
    "requirement_analysis",
    "architecture_design",
    "database_design",
    "api_component_design",
    "traceability",
    "quality_evaluation",
    "adr",
]

OUTPUT_DIR = (
    Path(__file__).resolve().parents[1]
    / "outputs"
    / "coordinator_demo"
)


class GraphState(TypedDict):
    project_state: ProjectState
    current_module: str
    next_module: str
    events: list[dict]
    final_report: dict


def record_event(state, event, module="", details=""):
    state["events"].append({
        "event": event,
        "module": module,
        "details": details,
    })


def validate_mock_output(module_name, output, project):
    """Basic structural validation for PP1 mock outputs."""
    if not isinstance(output, dict):
        return False, "Output must be a dictionary."

    if output.get("project_id") != project.project_id:
        return False, "Project ID mismatch."

    if output.get("module_name") != module_name:
        return False, "Module name mismatch."

    if not isinstance(output.get("data"), dict):
        return False, "Missing structured Module data."

    if not output["data"]:
        return False, "Module output is empty."

    expected_ids = {
        requirement.requirement_id
        for requirement in project.requirements
    }

    actual_ids = set(output.get("source_requirements", []))

    if not expected_ids.issubset(actual_ids):
        return False, "Requirement references are incomplete."

    # Demonstrate a simple domain-specific check.
    if module_name == "database_design":
        data = output["data"]

        if not data.get("tables"):
            return False, "Database tables are missing."

        if not isinstance(data.get("relationships"), list):
            return False, "Database relationships are missing."

    return True, "Validation passed."


def get_approved_outputs(project_state):
    """Only approved outputs may be passed downstream."""
    return {
        name: deepcopy(project_state.module_outputs[name])
        for name, module_state in project_state.module_states.items()
        if (
            module_state.status == WorkflowStatus.APPROVED
            and name in project_state.module_outputs
        )
    }


def initialize_node(state):
    project_state = state["project_state"]

    # Prove that the dependency manager blocks early execution.
    ready, missing = check_dependencies(
        "database_design",
        project_state.module_states,
    )

    if not ready:
        record_event(
            state,
            "DEPENDENCY_BLOCKED",
            "database_design",
            f"Waiting for: {', '.join(missing)}",
        )

    record_event(state, "WORKFLOW_STARTED")
    state["next_module"] = MODULE_ORDER[0]
    return state


def select_module_node(state):
    project_state = state["project_state"]

    for module_name in MODULE_ORDER:
        status = project_state.module_states[module_name].status

        if status == WorkflowStatus.APPROVED:
            continue

        if status == WorkflowStatus.FAILED:
            record_event(state, "WORKFLOW_FAILED", module_name)
            state["next_module"] = "stop"
            return state

        ready, missing = check_dependencies(
            module_name,
            project_state.module_states,
        )

        if ready:
            state["current_module"] = module_name
            state["next_module"] = "execute"
            return state

        record_event(
            state,
            "WAITING_FOR_DEPENDENCY",
            module_name,
            ", ".join(missing),
        )

        state["next_module"] = "stop"
        return state

    state["next_module"] = "report"
    return state


def execute_module_node(state):
    project_state = state["project_state"]
    module_name = state["current_module"]
    module_state = project_state.module_states[module_name]

    ready, missing = check_dependencies(
        module_name,
        project_state.module_states,
    )

    if not ready:
        raise RuntimeError(
            f"{module_name} blocked by dependencies: {missing}"
        )

    # Increment the version for every new output.
    module_state.version += 1
    module_state.status = WorkflowStatus.RUNNING

    output = execute_mock_module(
        module_name=module_name,
        project=project_state.project,
        approved_outputs=get_approved_outputs(project_state),
        version=module_state.version,
    )

    valid, reason = validate_mock_output(
        module_name,
        output,
        project_state.project,
    )

    module_state.validation_passed = valid

    if not valid:
        module_state.status = WorkflowStatus.FAILED
        record_event(state, "VALIDATION_FAILED", module_name, reason)
        state["next_module"] = "stop"
        return state

    # Store current output and preserve a versioned history.
    project_state.module_outputs[module_name] = output

    project_state.module_output_history.setdefault(
        module_name, []
    ).append(deepcopy(output))

    request_human_review(project_state, module_name)

    record_event(
        state,
        "REVIEW_REQUIRED",
        module_name,
        f"Version {module_state.version}",
    )

    state["next_module"] = "review"
    return state


def review_module_node(state):
    """
    Pause the LangGraph workflow for a real human decision.

    The runner will resume this node with:
        {"decision": "approve"}
    or:
        {"decision": "reject", "feedback": "..."}
    """
    project_state = state["project_state"]
    module_name = state["current_module"]
    module_state = project_state.module_states[module_name]

    output = project_state.module_outputs[module_name]

    # LangGraph pauses here until the runner provides a decision.
    decision_data = interrupt({
        "type": "HUMAN_REVIEW",
        "project_id": project_state.project.project_id,
        "module_name": module_name,
        "version": module_state.version,
        "output": output["data"],
        "message": "Approve or reject this Module output.",
    })

    decision = str(
        decision_data.get("decision", "")
    ).strip().lower()

    if decision == "approve":
        approve_module_output(project_state, module_name)

        record_event(
            state,
            "HUMAN_APPROVED",
            module_name,
            f"Approved version {module_state.version}",
        )

        state["next_module"] = "continue"
        return state

    if decision == "reject":
        feedback = str(
            decision_data.get("feedback", "")
        ).strip()

        if not feedback:
            raise ValueError(
                "Feedback is required when rejecting an output."
            )

        request_module_retry(
            project_state,
            module_name,
            feedback=feedback,
            max_retries=3,
        )

        record_event(
            state,
            "HUMAN_REJECTED",
            module_name,
            feedback,
        )

        state["next_module"] = "retry"
        return state

    raise ValueError(
        "Invalid review decision. Use 'approve' or 'reject'."
    )


def final_report_node(state):
    project_state = state["project_state"]

    not_approved = [
        name
        for name in MODULE_ORDER
        if (
            project_state.module_states[name].status
            != WorkflowStatus.APPROVED
        )
    ]

    if not_approved:
        raise RuntimeError(
            f"Cannot generate final report. "
            f"Unapproved Modules: {not_approved}"
        )

    report = {
        "project_id": project_state.project.project_id,
        "project_name": project_state.project.project_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "MOCK_PP1",
        "workflow_status": "COMPLETED",
        "requirements": [
            requirement.model_dump()
            for requirement in project_state.project.requirements
        ],
        "module_statuses": {
            name: {
                "status": module.status.value,
                "version": module.version,
                "retry_count": module.retry_count,
                "human_feedback": module.human_feedback,
            }
            for name, module in project_state.module_states.items()
        },
        "approved_artifacts": get_approved_outputs(project_state),
        "artifact_version_history": (
            project_state.module_output_history
        ),
        "execution_events": state["events"],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Unique ID for every completed workflow run.
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")

    report["run_id"] = run_id

    json_path = (
        OUTPUT_DIR
        / f"{project_state.project.project_id}_{run_id}_final_report.json"
    )

    markdown_path = (
        OUTPUT_DIR
        / f"{project_state.project.project_id}_{run_id}_final_report.md"
    )

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    lines = [
        "# DesignTrace AI - Final Software Design Report",
        "",
        f"**Project:** {report['project_name']}",
        f"**Project ID:** {report['project_id']}",
        f"**Run ID:** {report['run_id']}",
        "**Execution:** PP1 mock demonstration",
        "**Status:** COMPLETED",
        "",
        "## Requirements",
        "",
    ]

    for requirement in report["requirements"]:
        lines.append(
            f"- **{requirement['requirement_id']}**: "
            f"{requirement['requirement_text']}"
        )

    for module_name in MODULE_ORDER:
        module_info = report["module_statuses"][module_name]
        artifact = report["approved_artifacts"][module_name]

        lines.extend([
            "",
            f"## {module_name.replace('_', ' ').title()}",
            "",
            f"**Status:** {module_info['status']}",
            f"**Version:** {module_info['version']}",
            f"**Retries:** {module_info['retry_count']}",
            "",
            "```json",
            json.dumps(
                artifact["data"],
                indent=2,
                ensure_ascii=False,
            ),
            "```",
        ])

    lines.extend([
        "",
        "## Review and Execution History",
        "",
    ])

    for event in state["events"]:
        lines.append(
            f"- {event['event']}: "
            f"{event['module']} {event['details']}"
        )

    markdown_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    state["final_report"] = report
    record_event(
        state,
        "FINAL_REPORT_GENERATED",
        details=str(markdown_path),
    )

    return state


def route_selection(state):
    return state["next_module"]


def route_execution(state):
    return state["next_module"]


def route_review(state):
    return state["next_module"]


def build_coordinator_graph():
    graph = StateGraph(GraphState)

    graph.add_node("initialize", initialize_node)
    graph.add_node("select_module", select_module_node)
    graph.add_node("execute_module", execute_module_node)
    graph.add_node("review_module", review_module_node)
    graph.add_node("final_report", final_report_node)

    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "select_module")

    graph.add_conditional_edges(
        "select_module",
        route_selection,
        {
            "execute": "execute_module",
            "report": "final_report",
            "stop": END,
        },
    )

    graph.add_conditional_edges(
        "execute_module",
        route_execution,
        {
            "review": "review_module",
            "stop": END,
        },
    )

    graph.add_conditional_edges(
        "review_module",
        route_review,
        {
            "retry": "execute_module",
            "continue": "select_module",
        },
    )

    graph.add_edge("final_report", END)

    return graph.compile(checkpointer=InMemorySaver())


def run_demo():
    project = ProjectInput(
        project_id="MOCK-LIBRARY-001",
        project_name="Library Management System",
        project_description=(
            "A system for storing books, members "
            "and borrowing records."
        ),
        requirements=[
            Requirement(**item) for item in REQUIREMENTS
        ],
    )

    project_state = create_initial_project_state(project)

    graph = build_coordinator_graph()

    initial_state = {
        "project_state": project_state,
        "current_module": "",
        "next_module": "",
        "events": [],
        "final_report": {},
    }

    result = graph.invoke(
        initial_state,
        config={"recursion_limit": 100},
    )

    print("\nDESIGNTRACE AI - LANGGRAPH PP1 DEMO")
    print("=" * 55)

    for event in result["events"]:
        print(
            f"{event['event']:<25} "
            f"{event['module']:<24} "
            f"{event['details']}"
        )

    print("\nFINAL MODULE STATUSES")

    for name, module in result["project_state"].module_states.items():
        print(
            f"{name:<24} "
            f"{module.status.value:<18} "
            f"version={module.version} "
            f"retries={module.retry_count}"
        )

    report = result["final_report"]

    if report:
        print("\nWORKFLOW:", report["workflow_status"])
        print("FINAL REPORT LOCATION:", OUTPUT_DIR)
    else:
        print("\nWorkflow stopped before final report.")

    return result


if __name__ == "__main__":
    run_demo()
