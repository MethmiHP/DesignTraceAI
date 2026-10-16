"""
Store module outputs in Coordinator shared state.
"""

from typing import Any

from shared.models.workflow import WorkflowStatus


def save_database_artifacts(
    state: Any,
    result: dict,
) -> Any:
    """
    Save a validated database design result
    for human review.
    """

    module_state = state.module_states["database_design"]

    if result["status"] != WorkflowStatus.REVIEW_REQUIRED.value:
        raise ValueError(
            "Only validated database artifacts can be "
            "saved for review."
        )

    artifacts = result.get("artifacts")

    if not artifacts:
        raise ValueError("Database artifacts are missing.")

    validation = artifacts.get("validation_report", {})

    if not validation.get("passed", False):
        raise ValueError(
            "Database validation must pass before review."
        )

    # Save the artifacts as a draft.
    # ProjectState must support the module_outputs field.
    if not hasattr(state, "module_outputs"):
        raise ValueError(
            "ProjectState must define a module_outputs field."
        )

    state.module_outputs["database_design"] = artifacts

    # Update workflow information.
    module_state.status = WorkflowStatus.REVIEW_REQUIRED
    module_state.validation_passed = True
    module_state.version += 1

    return state
