"""
Tests for the integrated database design pipeline.
"""

from shared.models.project import ProjectInput, Requirement

from modules.database_design.design_pipeline import (
    generate_database_design_pipeline,
)


def create_project():

    return ProjectInput(
        project_id="P001",
        project_name="Hospital Appointment System",
        project_description="Patients book appointments with doctors.",
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


def test_pipeline_generates_tables():

    design = generate_database_design_pipeline(
        create_project()
    )

    table_names = {
        table.table_name
        for table in design.tables
    }

    assert "patients" in table_names
    assert "appointments" in table_names
    assert "doctors" in table_names


def test_pipeline_generates_relationships():

    design = generate_database_design_pipeline(
        create_project()
    )

    relationships = {
        (relationship.from_table, relationship.to_table)
        for relationship in design.relationships
    }

    assert ("patients", "appointments") in relationships
    assert ("doctors", "appointments") in relationships


def test_pipeline_generates_foreign_keys():

    design = generate_database_design_pipeline(
        create_project()
    )

    appointments = next(
        table
        for table in design.tables
        if table.table_name == "appointments"
    )

    foreign_keys = {
        column.name
        for column in appointments.columns
        if column.foreign_key is not None
    }

    assert "patient_id" in foreign_keys
    assert "doctor_id" in foreign_keys
