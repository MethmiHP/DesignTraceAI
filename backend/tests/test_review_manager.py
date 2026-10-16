import pytest

from coordinator.state_manager import (
    create_initial_project_state,
)
from coordinator.review_manager import (
    request_human_review,
    approve_module_output,
    request_module_retry,
)
from shared.models.project import ProjectInput
from shared.models.workflow import WorkflowStatus


def create_review_state():
    project = ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment system.",
    )

    state = create_initial_project_state(project)

    module = state.module_states["database_design"]
    module.status = WorkflowStatus.RUNNING
    module.validation_passed = True
    module.version = 1

    state.module_outputs["database_design"] = {
        "validation_report": {
            "passed": True,
            "issues": [],
        },
        "sql_schema": "CREATE TABLE patients (...);",
    }

    return state


def test_output_requires_human_review():
    state = create_review_state()

    request_human_review(state, "database_design")

    assert (
        state.module_states["database_design"].status
        == WorkflowStatus.REVIEW_REQUIRED
    )


def test_human_approval():
    state = create_review_state()

    request_human_review(state, "database_design")
    approve_module_output(state, "database_design")

    assert (
        state.module_states["database_design"].status
        == WorkflowStatus.APPROVED
    )


def test_human_feedback_requests_retry():
    state = create_review_state()

    request_human_review(state, "database_design")

    request_module_retry(
        state,
        "database_design",
        feedback="Add doctor specialization.",
    )

    module = state.module_states["database_design"]

    assert module.status == WorkflowStatus.RETRYING
    assert module.retry_count == 1
    assert module.validation_passed is False
    assert "Add doctor specialization." in module.human_feedback


def test_invalid_output_cannot_be_approved():
    state = create_review_state()

    state.module_states[
        "database_design"
    ].validation_passed = False

    with pytest.raises(ValueError):
        approve_module_output(
            state,
            "database_design",
        )


def test_retry_limit():
    state = create_review_state()

    module = state.module_states["database_design"]
    module.retry_count = 3

    request_human_review(state, "database_design")

    request_module_retry(
        state,
        "database_design",
        max_retries=3,
    )

    assert module.status == WorkflowStatus.FAILED
