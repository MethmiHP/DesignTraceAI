from shared.models.database import (
    DatabaseDesign,
    DatabaseTable,
    DatabaseColumn,
)

from modules.database_design.database_validator import (
    validate_database_design,
)


def get_r05_results(design):
    report = validate_database_design(design)

    return [
        result
        for result in report["results"]
        if result["rule_id"] == "DB-R05"
    ]


def test_primary_key_not_null_passes():
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
            )
        ]
    )

    results = get_r05_results(design)

    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_nullable_primary_key_fails():
    design = DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="patients",
                columns=[
                    DatabaseColumn(
                        name="patient_id",
                        data_type="BIGINT",
                        primary_key=True,
                        nullable=True,
                    )
                ],
            )
        ]
    )

    results = get_r05_results(design)

    assert len(results) == 1
    assert results[0]["status"] == "FAIL"


def test_valid_check_constraint_passes():
    design = DatabaseDesign(
        tables=[
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
                        name="status",
                        data_type="VARCHAR(255)",
                    ),
                ],
            )
        ],
        constraints=[
            "CHECK (status IN ('pending', 'confirmed'))"
        ],
    )

    results = get_r05_results(design)

    assert len(results) == 2
    assert all(
        result["status"] == "PASS"
        for result in results
    )


def test_check_missing_column_fails():
    design = DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="appointments",
                columns=[
                    DatabaseColumn(
                        name="appointment_id",
                        data_type="BIGINT",
                        primary_key=True,
                        nullable=False,
                    )
                ],
            )
        ],
        constraints=[
            "CHECK (status IN ('pending', 'confirmed'))"
        ],
    )

    results = get_r05_results(design)

    assert any(
        result["status"] == "FAIL"
        for result in results
    )
