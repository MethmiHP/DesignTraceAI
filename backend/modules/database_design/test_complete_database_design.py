"""
DesignTrace AI - Complete Database Design Pipeline Test

Tests:
1. Load a project from the LLM evaluation dataset.
2. Convert it into ProjectInput.
3. Extract concepts using RoBERTa.
4. Generate database design using Gemini.
5. Validate schema and requirement traceability.
6. Generate SQL and Mermaid ER diagram.
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from shared.models.project import (
    ProjectInput,
    Requirement,
    ArchitectureContext,
)

from modules.database_design.design_pipeline import (
    run_complete_database_design,
)


def main():
    print("DesignTrace AI - Complete Database Design Test")
    print("---------------------------------------------")

    dataset_path = (
        BASE_DIR / "datasets" / "llm" / "evaluation_cases.json"
    )

    with dataset_path.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    case = cases[0]

    requirements = [
        Requirement(
            requirement_id=req["requirement_id"],
            requirement_text=req["text"],
            database_relevant=True,
        )
        for req in case["requirements"]
    ]

    raw_architecture = case.get("architecture_context") or {}

    architecture = ArchitectureContext(
        architecture_style=raw_architecture.get(
            "architecture_style"
        ),
        database_type=raw_architecture.get(
            "database_type", "Relational"
        ),
        constraints=raw_architecture.get(
            "constraints", []
        ),
    )

    project = ProjectInput(
        project_id=case["project_id"],
        project_name=case["project_id"],
        project_description="Database design evaluation case.",
        requirements=requirements,
        architecture_context=architecture,
    )

    print("\nProject:", project.project_name)
    print("Requirements:", len(project.requirements))

    result = run_complete_database_design(
        project=project,
        generation_method="gemini",
    )

    print("\nComplete Pipeline Results")
    print("-------------------------")

    print(
        "Schema valid:",
        result["schema_validation"]["valid"],
    )

    print(
        "Mapping valid:",
        result["mapping_validation"]["valid"],
    )

    print(
        "Requirement coverage:",
        f'{result["mapping_validation"]["coverage_percentage"]}%',
    )

    print("Overall valid:", result["overall_valid"])

    print("\nGenerated tables:")
    for table in result["design"]["tables"]:
        print("-", table["table_name"])

    print("\nArtifacts:")
    for name, path in result["artifacts"].items():
        print(f"{name}: {path}")

    if not result["overall_valid"]:
        print("\nValidation errors:")

        for error in result["schema_validation"]["errors"]:
            print("SCHEMA:", error)

        for error in result["mapping_validation"]["errors"]:
            print("MAPPING:", error)

        raise SystemExit(
            "Complete pipeline validation did not pass."
        )

    print("\nComplete database pipeline test successful!")


if __name__ == "__main__":
    main()