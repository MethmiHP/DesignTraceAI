"""
Test the integrated database pipeline
inside the Coordinator workflow.
"""

from coordinator.state_manager import (
    create_initial_project_state,
)

from coordinator.database_review_workflow import (
    run_database_review_workflow,
)

from shared.models.project import (
    ProjectInput,
    Requirement,
)

from shared.models.workflow import WorkflowStatus


def create_test_state():

    project = ProjectInput(
        project_id="P001",
        project_name="Hospital Appointment System",
        project_description="Patient appointment booking.",
        requirements=[
            Requirement(
                requirement_id="FR-01",
                requirement_text=(
                    "A patient can register an account."
                ),
                database_relevant=True,
            ),
            Requirement(
                requirement_id="FR-02",
                requirement_text=(
                    "A patient can book an appointment "
                    "with a doctor."
                ),
                database_relevant=True,
            ),
        ],
    )

    state = create_initial_project_state(project)

    state.module_states[
        "requirement_analysis"
    ].status = WorkflowStatus.APPROVED

    state.module_states[
        "architecture_design"
    ].status = WorkflowStatus.APPROVED

    return state


def test_pipeline_runs_through_coordinator():

    state = create_test_state()

    run_database_review_workflow(state)

    module = state.module_states["database_design"]

    assert module.status == WorkflowStatus.REVIEW_REQUIRED
    assert module.validation_passed is True
    assert module.version == 1


def test_pipeline_output_saved():

    state = create_test_state()

    run_database_review_workflow(state)

    assert "database_design" in state.module_outputs

    output = state.module_outputs["database_design"]

    assert output is not None
