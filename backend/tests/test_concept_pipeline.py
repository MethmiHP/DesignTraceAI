"""
Tests for the Database Concept Pipeline.
"""

from shared.models.project import ProjectInput, Requirement

from modules.database_design.concept_pipeline import (
    run_concept_pipeline,
)


def test_concept_pipeline_extracts_project_entities():

    project = ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment system.",
        requirements=[
            Requirement(
                requirement_id="FR-01",
                requirement_text=(
                    "A patient can book an appointment "
                    "with a doctor."
                ),
                database_relevant=True,
            ),
            Requirement(
                requirement_id="FR-02",
                requirement_text=(
                    "The patient must provide an email "
                    "and phone number."
                ),
                database_relevant=True,
            ),
        ],
    )

    result = run_concept_pipeline(project)

    assert result.project_id == "P001"

    assert "patient" in result.candidate_entities
    assert "appointment" in result.candidate_entities
    assert "doctor" in result.candidate_entities

    assert "email" in result.candidate_attributes
    assert "phone" in result.candidate_attributes

    assert "book" in result.candidate_actions

    assert len(result.requirement_concepts) == 2


def test_concept_pipeline_ignores_non_database_requirements():

    project = ProjectInput(
        project_id="P002",
        project_name="Sample System",
        project_description="Sample project.",
        requirements=[
            Requirement(
                requirement_id="NFR-01",
                requirement_text="The system must respond quickly.",
                database_relevant=False,
            ),
        ],
    )

    result = run_concept_pipeline(project)

    assert result.requirement_concepts == []
    assert result.candidate_entities == []
    assert result.candidate_attributes == []
    assert result.candidate_actions == []
