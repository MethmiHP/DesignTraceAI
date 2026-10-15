"""
Tests for DB-R04 Data Type Validation.
"""

import pytest

from shared.models.database import (
    DatabaseDesign,
    DatabaseTable,
    DatabaseColumn,
)

from modules.database_design.database_validator import (
    validate_database_design,
)


def create_design(data_type):
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
                    DatabaseColumn(
                        name="email",
                        data_type=data_type,
                    ),
                ],
            ),
        ],
    )


def get_type_result(report):
    return next(
        result
        for result in report["results"]
        if (
            result["rule_id"] == "DB-R04"
            and result["column"] == "email"
        )
    )


@pytest.mark.parametrize(
    "data_type",
    [
        "BIGINT",
        "INTEGER",
        "VARCHAR(255)",
        "DECIMAL(10,2)",
        "DATE",
        "TIMESTAMP",
    ],
)
def test_supported_data_types_pass(data_type):
    report = validate_database_design(
        create_design(data_type)
    )

    assert get_type_result(report)["status"] == "PASS"
    assert report["status"] == "PASS"


@pytest.mark.parametrize(
    "data_type",
    [
        "UNKNOWN",
        "VARCHAR(0)",
        "DECIMAL()",
        "",
    ],
)
def test_invalid_data_types_fail(data_type):
    report = validate_database_design(
        create_design(data_type)
    )

    assert get_type_result(report)["status"] == "FAIL"
    assert report["status"] == "FAIL"


def test_all_columns_are_checked():
    report = validate_database_design(
        create_design("VARCHAR(255)")
    )

    results = [
        result
        for result in report["results"]
        if result["rule_id"] == "DB-R04"
    ]

    assert len(results) == 2
    assert all(
        result["status"] == "PASS"
        for result in results
    )
