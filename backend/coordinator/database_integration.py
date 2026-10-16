"""
Connect Database Design Module to Coordinator.
Check dependencies before generating database artifacts.

The real Database Design Module is imported only when
database generation is requested.
"""

from shared.models.project import ProjectInput
from shared.models.workflow import WorkflowStatus

from coordinator.dependency_manager import check_dependencies


def prepare_database_design(
    project: ProjectInput,
    module_states: dict | None = None,
) -> dict:

    # Step 1: Check dependencies.
    if module_states is not None:
        allowed, missing = check_dependencies(
            "database_design",
            module_states,
        )

        if not allowed:
            return {
                "project_id": project.project_id,
                "module_name": "database_design",
                "status": WorkflowStatus.PENDING.value,
                "missing_dependencies": missing,
                "artifacts": None,
            }

    # Step 2: Load the real Database Design Module only
    # when its integration is actually needed.
    try:
        from modules.database_design.database_module import (
            generate_database_design,
        )

        from modules.database_design.artifact_builder import (
            build_database_artifacts,
        )

    except ImportError as exc:
        raise RuntimeError(
            "The real Database Design Module is not available "
            "on this branch. Use the LangGraph mock workflow "
            "for the PP1 demonstration, or integrate the real "
            "Database Design Module before running this function."
        ) from exc

    # Step 3: Generate database design.
    design = generate_database_design(project)

    # Step 4: Build and validate artifacts.
    artifacts = build_database_artifacts(
        design,
        project.requirements,
    )

    # Step 5: Send output for human review.
    if artifacts["validation_report"]["passed"]:
        status = WorkflowStatus.REVIEW_REQUIRED.value
    else:
        status = WorkflowStatus.FAILED.value

    return {
        "project_id": project.project_id,
        "module_name": "database_design",
        "status": status,
        "missing_dependencies": [],
        "artifacts": artifacts,
    }
