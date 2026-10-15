"""
File: test_requirement_mapper.py

Purpose:
    Test requirement-to-database mapping.

Tests:
    1. A mapped requirement produces database elements.
    2. An unmapped requirement is identified.
    3. A non-database requirement is excluded.
"""

from shared.models.project import Requirement
from shared.models.database import (
    DatabaseDesign,
    DatabaseTable,
    DatabaseColumn,
)
from modules.database_design.requirement_mapper import (
    generate_requirement_mappings,
)


def create_sample_design():
    """Create a simple patient database design."""

    return DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="patients",
                purpose="Stores patient information.",
                source_requirement_ids=["FR-01"],
                columns=[
                    DatabaseColumn(
                        name="patient_id",
                        data_type="BIGINT",
                        nullable=False,
                        primary_key=True,
                        source_requirement_ids=["FR-01"],
                    ),
                ],
            ),
        ],
    )


def make_requirement(req_id, db_relevant=True):
    """Create a requirement for testing."""

    return Requirement(
        requirement_id=req_id,
        requirement_text="Sample requirement.",
        requirement_type="FR" if db_relevant else "NFR",
        database_relevant=db_relevant,
    )


def test_mapped_requirement():
    """FR-01 should map to the patients table."""

    result = generate_requirement_mappings(
        create_sample_design(),
        [make_requirement("FR-01")],
    )

    mapping = result["requirement_mappings"][0]

    assert mapping["mapped"] is True
    assert "patients" in mapping["database_elements"]
    assert "patients.patient_id" not in mapping["database_elements"]


def test_unmapped_requirement():
    """FR-02 should be reported as unmapped."""

    result = generate_requirement_mappings(
        create_sample_design(),
        [make_requirement("FR-02")],
    )

    mapping = result["requirement_mappings"][0]

    assert mapping["mapped"] is False
    assert mapping["database_elements"] == []


def test_non_database_requirement_excluded():
    """A non-database NFR should be ignored."""

    result = generate_requirement_mappings(
        create_sample_design(),
        [make_requirement("NFR-01", db_relevant=False)],
    )

    assert result["requirement_mappings"] == []
