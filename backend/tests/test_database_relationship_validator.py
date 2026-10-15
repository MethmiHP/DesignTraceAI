"""
Tests for DB-R03 Relationship Validation.
"""

from shared.models.database import (
    DatabaseDesign,
    DatabaseTable,
    DatabaseColumn,
    DatabaseRelationship,
)

from modules.database_design.database_validator import (
    validate_database_design,
)


def create_design(
    from_table="patients",
    to_table="appointments",
    relationship_type="one-to-many",
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
                ],
            ),
        ],
        relationships=[
            DatabaseRelationship(
                relationship_id="REL-01",
                from_table=from_table,
                to_table=to_table,
                relationship_type=relationship_type,
            ),
        ],
    )

def get_relationship_results(report):
    return [
        result
        for result in report["results"]
        if result["rule_id"] == "DB-R03"
    ]


def test_valid_relationship_passes():
    design = create_design()

    report = validate_database_design(design)

    results = get_relationship_results(report)

    assert len(results) == 1
    assert results[0]["status"] == "PASS"
    assert report["status"] == "PASS"


def test_missing_source_table_fails():
    design = create_design(
        from_table="unknown_patients"
    )

    report = validate_database_design(design)

    results = get_relationship_results(report)

    assert results[0]["status"] == "FAIL"
    assert report["status"] == "FAIL"


def test_missing_target_table_fails():
    design = create_design(
        to_table="unknown_appointments"
    )

    report = validate_database_design(design)

    results = get_relationship_results(report)

    assert results[0]["status"] == "FAIL"
    assert report["status"] == "FAIL"


def test_invalid_relationship_type_fails():
    design = create_design(
        relationship_type="invalid-type"
    )

    report = validate_database_design(design)

    results = get_relationship_results(report)

    assert results[0]["status"] == "FAIL"
    assert report["status"] == "FAIL"


def test_multiple_relationships_validated():
    design = create_design()

    design.relationships.append(
        DatabaseRelationship(
            relationship_id="REL-02",
            from_table="patients",
            to_table="missing_table",
            relationship_type="one-to-many",
        )
    )

    report = validate_database_design(design)

    results = get_relationship_results(report)

    assert len(results) == 2

    assert sum(
        result["status"] == "PASS"
        for result in results
    ) == 1

    assert sum(
        result["status"] == "FAIL"
        for result in results
    ) == 1

    assert report["status"] == "FAIL"
