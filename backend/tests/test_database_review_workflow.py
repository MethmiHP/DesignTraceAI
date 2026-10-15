import pytest

from coordinator.state_manager import (
    create_initial_project_state,
)
from coordinator.database_review_workflow import (
    run_database_review_workflow,
)
from coordinator.review_manager import (
    approve_module_output,
    request_module_retry,
)
from shared.models.project import ProjectInput
from shared.models.workflow import WorkflowStatus


def create_state():
    project = ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment system.",
    )

    state = create_initial_project_state(project)

    state.module_states[
        "requirement_analysis"
    ].status = WorkflowStatus.APPROVED

    state.module_states[
        "architecture_design"
    ].status = WorkflowStatus.APPROVED

    return state


def test_database_output_requires_review():
    state = create_state()

    run_database_review_workflow(state)

    module = state.module_states["database_design"]

    assert module.status == WorkflowStatus.REVIEW_REQUIRED
    assert module.validation_passed is True
    assert module.version == 1
    assert "database_design" in state.module_outputs


def test_database_can_be_approved():
    state = create_state()

    run_database_review_workflow(state)
    approve_module_output(state, "database_design")

    assert (
        state.module_states["database_design"].status
        == WorkflowStatus.APPROVED
    )


def test_database_can_request_retry():
    state = create_state()

    run_database_review_workflow(state)

    request_module_retry(
        state,
        "database_design",
        feedback="Add doctor specialization.",
    )

    module = state.module_states["database_design"]

    assert module.status == WorkflowStatus.RETRYING
    assert module.retry_count == 1
    assert module.validation_passed is False


def test_database_blocked_without_approval():
    state = create_state()

    state.module_states[
        "architecture_design"
    ].status = WorkflowStatus.PENDING

    with pytest.raises(ValueError):
        run_database_review_workflow(state)

    assert (
        state.module_states["database_design"].status
        == WorkflowStatus.PENDING
    )
