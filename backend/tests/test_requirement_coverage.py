"""
DesignTrace AI - Requirement Coverage Tests
===========================================

Purpose:
    Test DB-R06 requirement-to-database mapping coverage.

Tests:
    1. A mapped database requirement should pass.
    2. An unmapped database requirement should fail.
    3. A non-database requirement should not require a mapping.
"""

from shared.models.project import Requirement

from shared.models.database import (
    DatabaseColumn,
    DatabaseTable,
    DatabaseDesign,
)

from modules.database_design.validator import (
    validate_database_design,
)


def create_sample_design():
    """
    Create a small valid database design.

    FR-01 is mapped to the patients table.
    """

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
                        source_requirement_ids=["FR-01"],
                    ),
                ],
                source_requirement_ids=["FR-01"],
            )
        ]
    )


def test_mapped_requirement_passes():
    """DB-R06 should pass when FR-01 is mapped."""

    requirements = [
        Requirement(
            requirement_id="FR-01",
            requirement_text="A patient can register an account.",
            requirement_type="FR",
            database_relevant=True,
        )
    ]

    result = validate_database_design(
        create_sample_design(),
        requirements,
    )

    assert result.passed is True
    assert result.issues == []


def test_unmapped_requirement_fails():
    """DB-R06 should detect an unmapped FR-02."""

    requirements = [
        Requirement(
            requirement_id="FR-01",
            requirement_text="A patient can register an account.",
            requirement_type="FR",
            database_relevant=True,
        ),
        Requirement(
            requirement_id="FR-02",
            requirement_text="A patient can book an appointment.",
            requirement_type="FR",
            database_relevant=True,
        ),
    ]

    result = validate_database_design(
        create_sample_design(),
        requirements,
    )

    assert result.passed is False

    assert any(
        issue.rule_id == "DB-R06"
        and "FR-02" in issue.message
        for issue in result.issues
    )


def test_non_database_requirement_is_ignored():
    """A non-database requirement does not need a DB mapping."""

    requirements = [
        Requirement(
            requirement_id="NFR-01",
            requirement_text="The interface should be responsive.",
            requirement_type="NFR",
            database_relevant=False,
        )
    ]

    result = validate_database_design(
        create_sample_design(),
        requirements,
    )

    assert result.passed is True
    assert not any(
        issue.rule_id == "DB-R06"
        for issue in result.issues
    )
