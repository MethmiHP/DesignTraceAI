"""
DesignTrace AI - Database Validation Tests
==========================================

Purpose:
    Automatically test the database validation rules.

Tests:
    1. Valid generated database should pass.
    2. Missing primary key should trigger DB-R01.
    3. Missing foreign-key table should trigger DB-R02.
    4. Invalid relationship should trigger DB-R03.
    5. Unsupported data type should trigger DB-R04.
"""

from shared.models.project import ProjectInput

from shared.models.database import (
    DatabaseColumn,
    DatabaseTable,
    DatabaseDesign,
    ForeignKeyReference,
    DatabaseRelationship,
)

from modules.database_design.database_module import (
    generate_database_design,
)

from modules.database_design.validator import (
    validate_database_design,
)


def test_valid_database_passes():
    """A valid mock database should pass validation."""

    project = ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment system.",
    )

    design = generate_database_design(project)
    result = validate_database_design(design)

    assert result.passed is True
    assert result.issues == []


def test_missing_primary_key():
    """DB-R01 must detect a table without a primary key."""

    design = DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="doctors",
                columns=[
                    DatabaseColumn(
                        name="doctor_name",
                        data_type="VARCHAR(255)",
                    )
                ],
            )
        ]
    )

    result = validate_database_design(design)

    assert result.passed is False
    assert any(
        issue.rule_id == "DB-R01"
        for issue in result.issues
    )


def test_missing_foreign_key_table():
    """DB-R02 must detect a missing referenced table."""

    design = DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="appointments",
                columns=[
                    DatabaseColumn(
                        name="appointment_id",
                        data_type="BIGINT",
                        primary_key=True,
                    ),
                    DatabaseColumn(
                        name="doctor_id",
                        data_type="BIGINT",
                        foreign_key=ForeignKeyReference(
                            table="doctors",
                            column="doctor_id",
                        ),
                    ),
                ],
            )
        ]
    )

    result = validate_database_design(design)

    assert result.passed is False
    assert any(
        issue.rule_id == "DB-R02"
        for issue in result.issues
    )


def test_missing_relationship_table():
    """DB-R03 must detect a relationship using a missing table."""

    design = DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="patients",
                columns=[
                    DatabaseColumn(
                        name="patient_id",
                        data_type="BIGINT",
                        primary_key=True,
                    )
                ],
            )
        ],
        relationships=[
            DatabaseRelationship(
                relationship_id="REL-01",
                from_table="patients",
                to_table="appointments",
                relationship_type="one-to-many",
                foreign_key="appointments.patient_id",
            )
        ],
    )

    result = validate_database_design(design)

    assert result.passed is False
    assert any(
        issue.rule_id == "DB-R03"
        for issue in result.issues
    )


def test_invalid_data_type():
    """DB-R04 must detect an unsupported data type."""

    design = DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="patients",
                columns=[
                    DatabaseColumn(
                        name="patient_id",
                        data_type="BIGINT",
                        primary_key=True,
                    ),
                    DatabaseColumn(
                        name="age",
                        data_type="MAGIC_NUMBER",
                    ),
                ],
            )
        ]
    )

    result = validate_database_design(design)

    assert result.passed is False
    assert any(
        issue.rule_id == "DB-R04"
        for issue in result.issues
    )