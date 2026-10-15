
from modules.database_design.requirement_constraint_extractor import (
    extract_requirement_constraints,
)


def test_extract_unique_constraint():
    requirements = [
        "Patient email must be unique."
    ]

    result = extract_requirement_constraints(requirements)

    assert result[0]["type"] == "UNIQUE"
    assert result[0]["column"] == "email"


def test_extract_not_null_constraint():
    requirements = [
        "Every appointment must have a status."
    ]

    result = extract_requirement_constraints(requirements)

    assert result[0]["type"] == "NOT_NULL"
    assert result[0]["column"] == "status"


def test_extract_check_constraint():
    requirements = [
        "Appointment status must be one of pending, confirmed, cancelled."
    ]

    result = extract_requirement_constraints(requirements)

    assert result[0]["type"] == "CHECK"
    assert result[0]["column"] == "status"

    assert result[0]["allowed_values"] == [
        "pending",
        "confirmed",
        "cancelled",
    ]


def test_no_constraint_found():
    requirements = [
        "The system shall display the dashboard."
    ]

    result = extract_requirement_constraints(requirements)

    assert result == []
