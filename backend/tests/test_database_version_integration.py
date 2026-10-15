from coordinator.state_manager import (
    create_initial_project_state,
)
from coordinator.database_review_workflow import (
    run_database_review_workflow,
)
from coordinator.review_manager import (
    request_module_retry,
    approve_module_output,
)
from coordinator.version_manager import (
    get_module_output_history,
    get_module_output_version,
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


def test_database_first_version_saved():
    state = create_state()

    run_database_review_workflow(state)

    history = get_module_output_history(
        state, "database_design"
    )

    assert len(history) == 1
    assert history[0]["version"] == 1

    assert (
        state.module_states["database_design"].status
        == WorkflowStatus.REVIEW_REQUIRED
    )


def test_database_retry_creates_second_version():
    state = create_state()

    run_database_review_workflow(state)

    request_module_retry(
        state,
        "database_design",
        feedback="Add doctor specialization.",
    )

    run_database_review_workflow(state)

    history = get_module_output_history(
        state, "database_design"
    )

    assert len(history) == 2
    assert history[0]["version"] == 1
    assert history[1]["version"] == 2

    assert (
        state.module_states["database_design"].status
        == WorkflowStatus.REVIEW_REQUIRED
    )


def test_previous_version_preserved():
    state = create_state()

    run_database_review_workflow(state)

    first = get_module_output_version(
        state, "database_design", 1
    )

    request_module_retry(
        state,
        "database_design",
        feedback="Improve relationships.",
    )

    run_database_review_workflow(state)

    first_after_retry = get_module_output_version(
        state, "database_design", 1
    )

    assert first == first_after_retry


def test_approval_after_regeneration():
    state = create_state()

    run_database_review_workflow(state)

    request_module_retry(
        state,
        "database_design",
        feedback="Add missing database constraints.",
    )

    run_database_review_workflow(state)

    approve_module_output(
        state,
        "database_design",
    )

    assert (
        state.module_states["database_design"].status
        == WorkflowStatus.APPROVED
    )

    assert (
        state.module_states["database_design"].version
        == 2
    )
