"""
DesignTrace AI - Database End-to-End Workflow Test
==================================================

Tests the complete Database Design Module workflow
managed by the Coordinator Agent.
"""

from coordinator.state_manager import create_initial_project_state
from coordinator.database_review_workflow import run_database_review_workflow
from coordinator.review_manager import (
    request_module_retry,
    approve_module_output,
)
from coordinator.version_manager import get_module_output_version

from shared.models.project import ProjectInput
from shared.models.workflow import WorkflowStatus


def create_test_state():
    """Create a test project with approved dependencies."""

    project = ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment booking system.",
    )

    state = create_initial_project_state(project)

    state.module_states[
        "requirement_analysis"
    ].status = WorkflowStatus.APPROVED

    state.module_states[
        "architecture_design"
    ].status = WorkflowStatus.APPROVED

    return state


def test_database_complete_end_to_end_workflow():
    """
    Verify database generation, review, retry,
    version preservation, and approval.
    """

    state = create_test_state()

    # STEP 1: Generate first database design.
    run_database_review_workflow(state)

    assert (
        state.module_states["database_design"].status
        == WorkflowStatus.REVIEW_REQUIRED
    )

    assert state.module_states["database_design"].version == 1

    # STEP 2: Retrieve first version.
    first_version = get_module_output_version(
        state,
        "database_design",
        1,
    )

    assert first_version is not None

    # STEP 3: Request changes.
    request_module_retry(
        state,
        "database_design",
        feedback="Add doctor specialization.",
    )

    assert (
        state.module_states["database_design"].status
        == WorkflowStatus.RETRYING
    )

    # STEP 4: Regenerate database design.
    run_database_review_workflow(state)

    assert (
        state.module_states["database_design"].status
        == WorkflowStatus.REVIEW_REQUIRED
    )

    assert state.module_states["database_design"].version == 2

    # STEP 5: Verify previous version is preserved.
    preserved_version = get_module_output_version(
        state,
        "database_design",
        1,
    )

    assert preserved_version == first_version

    # STEP 6: Verify second version exists.
    second_version = get_module_output_version(
        state,
        "database_design",
        2,
    )

    assert second_version is not None

    # STEP 7: Approve regenerated design.
    approve_module_output(
        state,
        "database_design",
    )

    assert (
        state.module_states["database_design"].status
        == WorkflowStatus.APPROVED
    )

    assert state.module_states["database_design"].validation_passed

    # STEP 8: Verify database artifacts exist.
    assert "database_design" in state.module_outputs

    artifacts = state.module_outputs["database_design"]

    assert "validation_report" in artifacts
    assert "er_diagram" in artifacts
    assert "sql_schema" in artifacts
    assert "requirement_mappings" in artifacts