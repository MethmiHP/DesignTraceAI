import pytest

from shared.models.project import ProjectInput
from shared.models.workflow import WorkflowStatus
from importlib.util import find_spec

from coordinator.state_manager import (
    create_initial_project_state,
)

from coordinator.database_integration import (
    prepare_database_design,
)

from coordinator.artifact_store import (
    save_database_artifacts,
)


def create_approved_state():
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

    return project, state

@pytest.mark.skipif(
    find_spec("modules.database_design.database_module") is None
    or find_spec("modules.database_design.artifact_builder") is None,
    reason="Real Database Design Module is not integrated on this branch.",
)


def test_database_artifacts_saved():
    project, state = create_approved_state()

    result = prepare_database_design(
        project,
        state.module_states,
    )

    updated_state = save_database_artifacts(
        state,
        result,
    )

    assert "database_design" in updated_state.module_outputs

    assert (
        updated_state.module_states["database_design"].status
        == WorkflowStatus.REVIEW_REQUIRED
    )

    assert (
        updated_state.module_states["database_design"]
        .validation_passed
    )

    assert (
        updated_state.module_states["database_design"].version
        == 1
    )


def test_blocked_database_artifacts_not_saved():
    project = ProjectInput(
        project_id="P002",
        project_name="Blocked Project",
        project_description="Test dependency blocking.",
    )

    state = create_initial_project_state(project)

    result = prepare_database_design(
        project,
        state.module_states,
    )

    with pytest.raises(ValueError):
        save_database_artifacts(state, result)

    assert "database_design" not in state.module_outputs
