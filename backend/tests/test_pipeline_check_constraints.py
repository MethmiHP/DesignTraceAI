"""
Test CHECK constraint integration in the
Database Design Pipeline.
"""

from shared.models.project import ProjectInput, Requirement

from modules.database_design.design_pipeline import (
    generate_database_design_pipeline,
)

from modules.database_design.requirement_constraint_applier import (
    apply_requirement_constraints,
)


def create_project():
    return ProjectInput(
        project_id="P003",
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
            Requirement(
                requirement_id="FR-05",
                requirement_text=(
                    "Appointment status must be one of "
                    "pending, confirmed, cancelled."
                ),
                database_relevant=True,
            ),
        ],
    )


def test_pipeline_generates_status_column():
    design = generate_database_design_pipeline(
        create_project()
    )

    appointments = next(
        table
        for table in design.tables
        if table.table_name == "appointments"
    )

    assert any(
        column.name == "status"
        for column in appointments.columns
    )


def test_pipeline_generates_check_constraint():
    design = generate_database_design_pipeline(
        create_project()
    )

    expected = (
        "CHECK (status IN "
        "('pending', 'confirmed', 'cancelled'))"
    )

    assert expected in design.constraints


def test_check_constraint_not_duplicated():
    design = generate_database_design_pipeline(
        create_project()
    )

    mapped_constraint = {
        "type": "CHECK",
        "table": "appointments",
        "column": "status",
        "allowed_values": [
            "pending",
            "confirmed",
            "cancelled",
        ],
        "status": "MAPPED",
    }

    apply_requirement_constraints(
        design,
        [mapped_constraint],
    )

    expected = (
        "CHECK (status IN "
        "('pending', 'confirmed', 'cancelled'))"
    )

    assert design.constraints.count(expected) == 1
