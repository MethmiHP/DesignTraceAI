import json
import sys
from pathlib import Path


# -----------------------------------------
# Project path configuration
# -----------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))


# -----------------------------------------
# Imports
# -----------------------------------------

from shared.llm.gemini_generator import (
    generate_database_design,
    save_database_design,
)

from modules.database_design.requirement_mapping_validator import (
    validate_requirement_mapping,
)


# -----------------------------------------
# Main test
# -----------------------------------------

def main():
    print("DesignTrace AI - Gemini API Test")
    print("--------------------------------")

    dataset_path = (
        BASE_DIR / "datasets" / "llm" / "evaluation_cases.json"
    )

    with dataset_path.open(
        "r",
        encoding="utf-8"
    ) as file:
        cases = json.load(file)

    # Select the first evaluation case
    case = cases[0]

    print("Testing case:", case["case_id"])
    print("Project:", case["project_id"])

    # -------------------------------------
    # Step 1: Generate database design
    # -------------------------------------

    design = generate_database_design(
        requirements=case["requirements"],
        project_name=case["project_id"],
        architecture_context=case.get(
            "architecture_context", {}
        ),
    )

    # -------------------------------------
    # Step 2: Save generated database
    # -------------------------------------

    output_path = save_database_design(
        design,
        f"{case['case_id']}_gemini.json"
    )

    print("\nGenerated tables:")

    for table in design["tables"]:
        print("-", table["name"])

    print(
        "\nRelationships:",
        len(design["relationships"])
    )

    print(
        "Requirement mappings:",
        len(design["requirement_mapping"])
    )

    print("\nSaved to:", output_path)
    print("\nGemini API integration successful!")

    # -------------------------------------
    # Step 3: Validate requirement mappings
    # -------------------------------------

    mapping_result = validate_requirement_mapping(
        requirements=case["requirements"],
        design=design,
    )

    print("\nRequirement Mapping Validation")
    print("--------------------------------")

    print("Valid:", mapping_result["valid"])

    print(
        "Coverage:",
        f"{mapping_result['coverage_percentage']}%"
    )

    print(
        "Mapped requirements:",
        f"{mapping_result['mapped_requirements']}/"
        f"{mapping_result['total_requirements']}"
    )

    print("\nErrors:")

    if mapping_result["errors"]:
        for error in mapping_result["errors"]:
            print("ERROR:", error)
    else:
        print("No mapping errors.")

    print("\nWarnings:")

    if mapping_result["warnings"]:
        for warning in mapping_result["warnings"]:
            print("WARNING:", warning)
    else:
        print("No warnings.")


if __name__ == "__main__":
    main()
