"""
Tests for the rule-based database concept extractor.
"""

from shared.models.project import Requirement

from modules.database_design.concept_extractor import (
    extract_database_concepts,
    extract_project_concepts,
)


def test_extract_entities_and_action():

    requirement = Requirement(
        requirement_id="FR-01",
        requirement_text=(
            "A patient can book an appointment "
            "with a doctor."
        ),
        database_relevant=True,
    )

    result = extract_database_concepts(requirement)

    assert "patient" in result.entities
    assert "appointment" in result.entities
    assert "doctor" in result.entities
    assert "book" in result.actions


def test_extract_attributes():

    requirement = Requirement(
        requirement_id="FR-02",
        requirement_text=(
            "The patient must provide an email "
            "and phone number."
        ),
        database_relevant=True,
    )

    result = extract_database_concepts(requirement)

    assert "patient" in result.entities
    assert "email" in result.attributes
    assert "phone" in result.attributes


def test_plural_entities():

    requirement = Requirement(
        requirement_id="FR-03",
        requirement_text="Doctors can view appointments.",
        database_relevant=True,
    )

    result = extract_database_concepts(requirement)

    assert "doctor" in result.entities
    assert "appointment" in result.entities
    assert "view" in result.actions


def test_non_database_requirement_excluded():

    requirements = [
        Requirement(
            requirement_id="FR-01",
            requirement_text="Patients can book appointments.",
            database_relevant=True,
        ),
        Requirement(
            requirement_id="NFR-01",
            requirement_text="The system must respond quickly.",
            database_relevant=False,
        ),
    ]

    results = extract_project_concepts(requirements)

    assert len(results) == 1
    assert results[0].requirement_id == "FR-01"


def test_empty_requirement():

    requirement = Requirement(
        requirement_id="FR-04",
        requirement_text="",
        database_relevant=True,
    )

    result = extract_database_concepts(requirement)

    assert result.entities == []
    assert result.attributes == []
    assert result.actions == []

def test_book_appointment_is_action_not_entity():
    requirement = Requirement(
        requirement_id="FR-TEST",
        requirement_text=(
            "A patient can book an appointment with a doctor."
        ),
        requirement_type="FR",
        database_relevant=True,
    )

    result = extract_database_concepts(requirement)

    assert "patient" in result.entities
    assert "appointment" in result.entities
    assert "doctor" in result.entities

    assert "book" not in result.entities
    assert "book" in result.actions
