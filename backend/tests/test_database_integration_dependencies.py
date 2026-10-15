from shared.models.project import ProjectInput
from shared.models.workflow import WorkflowStatus

from coordinator.state_manager import (
    create_initial_project_state,
)

from coordinator.database_integration import (
    prepare_database_design,
)


def create_project_and_state():
    project = ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment system.",
    )

    state = create_initial_project_state(project)

    return project, state


def test_database_blocked_when_dependencies_pending():
    project, state = create_project_and_state()

    result = prepare_database_design(
        project,
        state.module_states,
    )

    assert result["status"] == "PENDING"
    assert result["artifacts"] is None
    assert "requirement_analysis" in result["missing_dependencies"]
    assert "architecture_design" in result["missing_dependencies"]


def test_database_blocked_when_architecture_not_approved():
    project, state = create_project_and_state()

    state.module_states[
        "requirement_analysis"
    ].status = WorkflowStatus.APPROVED

    result = prepare_database_design(
        project,
        state.module_states,
    )

    assert result["status"] == "PENDING"
    assert result["artifacts"] is None
    assert "architecture_design" in result["missing_dependencies"]


def test_database_runs_when_dependencies_approved():
    project, state = create_project_and_state()

    state.module_states[
        "requirement_analysis"
    ].status = WorkflowStatus.APPROVED

    state.module_states[
        "architecture_design"
    ].status = WorkflowStatus.APPROVED

    result = prepare_database_design(
        project,
        state.module_states,
    )

    assert result["status"] == "REVIEW_REQUIRED"
    assert result["missing_dependencies"] == []
    assert result["artifacts"]["validation_report"]["passed"]
