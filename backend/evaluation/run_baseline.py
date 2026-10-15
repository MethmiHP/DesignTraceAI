"""
DesignTrace AI - Baseline Evaluation Runner
===========================================

Runs the deterministic Database Design Module
on three sample projects and saves the outputs.

Generated files:
    1. database_design.json
    2. validation_report.json
    3. er_diagram.mmd
    4. requirement_mapping.json
    5. schema.sql (only when validation passes)
    6. baseline_summary.json

Run from the backend folder:
    python -m evaluation.run_baseline
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from shared.models.project import ProjectInput

from modules.database_design.design_pipeline import (
    generate_database_design_pipeline,
)
from modules.database_design.database_validator import (
    validate_database_design,
)
from modules.database_design.sql_generator import (
    generate_sql_schema,
)
from modules.database_design.er_diagram import (
    generate_er_diagram,
)
from modules.database_design.requirement_mapper import (
    generate_requirement_mappings,
)


# --------------------------------------------------
# Evaluation directories
# --------------------------------------------------

EVALUATION_DIR = Path(__file__).resolve().parent

INPUT_DIR = EVALUATION_DIR / "sample_projects"

OUTPUT_DIR = EVALUATION_DIR / "baseline_results"

PROJECTS = [
    "hospital",
    "library",
    "ecommerce",
    "student",
]


# --------------------------------------------------
# Helper: Save JSON files
# --------------------------------------------------

def save_json(path: Path, data):
    """Save data to a formatted JSON file."""

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# --------------------------------------------------
# Run baseline for one project
# --------------------------------------------------

def run_project(project_name: str):

    print(f"\nRunning baseline: {project_name}")

    input_path = INPUT_DIR / f"{project_name}.json"

    output_path = OUTPUT_DIR / project_name

    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Step 1: Load and validate project input.

    project = ProjectInput.model_validate_json(
        input_path.read_text(
            encoding="utf-8"
        )
    )

    # Step 2: Generate database design.
    # No human feedback is used in the baseline.

    design = generate_database_design_pipeline(
        project,
        feedback=None,
    )

    # Step 3: Save database design JSON.

    save_json(
        output_path / "database_design.json",
        design.model_dump(mode="json"),
    )

    # Step 4: Validate database design.

    report = validate_database_design(design)

    save_json(
        output_path / "validation_report.json",
        report,
    )

    # Step 5: Generate and save ER diagram.

    er_diagram = generate_er_diagram(design)

    (output_path / "er_diagram.mmd").write_text(
        er_diagram,
        encoding="utf-8",
    )

    # Step 6: Generate requirement-to-database mappings.

    mapping_report = generate_requirement_mappings(
        design=design,
        requirements=project.requirements,
    )

    save_json(
        output_path / "requirement_mapping.json",
        mapping_report,
    )

    # Step 7: Calculate requirement mapping coverage.

    mappings = mapping_report["requirement_mappings"]

    total_requirements = len(mappings)

    mapped_requirements = sum(
        1
        for mapping in mappings
        if mapping["mapped"]
    )

    unmapped_requirements = (
        total_requirements - mapped_requirements
    )

    if total_requirements > 0:
        mapping_coverage = round(
            (
                mapped_requirements
                / total_requirements
            ) * 100,
            2,
        )
    else:
        mapping_coverage = 0.0

    # Step 8: Generate SQL only when validation passes.

    sql_status = "NOT_GENERATED"

    sql_path = output_path / "schema.sql"

    # Remove SQL from an earlier run to avoid stale results.
    if sql_path.exists():
        sql_path.unlink()

    if report["status"] == "PASS":

        try:
            sql = generate_sql_schema(design)

            sql_path.write_text(
                sql,
                encoding="utf-8",
            )

            sql_status = "GENERATED"

        except ValueError as error:
            sql_status = f"ERROR: {error}"

    # Step 9: Create baseline summary.

    summary = {
        "project_id": project.project_id,
        "project_name": project.project_name,
        "baseline_type": "deterministic_prototype",
        "human_feedback": False,
        "run_timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        # Database design results
        "tables_generated": len(design.tables),
        "relationships_generated": len(
            design.relationships
        ),

        # Validation results
        "validation_status": report["status"],
        "total_checks": report["total_checks"],
        "passed_checks": report["passed_checks"],
        "failed_checks": report["failed_checks"],

        # SQL generation result
        "sql_status": sql_status,

        # Requirement mapping results
        "total_database_requirements": total_requirements,
        "mapped_requirements": mapped_requirements,
        "unmapped_requirements": unmapped_requirements,
        "mapping_coverage_percent": mapping_coverage,
    }

    # Step 10: Save baseline summary.

    save_json(
        output_path / "baseline_summary.json",
        summary,
    )

    # Step 11: Print results.

    print("Validation:", report["status"])

    print("Tables:", len(design.tables))

    print(
        "Relationships:",
        len(design.relationships),
    )

    print("SQL:", sql_status)

    print(
        "Requirement Mapping:",
        f"{mapped_requirements}/{total_requirements}",
    )

    print(
        "Unmapped Requirements:",
        unmapped_requirements,
    )

    print(
        "Mapping Coverage:",
        f"{mapping_coverage}%",
    )

    print("Saved to:", output_path)


# --------------------------------------------------
# Run all sample projects
# --------------------------------------------------

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for project_name in PROJECTS:
        run_project(project_name)

    print("\nBaseline evaluation completed.")


if __name__ == "__main__":
    main()
