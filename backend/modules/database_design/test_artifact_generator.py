import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from modules.database_design.schema_validator import (
    validate_database_design,
)

from modules.database_design.artifact_generator import (
    save_artifacts,
)


def main():
    design_path = (
        BASE_DIR
        / "outputs"
        / "database_designs"
        / "LLM-001_gemini.json"
    )

    with design_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        design = json.load(file)

    validation = validate_database_design(design)

    if not validation["valid"]:
        print("Schema validation failed.")
        for error in validation["errors"]:
            print("-", error)
        return

    output_dir = (
        BASE_DIR
        / "outputs"
        / "database_designs"
        / "artifacts"
    )

    paths = save_artifacts(
        design=design,
        output_dir=output_dir,
        base_name="LLM-001",
    )

    print("DesignTrace AI - Artifact Generation")
    print("------------------------------------")
    print("Schema validation: PASSED")
    print("SQL file:", paths["sql_file"])
    print("ER diagram:", paths["er_diagram_file"])
    print("\nArtifact generation successful!")


if __name__ == "__main__":
    main()
