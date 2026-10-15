"""
DesignTrace AI - RoBERTa Concept Pipeline Test
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from shared.models.project import (
    ProjectInput,
    Requirement,
)

from modules.database_design.concept_pipeline import (
    run_concept_pipeline,
)


def main():

    project = ProjectInput(
        project_id="TEST-001",
        project_name="Hospital Management",
        project_description="Hospital appointment system",
        requirements=[
            Requirement(
                requirement_id="FR-001",
                requirement_text=(
                    "The system shall store patient "
                    "name, email address and phone number."
                ),
                database_relevant=True,
            ),
            Requirement(
                requirement_id="FR-002",
                requirement_text=(
                    "Patients can book appointments "
                    "with doctors."
                ),
                database_relevant=True,
            ),
        ],
    )

    result = run_concept_pipeline(
        project,
        method="roberta",
    )

    print("\nDesignTrace AI - RoBERTa Concept Test")
    print("-----------------------------------")

    print("\nEntities:")
    for entity in result.candidate_entities:
        print("-", entity)

    print("\nAttributes:")
    for attribute in result.candidate_attributes:
        print("-", attribute)

    print("\nActions:")
    for action in result.candidate_actions:
        print("-", action)

    print("\nRoBERTa concept pipeline test completed!")


if __name__ == "__main__":
    main()
