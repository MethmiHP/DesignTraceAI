"""
Tests for DB-R02 Foreign Key Validation.
"""

from shared.models.database import (
    DatabaseDesign,
    DatabaseTable,
    DatabaseColumn,
    ForeignKeyReference,
)

from modules.database_design.database_validator import (
    validate_database_design,
)


def create_design(
    referenced_table="patients",
    referenced_column="patient_id",
):

    return DatabaseDesign(
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
                ],
            ),
            DatabaseTable(
                table_name="appointments",
                columns=[
                    DatabaseColumn(
                        name="appointment_id",
                        data_type="BIGINT",
                        primary_key=True,
                        nullable=False,
                    ),
                    DatabaseColumn(
                        name="patient_id",
                        data_type="BIGINT",
                        foreign_key=ForeignKeyReference(
                            table=referenced_table,
                            column=referenced_column,
                        ),
                    ),
                ],
            ),
        ],
    )


def get_fk_results(report):
    return [
        result
        for result in report["results"]
        if result["rule_id"] == "DB-R02"
    ]


def test_valid_foreign_key_passes():

    design = create_design()

    report = validate_database_design(design)

    fk_results = get_fk_results(report)

    assert len(fk_results) == 1
    assert fk_results[0]["status"] == "PASS"
    assert report["status"] == "PASS"


def test_missing_referenced_table_fails():

    design = create_design(
        referenced_table="unknown_patients"
    )

    report = validate_database_design(design)

    fk_results = get_fk_results(report)

    assert len(fk_results) == 1
    assert fk_results[0]["status"] == "FAIL"
    assert report["status"] == "FAIL"


def test_missing_referenced_column_fails():

    design = create_design(
        referenced_column="unknown_id"
    )

    report = validate_database_design(design)

    fk_results = get_fk_results(report)

    assert len(fk_results) == 1
    assert fk_results[0]["status"] == "FAIL"
    assert report["status"] == "FAIL"


def test_multiple_foreign_keys_validated():

    design = create_design()

    appointments = next(
        table
        for table in design.tables
        if table.table_name == "appointments"
    )

    appointments.columns.append(
        DatabaseColumn(
            name="unknown_id",
            data_type="BIGINT",
            foreign_key=ForeignKeyReference(
                table="missing_table",
                column="id",
            ),
        )
    )

    report = validate_database_design(design)

    fk_results = get_fk_results(report)

    assert len(fk_results) == 2

    assert sum(
        result["status"] == "PASS"
        for result in fk_results
    ) == 1

    assert sum(
        result["status"] == "FAIL"
        for result in fk_results
    ) == 1

    assert report["status"] == "FAIL"
