"""
Tests for DB-R07: Empty Database Design Validation.
"""

from shared.models.database import DatabaseDesign

from modules.database_design.database_validator import (
    validate_database_design,
)


def test_empty_database_design_fails():
    design = DatabaseDesign(
        tables=[],
        relationships=[],
        constraints=[],
    )

    report = validate_database_design(design)

    results = [
        result
        for result in report["results"]
        if result["rule_id"] == "DB-R07"
    ]

    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert report["status"] == "FAIL"
