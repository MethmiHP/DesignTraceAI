"""
Tests for feedback-aware database regeneration.
"""

import pytest

from shared.models.project import ProjectInput
from modules.database_design.database_module import (
    generate_database_design,
)


@pytest.fixture
def project():
    return ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment system.",
    )


def test_initial_database_design(project):
    design = generate_database_design(project)

    table_names = {
        table.table_name
        for table in design.tables
    }

    assert "patients" in table_names
    assert "appointments" in table_names
    assert "doctors" not in table_names


def test_feedback_adds_doctors_table(project):
    initial = generate_database_design(project)

    revised = generate_database_design(
        project,
        previous_design=initial,
        human_feedback=["Add a doctors table."],
    )

    table_names = {
        table.table_name
        for table in revised.tables
    }

    assert "doctors" in table_names

    # Previous design must remain unchanged.
    assert "doctors" not in {
        table.table_name
        for table in initial.tables
    }


def test_feedback_links_doctors_to_appointments(project):
    initial = generate_database_design(project)

    revised = generate_database_design(
        project,
        previous_design=initial,
        human_feedback=[
            "Add a doctors table and link doctors "
            "to appointments."
        ],
    )

    appointments = next(
        table
        for table in revised.tables
        if table.table_name == "appointments"
    )

    doctor_column = next(
        column
        for column in appointments.columns
        if column.name == "doctor_id"
    )

    assert doctor_column.foreign_key.table == "doctors"

    assert any(
        relationship.foreign_key
        == "appointments.doctor_id"
        for relationship in revised.relationships
    )


def test_repeated_feedback_does_not_duplicate_tables(project):
    initial = generate_database_design(project)

    revised = generate_database_design(
        project,
        previous_design=initial,
        human_feedback=["Add a doctors table."],
    )

    revised_again = generate_database_design(
        project,
        previous_design=revised,
        human_feedback=["Add a doctors table."],
    )

    assert sum(
        table.table_name == "doctors"
        for table in revised_again.tables
    ) == 1


def test_unsupported_feedback_is_rejected(project):
    initial = generate_database_design(project)

    with pytest.raises(
        ValueError,
        match="Unsupported database feedback",
    ):
        generate_database_design(
            project,
            previous_design=initial,
            human_feedback=[
                "Change the database to MongoDB."
            ],
        )
