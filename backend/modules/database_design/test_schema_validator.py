import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from modules.database_design.schema_validator import (
    validate_database_design,
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

    result = validate_database_design(design)

    print("\nDesignTrace AI - Schema Validation")
    print("----------------------------------")
    print("Valid:", result["valid"])
    print("Statistics:", result["statistics"])

    print("\nErrors:")
    if result["errors"]:
        for error in result["errors"]:
            print("-", error)
    else:
        print("No structural errors found.")

    print("\nWarnings:")
    if result["warnings"]:
        for warning in result["warnings"]:
            print("-", warning)
    else:
        print("No warnings.")


if __name__ == "__main__":
    main()
