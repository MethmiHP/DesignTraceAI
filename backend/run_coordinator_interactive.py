"""
DesignTrace AI - Interactive LangGraph Coordinator Demo

Run:
    python run_coordinator_interactive.py

This demonstration uses real terminal-based human decisions
and simulated outputs from the seven DesignTrace AI Modules.
"""

import json
from uuid import uuid4

from langgraph.types import Command

from coordinator.langgraph_workflow import (
    build_coordinator_graph,
    MODULE_ORDER,
    OUTPUT_DIR,
)
from coordinator.state_manager import create_initial_project_state
from shared.models.project import ProjectInput, Requirement
from mocks.mock_modules import REQUIREMENTS


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


def ask_review_decision(review):
    """Display the mock artifact and ask for a real decision."""

    print("\n" + "=" * 65)
    print("HUMAN REVIEW REQUIRED")
    print("=" * 65)

    print("Module:", review["module_name"])
    print("Version:", review["version"])
    print("Project:", review["project_id"])

    print("\nGENERATED MOCK OUTPUT:")
    print(
        json.dumps(
            review["output"],
            indent=2,
            ensure_ascii=False,
        )
    )

    while True:
        decision = input(
            "\nEnter 'approve' or 'reject': "
        ).strip().lower()

        if decision == "approve":
            return {"decision": "approve"}

        if decision == "reject":
            while True:
                feedback = input(
                    "Enter rejection feedback: "
                ).strip()

                if feedback:
                    return {
                        "decision": "reject",
                        "feedback": feedback,
                    }

                print("Feedback cannot be empty.")

        print("Invalid option. Please type approve or reject.")


def main():
    print("\nDESIGNTRACE AI - INTERACTIVE COORDINATOR")
    print("=" * 65)
    print("Execution mode: PP1 mock demonstration")
    print("Workflow engine: LangGraph")
    print("Review mode: Real terminal-based human input")

    project = create_demo_project()
    project_state = create_initial_project_state(project)

    graph = build_coordinator_graph()

    # A unique thread ID identifies this workflow's checkpoints.
    config = {
        "configurable": {
            "thread_id": str(uuid4()),
        },
        "recursion_limit": 100,
    }

    initial_state = {
        "project_state": project_state,
        "current_module": "",
        "next_module": "",
        "events": [],
        "final_report": {},
    }

    result = graph.invoke(initial_state, config=config)

    # Every interrupt is a real pause in LangGraph execution.
    while result.get("__interrupt__"):
        interrupts = result["__interrupt__"]

        # The graph pauses for one Module review at a time.
        review = interrupts[0].value

        decision = ask_review_decision(review)

        # Resume the exact paused LangGraph workflow.
        result = graph.invoke(
            Command(resume=decision),
            config=config,
        )

    print("\n" + "=" * 65)
    print("FINAL WORKFLOW RESULTS")
    print("=" * 65)

    if not result.get("final_report"):
        print("Workflow stopped without a final report.")
        print("\nEvents:")
        for event in result.get("events", []):
            print(
                event["event"],
                event["module"],
                event["details"],
            )
        return

    for module_name in MODULE_ORDER:
        module_state = (
            result["project_state"].module_states[module_name]
        )

        print(
            f"{module_name:<24} "
            f"{module_state.status.value:<18} "
            f"version={module_state.version} "
            f"retries={module_state.retry_count}"
        )

    print("\nWORKFLOW: COMPLETED")

    print("\nREVIEW HISTORY:")

    for event in result["events"]:
        print(
            f"{event['event']:<25} "
            f"{event['module']:<24} "
            f"{event['details']}"
        )

    print("\nFINAL REPORTS:")

    for event in result["events"]:
        if event["event"] == "FINAL_REPORT_GENERATED":
            markdown_path = OUTPUT_DIR / (
                str(event["details"]).replace("\\", "/").split("/")[-1]
            )

            json_path = markdown_path.with_suffix(".json")

            print("Markdown report:", markdown_path)
            print("JSON report:", json_path)
            break

if __name__ == "__main__":
    main()
