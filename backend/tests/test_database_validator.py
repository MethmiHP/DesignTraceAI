"""
Tests for Database Design Validation.

DB-R01: Primary Key Validation.
"""

from shared.models.database import (
    DatabaseDesign,
    DatabaseTable,
    DatabaseColumn,
)

from modules.database_design.database_validator import (
    validate_database_design,
)


def test_table_with_primary_key_passes():

    design = DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="patients",
                columns=[
                    DatabaseColumn(
                        name="patient_id",
                        data_type="BIGINT",
                        primary_key=True,
                        nullable=False,
                    ),
                    DatabaseColumn(
                        name="email",
                        data_type="VARCHAR(255)",
                    ),
                ],
            )
        ]
    )

    report = validate_database_design(design)

    assert report["status"] == "PASS"
    assert report["total_checks"] == 5
    assert report["passed_checks"] == 5
    assert report["failed_checks"] == 0


def test_table_without_primary_key_fails():

    design = DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="patients",
                columns=[
                    DatabaseColumn(
                        name="email",
                        data_type="VARCHAR(255)",
                    )
                ],
            )
        ]
    )

    report = validate_database_design(design)

    assert report["status"] == "FAIL"
    assert report["failed_checks"] == 1

    assert any(
    result["rule_id"] == "DB-R01"
    and result["status"] == "FAIL"
    for result in report["results"]
    )


def test_multiple_tables_validated():

    design = DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="patients",
                columns=[
                    DatabaseColumn(
                        name="patient_id",
                        data_type="BIGINT",
                        primary_key=True,
                        nullable=False,
                    )
                ],
            ),
            DatabaseTable(
                table_name="appointments",
                columns=[
                    DatabaseColumn(
                        name="status",
                        data_type="VARCHAR(255)",
                    )
                ],
            ),
        ]
    )

    report = validate_database_design(design)

    assert report["total_checks"] == 6
    assert report["passed_checks"] == 5
    assert report["failed_checks"] == 1
    assert report["status"] == "FAIL"
