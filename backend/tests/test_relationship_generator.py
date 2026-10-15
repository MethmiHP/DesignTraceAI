from shared.models.project import ProjectInput, Requirement

from modules.database_design.schema_generator import (
    generate_schema_from_concepts,
)

from modules.database_design.relationship_generator import (
    add_database_relationships,
)


def create_design():

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

    return generate_schema_from_concepts(project)


def test_patient_appointment_relationship():

    design = add_database_relationships(create_design())

    assert any(
        relationship.from_table == "patients"
        and relationship.to_table == "appointments"
        for relationship in design.relationships
    )


def test_doctor_appointment_relationship():

    design = add_database_relationships(create_design())

    assert any(
        relationship.from_table == "doctors"
        and relationship.to_table == "appointments"
        for relationship in design.relationships
    )


def test_foreign_keys_generated():

    design = add_database_relationships(create_design())

    appointments = next(
        table for table in design.tables
        if table.table_name == "appointments"
    )

    foreign_keys = {
        column.name
        for column in appointments.columns
        if column.foreign_key is not None
    }

    assert "patient_id" in foreign_keys
    assert "doctor_id" in foreign_keys


def test_relationship_generation_no_duplicates():

    design = create_design()

    first = add_database_relationships(design)
    second = add_database_relationships(first)

    assert len(second.relationships) == len(first.relationships)
