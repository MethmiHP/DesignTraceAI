"""
DesignTrace AI - Database Review Workflow

Coordinates:
    - Dependency checking
    - Initial database generation
    - Feedback-aware regeneration
    - Validation and artifact generation
    - Version storage
    - Human review
"""

from coordinator.state_manager import ProjectState
from coordinator.review_manager import request_human_review
from coordinator.version_manager import save_module_output_version

from shared.models.workflow import WorkflowStatus
from shared.models.database import DatabaseDesign

from modules.database_design.design_pipeline import (
    generate_database_design_pipeline,
)
from modules.database_design.artifact_builder import (
    build_database_artifacts,
)


REQUIRED_MODULES = (
    "requirement_analysis",
    "architecture_design",
)


def run_database_review_workflow(
    state: ProjectState,
) -> ProjectState:
    """
    Generate or regenerate a database design and
    save it as a versioned draft for human review.
    """

    module_name = "database_design"
    module = state.module_states[module_name]

    # Step 1: Check dependencies.
    for dependency in REQUIRED_MODULES:
        if (
            state.module_states[dependency].status
            != WorkflowStatus.APPROVED
        ):
            raise ValueError(
                "Database Design Module blocked: "
                f"{dependency} is not approved."
            )

    if module.status not in (
        WorkflowStatus.PENDING,
        WorkflowStatus.RETRYING,
    ):
        raise ValueError(
            "Database Design Module is not ready."
        )

    previous_design = None
    feedback = []

    # Step 2: Prepare feedback for regeneration.
    if module.status == WorkflowStatus.RETRYING:
        feedback = list(module.human_feedback)

        previous_artifacts = state.module_outputs.get(
            module_name
        )

        if previous_artifacts is None:
            raise ValueError(
                "Cannot regenerate: previous database "
                "artifacts are missing."
            )

        previous_design_data = previous_artifacts.get(
            "database_design"
        )

        if previous_design_data is None:
            raise ValueError(
                "Cannot regenerate: previous database "
                "design is missing."
            )

        previous_design = DatabaseDesign.model_validate(
            previous_design_data
        )

    # Step 3: Generate or revise design.
    module.status = WorkflowStatus.RUNNING

    try:
        design = generate_database_design_pipeline(
           state.project,
           feedback=module.human_feedback,
        )

        # Step 4: Validate and build artifacts.
        artifacts = build_database_artifacts(
            design,
            state.project.requirements,
        )

        validation = artifacts["validation_report"]
        module.validation_passed = validation["passed"]

        # Do not save an invalid regenerated design.
        if not module.validation_passed:
            module.status = WorkflowStatus.FAILED
            return state

        # Step 5: Save a new version.
        save_module_output_version(
            state,
            module_name,
            artifacts,
        )

        # Step 6: Request human review.
        request_human_review(state, module_name)

        return state

    except Exception:
        module.status = WorkflowStatus.FAILED
        module.validation_passed = False
        raise
