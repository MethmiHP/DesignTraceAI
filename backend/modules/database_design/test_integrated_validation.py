"""
DesignTrace AI - Integrated Database Validation Test

Tests:
1. Load a standardized database design
2. Convert it to the artifact-compatible format
3. Validate database structure
4. Generate SQL and Mermaid ER diagram if valid

No Gemini API call is required.
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from shared.models.database import DatabaseDesign

from modules.database_design.artifact_adapter import (
    convert_design_for_artifacts,
)

from modules.database_design.schema_validator import (
    validate_database_design,
)

from modules.database_design.artifact_generator import (
    save_artifacts,
)


def main():
    print("DesignTrace AI - Integrated Validation Test")
    print("-------------------------------------------")

    input_path = (
        BASE_DIR
        / "outputs"
        / "database_designs"
        / "LLM-001_standardized.json"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Database design not found: {input_path}"
        )

    # Step 1: Load the standard DatabaseDesign model.
    design = DatabaseDesign.model_validate_json(
        input_path.read_text(encoding="utf-8")
    )

    # Step 2: Convert into the format expected
    # by the existing validator and artifact generator.
    artifact_design = convert_design_for_artifacts(
        design
    )

    # Step 3: Validate the relational schema.
    print("\nValidating database schema...")

    validation_result = validate_database_design(
        artifact_design
    )

    print("Valid:", validation_result["valid"])
    print("Statistics:", validation_result["statistics"])

    for error in validation_result["errors"]:
        print("ERROR:", error)

    for warning in validation_result["warnings"]:
        print("WARNING:", warning)

    # Step 4: Stop if structural validation fails.
    if not validation_result["valid"]:
        print("\nArtifact generation stopped.")
        print("Fix the schema errors first.")
        return

    # Step 5: Generate artifacts only after validation.
    print("\nGenerating database artifacts...")

    output_dir = (
        BASE_DIR
        / "outputs"
        / "database_designs"
        / "artifacts"
    )

    artifact_paths = save_artifacts(
        design=artifact_design,
        output_dir=output_dir,
        base_name="LLM-001_validated",
    )

    print("\nGenerated artifacts:")
    print("SQL:", artifact_paths["sql_file"])
    print(
        "ER diagram:",
        artifact_paths["er_diagram_file"],
    )

    # Step 6: Save validation report.
    report_path = (
        output_dir / "LLM-001_validation_report.json"
    )

    report_path.write_text(
        json.dumps(
            validation_result,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Validation report:", report_path)

    print("\nIntegrated validation test successful!")


if __name__ == "__main__":
    main()
