"""
DesignTrace AI - Pipeline Requirement Constraint Integration Tests

Tests whether requirement constraints reach the final
database design through the complete pipeline.
"""

from shared.models.project import ProjectInput, Requirement

from modules.database_design.design_pipeline import (
    generate_database_design_pipeline,
)


def create_project():
    return ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment system.",
        requirements=[
            Requirement(
                requirement_id="FR-01",
                requirement_text="A patient can register an account.",
                database_relevant=True,
            ),
            Requirement(
                requirement_id="FR-02",
                requirement_text="Patient email must be unique.",
                database_relevant=True,
            ),
        ],
    )


def test_pipeline_generates_patient_table():
    design = generate_database_design_pipeline(create_project())

    table_names = [
        table.table_name
        for table in design.tables
    ]

    assert "patients" in table_names


def test_pipeline_applies_unique_email_constraint():
    design = generate_database_design_pipeline(create_project())

    patients = next(
        table
        for table in design.tables
        if table.table_name == "patients"
    )

    email = next(
        column
        for column in patients.columns
        if column.name == "email"
    )

    assert email.unique is True



def test_pipeline_applies_not_null_status_constraint():
    project = ProjectInput(
        project_id="P002",
        project_name="Appointment System",
        project_description="Hospital appointment system.",
        requirements=[
            Requirement(
                requirement_id="FR-03",
                requirement_text=(
                    "A patient can book an appointment."
                ),
                database_relevant=True,
            ),
            Requirement(
                requirement_id="FR-04",
                requirement_text=(
                    "Every appointment must have a status."
                ),
                database_relevant=True,
            ),
        ],
    )

    design = generate_database_design_pipeline(project)

    appointments = next(
        table
        for table in design.tables
        if table.table_name == "appointments"
    )

    status = next(
        column
        for column in appointments.columns
        if column.name == "status"
    )

    assert status.nullable is False

