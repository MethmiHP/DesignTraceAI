"""
Tests for baseline requirement-driven schema generation.
"""

from shared.models.project import ProjectInput, Requirement

from modules.database_design.schema_generator import (
    generate_schema_from_concepts,
)


def test_schema_generator_creates_tables():

    project = ProjectInput(
        project_id="P001",
        project_name="Hospital System",
        project_description="Appointment management.",
        requirements=[
            Requirement(
                requirement_id="FR-01",
                requirement_text=(
                    "A patient can book an appointment "
                    "with a doctor."
                ),
                database_relevant=True,
            ),
        ],
    )

    design = generate_schema_from_concepts(project)

    table_names = {
        table.table_name
        for table in design.tables
    }

    assert "patients" in table_names
    assert "appointments" in table_names
    assert "doctors" in table_names


def test_schema_generator_creates_primary_keys():

    project = ProjectInput(
        project_id="P002",
        project_name="Hospital System",
        project_description="Patient registration.",
        requirements=[
            Requirement(
                requirement_id="FR-01",
                requirement_text="A patient can register.",
                database_relevant=True,
            ),
        ],
    )

    design = generate_schema_from_concepts(project)

    patient_table = next(
        table for table in design.tables
        if table.table_name == "patients"
    )

    assert any(
        column.primary_key
        for column in patient_table.columns
    )


def test_schema_generator_adds_attributes():

    project = ProjectInput(
        project_id="P003",
        project_name="Hospital System",
        project_description="Patient registration.",
        requirements=[
            Requirement(
                requirement_id="FR-01",
                requirement_text=(
                    "A patient must provide an email "
                    "and phone number."
                ),
                database_relevant=True,
            ),
        ],
    )

    design = generate_schema_from_concepts(project)

    patient_table = next(
        table for table in design.tables
        if table.table_name == "patients"
    )

    column_names = {
        column.name
        for column in patient_table.columns
    }

    assert "patient_id" in column_names
    assert "email" in column_names
    assert "phone" in column_names


def test_schema_generator_ignores_non_database_requirements():

    project = ProjectInput(
        project_id="P004",
        project_name="Sample System",
        project_description="Sample project.",
        requirements=[
            Requirement(
                requirement_id="NFR-01",
                requirement_text="The system must respond quickly.",
                database_relevant=False,
            ),
        ],
    )

    design = generate_schema_from_concepts(project)

    assert design.tables == []
    assert design.relationships == []
