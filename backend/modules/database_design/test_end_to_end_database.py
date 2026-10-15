"""
DesignTrace AI - End-to-End Database Design Test

Tests:
1. Load project requirements
2. Load existing Gemini-generated schema
3. Validate requirement mappings
4. Convert to standard DatabaseDesign
5. Validate database structure
6. Generate SQL and ER diagram
7. Save combined validation report

No Gemini API call is required.
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from modules.database_design.gemini_adapter import (
    convert_gemini_design,
)

from modules.database_design.artifact_adapter import (
    convert_design_for_artifacts,
)

from modules.database_design.schema_validator import (
    validate_database_design,
)

from modules.database_design.requirement_mapping_validator import (
    validate_requirement_mapping,
)

from modules.database_design.artifact_generator import (
    save_artifacts,
)


def main():
    print("DesignTrace AI - End-to-End Database Test")
    print("-----------------------------------------")

    # Step 1: Load evaluation requirements.
    dataset_path = (
        BASE_DIR
        / "datasets"
        / "llm"
        / "evaluation_cases.json"
    )

    with dataset_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        cases = json.load(file)

    case = cases[0]
    case_id = case["case_id"]
    requirements = case["requirements"]

    print("\nProject:", case["project_id"])
    print("Case:", case_id)

    # Step 2: Load existing Gemini output.
    gemini_path = (
        BASE_DIR
        / "outputs"
        / "database_designs"
        / f"{case_id}_gemini.json"
    )

    with gemini_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        gemini_design = json.load(file)

    # Step 3: Validate requirement mappings.
    print("\nValidating requirement mappings...")

    mapping_result = validate_requirement_mapping(
        requirements=requirements,
        design=gemini_design,
    )

    print("Mapping valid:", mapping_result["valid"])
    print(
        "Coverage:",
        f"{mapping_result['coverage_percentage']}%",
    )
    print(
        "Mapped requirements:",
        f"{mapping_result['mapped_requirements']}/"
        f"{mapping_result['total_requirements']}",
    )

    for error in mapping_result["errors"]:
        print("MAPPING ERROR:", error)

    for warning in mapping_result["warnings"]:
        print("MAPPING WARNING:", warning)

    # Step 4: Convert to the standard DatabaseDesign.
    print("\nConverting Gemini design...")

    standard_design = convert_gemini_design(
        gemini_design
    )

    artifact_design = convert_design_for_artifacts(
        standard_design
    )

    # Preserve mappings for the structural validator.
    artifact_design["requirement_mapping"] = (
        gemini_design.get("requirement_mapping", [])
    )

    # Step 5: Validate database structure.
    print("\nValidating database structure...")

    schema_result = validate_database_design(
        artifact_design
    )

    print("Schema valid:", schema_result["valid"])
    print("Statistics:", schema_result["statistics"])

    for error in schema_result["errors"]:
        print("SCHEMA ERROR:", error)

    for warning in schema_result["warnings"]:
        print("SCHEMA WARNING:", warning)

    # Step 6: Build combined validation result.
    # Coverage below 100% is treated as incomplete,
    # even if the mapping validator has no errors.
    mapping_complete = (
        mapping_result["coverage_percentage"] == 100.0
    )

    overall_valid = (
        schema_result["valid"]
        and mapping_result["valid"]
        and mapping_complete
    )

    report = {
        "case_id": case_id,
        "project_id": case["project_id"],
        "overall_valid": overall_valid,
        "schema_validation": schema_result,
        "requirement_mapping_validation": mapping_result,
    }

    output_dir = (
        BASE_DIR
        / "outputs"
        / "database_designs"
        / "artifacts"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = (
        output_dir
        / f"{case_id}_end_to_end_report.json"
    )

    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\nOverall validation:", overall_valid)
    print("Validation report:", report_path)

    # Step 7: Generate artifacts only if valid.
    if not overall_valid:
        print(
            "\nValidation failed or mapping is incomplete."
        )
        print("Artifact generation stopped.")
        return

    print("\nGenerating SQL and ER diagram...")

    artifact_paths = save_artifacts(
        design=artifact_design,
        output_dir=output_dir,
        base_name=f"{case_id}_end_to_end",
    )

    print("\nGenerated artifacts:")
    print("SQL:", artifact_paths["sql_file"])
    print(
        "ER diagram:",
        artifact_paths["er_diagram_file"],
    )

    print("\nEnd-to-end integration test successful!")


if __name__ == "__main__":
    main()
