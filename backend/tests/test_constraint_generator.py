from copy import deepcopy

from modules.database_design.database_module import (
    generate_database_design,
)
from modules.database_design.constraint_generator import (
    generate_database_constraints,
)
from shared.models.project import ProjectInput


def create_project():
    return ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment system.",
        requirements=[],
    )


def test_primary_key_not_nullable():
    design = generate_database_design(create_project())
    result = generate_database_constraints(design)

    for table in result.tables:
        for column in table.columns:
            if column.primary_key:
                assert column.nullable is False


def test_email_unique():
    design = generate_database_design(create_project())
    result = generate_database_constraints(design)

    patients = next(
        table for table in result.tables
        if table.table_name == "patients"
    )

    email = next(
        column for column in patients.columns
        if column.name == "email"
    )

    assert email.unique is True


def test_constraint_generation_idempotent():
    design = generate_database_design(create_project())

    first = generate_database_constraints(
        deepcopy(design)
    )
    second = generate_database_constraints(
        deepcopy(first)
    )

    assert first == second
