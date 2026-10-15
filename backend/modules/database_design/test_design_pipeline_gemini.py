"""
DesignTrace AI - Gemini Pipeline Integration Test

Tests:
ProjectInput -> Gemini -> Adapter -> DatabaseDesign
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from shared.models.project import (
    ProjectInput,
    Requirement,
    ArchitectureContext,
)

from shared.models.database import DatabaseDesign

from modules.database_design.design_pipeline import (
    generate_database_design_pipeline,
)


def main():
    print("DesignTrace AI - Gemini Pipeline Test")
    print("-------------------------------------")

    project = ProjectInput(
        project_id="hospital_management",
        project_name="Hospital Management System",
        project_description=(
            "A system for managing patients, doctors, "
            "and medical appointments."
        ),
        requirements=[
            Requirement(
                requirement_id="FR-001",
                requirement_text=(
                    "The system shall register patients "
                    "with their full name, email address, "
                    "and phone number."
                ),
                requirement_type="FR",
                database_relevant=True,
            ),
            Requirement(
                requirement_id="FR-002",
                requirement_text=(
                    "The system shall store doctor names "
                    "and specializations."
                ),
                requirement_type="FR",
                database_relevant=True,
            ),
            Requirement(
                requirement_id="FR-003",
                requirement_text=(
                    "Patients shall book appointments "
                    "with doctors at a selected date "
                    "and time."
                ),
                requirement_type="FR",
                database_relevant=True,
            ),
        ],
        architecture_context=ArchitectureContext(
            architecture_style="Layered Architecture",
            database_type="Relational",
            constraints=[
                "Use PostgreSQL-compatible data types.",
                "Every table must have a primary key.",
                "Use foreign keys for relationships.",
            ],
        ),
    )

    design = generate_database_design_pipeline(
        project=project,
        generation_method="gemini",
    )

    assert isinstance(design, DatabaseDesign)

    print("\nGenerated tables:")

    for table in design.tables:
        print("-", table.table_name)

    print(
        "\nRelationships:",
        len(design.relationships)
    )

    print(
        "Constraints:",
        len(design.constraints)
    )

    print("\nGemini pipeline integration successful!")


if __name__ == "__main__":
    main()
