"""
Tests for feedback integration in the database pipeline.
"""

from shared.models.project import ProjectInput, Requirement

from modules.database_design.design_pipeline import (
    generate_database_design_pipeline,
)


def create_project():
    return ProjectInput(
        project_id="P001",
        project_name="Hospital Appointment System",
        project_description="Patient appointment management.",
        requirements=[
            Requirement(
                requirement_id="FR-01",
                requirement_text="A patient can register an account.",
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


def test_pipeline_accepts_feedback():

    design = generate_database_design_pipeline(
        create_project(),
        feedback=["Add doctor specialization."],
    )

    assert design is not None


def test_pipeline_adds_specialization():

    design = generate_database_design_pipeline(
        create_project(),
        feedback=["Add doctor specialization."],
    )

    doctors = next(
        table for table in design.tables
        if table.table_name == "doctors"
    )

    column_names = {
        column.name for column in doctors.columns
    }

    assert "specialization" in column_names


def test_pipeline_without_feedback():

    design = generate_database_design_pipeline(
        create_project()
    )

    assert len(design.tables) > 0
