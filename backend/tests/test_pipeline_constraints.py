"""
Tests for constraint generator integration
with the Database Design Pipeline.
"""

from unittest.mock import patch

from shared.models.project import ProjectInput
from modules.database_design.design_pipeline import (
    generate_database_design_pipeline,
)


def create_project():
    return ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment system.",
        requirements=[],
    )


def test_pipeline_calls_constraint_generator():
    project = create_project()

    with patch(
        "modules.database_design.design_pipeline."
        "generate_database_constraints",
        wraps=None,
    ) as mock_constraints:

        # Return the original design unchanged.
        mock_constraints.side_effect = lambda design: design

        generate_database_design_pipeline(project)

        mock_constraints.assert_called_once()


def test_pipeline_constraint_generator_runs_without_feedback():
    project = create_project()

    with patch(
        "modules.database_design.design_pipeline."
        "generate_database_constraints",
        side_effect=RuntimeError("Constraint step reached"),
    ):
        try:
            generate_database_design_pipeline(project)
        except RuntimeError as error:
            assert str(error) == "Constraint step reached"
        else:
            raise AssertionError(
                "Constraint generator was not called."
            )
