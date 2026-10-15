"""
DesignTrace AI - Artifact Adapter Test

Tests:
Standard DatabaseDesign
    -> Artifact Adapter
    -> SQL and Mermaid files
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from shared.models.database import DatabaseDesign

from modules.database_design.artifact_adapter import (
    convert_design_for_artifacts,
)

from modules.database_design.artifact_generator import (
    save_artifacts,
)


def main():
    print("DesignTrace AI - Artifact Adapter Test")
    print("--------------------------------------")

    input_path = (
        BASE_DIR
        / "outputs"
        / "database_designs"
        / "LLM-001_standardized.json"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Standardized database design not found: {input_path}"
        )

    design = DatabaseDesign.model_validate_json(
        input_path.read_text(encoding="utf-8")
    )

    artifact_design = convert_design_for_artifacts(
        design
    )

    print("\nConverted tables:")
    for table in artifact_design["tables"]:
        print("-", table["name"])

    output_dir = (
        BASE_DIR
        / "outputs"
        / "database_designs"
        / "artifacts"
    )

    paths = save_artifacts(
        design=artifact_design,
        output_dir=output_dir,
        base_name="LLM-001_integrated",
    )

    print("\nGenerated artifacts:")
    print("SQL:", paths["sql_file"])
    print("ER diagram:", paths["er_diagram_file"])

    print("\nArtifact adapter test successful!")


if __name__ == "__main__":
    main()
