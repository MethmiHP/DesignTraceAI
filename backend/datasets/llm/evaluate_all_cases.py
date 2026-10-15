"""
DesignTrace AI - Evaluate All LLM Cases
======================================

Evaluates the RoBERTa + Gemini Database Design Module
on every case in datasets/llm/evaluation_cases.json.

For each case:
1. Build ProjectInput.
2. Run RoBERTa + Gemini.
3. Validate database structure.
4. Validate requirement traceability.
5. Generate SQL and Mermaid ER artifacts.
6. Record results and execution time.

Outputs:
    outputs/llm_evaluation/evaluation_report.json
    outputs/llm_evaluation/evaluation_summary.csv

Important:
    This evaluates structural validity and traceability
    coverage. It does not prove semantic correctness
    against a human-reviewed reference schema.
"""

import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# --------------------------------------------------
# Project paths
# --------------------------------------------------

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


DATASET_PATH = (
    BASE_DIR
    / "datasets"
    / "llm"
    / "evaluation_cases.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "llm_evaluation"
)

ARTIFACT_DIR = (
    OUTPUT_DIR
    / "artifacts"
)


# --------------------------------------------------
# Load evaluation cases
# --------------------------------------------------

def load_evaluation_cases():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found: {DATASET_PATH}"
        )

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if isinstance(data, list):
        cases = data

    elif isinstance(data, dict):
        cases = data.get("cases")

        if cases is None:
            cases = data.get("evaluation_cases")

    else:
        raise ValueError(
            "Evaluation dataset must be a JSON list "
            "or an object containing a cases list."
        )

    if not isinstance(cases, list):
        raise ValueError(
            "Could not find evaluation cases list."
        )

    if not cases:
        raise ValueError(
            "Evaluation dataset contains no cases."
        )

    return cases


# --------------------------------------------------
# Convert dataset case to ProjectInput
# --------------------------------------------------

def build_project_input(case):
    case_id = case["case_id"]

    project_id = case.get(
        "project_id",
        case_id,
    )

    project_name = case.get(
        "project_name",
        project_id,
    )

    project_description = case.get(
        "project_description",
        f"Database design evaluation case {case_id}",
    )

    raw_requirements = case.get(
        "requirements",
        [],
    )

    if not raw_requirements:
        raise ValueError(
            f"Case {case_id} contains no requirements."
        )

    requirements = []

    for index, raw_req in enumerate(
        raw_requirements,
        start=1,
    ):
        if isinstance(raw_req, str):
            requirement_id = f"FR-{index:03d}"
            requirement_text = raw_req
            database_relevant = True
            requirement_type = "FR"

        elif isinstance(raw_req, dict):
            requirement_id = raw_req.get(
                "requirement_id",
                f"FR-{index:03d}",
            )

            requirement_text = (
                raw_req.get("requirement_text")
                or raw_req.get("text")
            )

            if not requirement_text:
                raise ValueError(
                    f"Requirement {requirement_id} "
                    "has no text."
                )

            database_relevant = raw_req.get(
                "database_relevant",
                True,
            )

            requirement_type = raw_req.get(
                "requirement_type",
                "FR",
            )

        else:
            raise ValueError(
                f"Unsupported requirement format "
                f"in case {case_id}."
            )

        requirements.append(
            Requirement(
                requirement_id=requirement_id,
                requirement_text=requirement_text,
                requirement_type=requirement_type,
                database_relevant=database_relevant,
            )
        )

    raw_architecture = case.get(
        "architecture_context",
        {},
    ) or {}

    if not isinstance(raw_architecture, dict):
        raise ValueError(
            f"Architecture context for {case_id} "
            "must be a dictionary."
        )

    raw_constraints = raw_architecture.get(
        "constraints",
        [],
    )

    if isinstance(raw_constraints, str):
        raw_constraints = [raw_constraints]

    architecture_context = ArchitectureContext(
        architecture_style=raw_architecture.get(
            "architecture_style"
        ),
        database_type=raw_architecture.get(
            "database_type",
            "Relational",
        ),
        constraints=raw_constraints,
    )

    return ProjectInput(
        project_id=project_id,
        project_name=project_name,
        project_description=project_description,
        requirements=requirements,
        architecture_context=architecture_context,
    )


# --------------------------------------------------
# Evaluate one case
# --------------------------------------------------

def evaluate_case(case, index, total):
    case_id = case["case_id"]

    print("\n" + "=" * 60)
    print(
        f"Evaluating case {index}/{total}: {case_id}"
    )
    print("=" * 60)

    project = build_project_input(case)

    print("Project:", project.project_name)
    print("Requirements:", len(project.requirements))

    start_time = time.perf_counter()

    try:
        # Run your complete database design pipeline.
        result = run_complete_database_design(
            project=project,
            generation_method="gemini",
            output_dir=ARTIFACT_DIR / case_id,
        )

        elapsed_seconds = round(
            time.perf_counter() - start_time,
            2,
        )

        schema_result = result["schema_validation"]
        mapping_result = result["mapping_validation"]

        design = result["design"]

        # Save the complete generated schema for quality evaluation.
        generated_design_dir = OUTPUT_DIR / "generated_designs"
        generated_design_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        generated_design_path = (
            generated_design_dir / f"{case_id}_design.json"
        )

        with generated_design_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                design,
                file,
                indent=2,
                ensure_ascii=False,
            ) 

        tables = design.get("tables", [])
        relationships = design.get(
            "relationships",
            [],
        )

        case_result = {
            "case_id": case_id,
            "generated_design_file": str(generated_design_path),
            "project_id": project.project_id,
            "status": "completed",
            "generation_method": "gemini",
            "nlp_model": "roberta",
            "schema_valid": schema_result["valid"],
            "mapping_valid": mapping_result["valid"],
            "overall_valid": result["overall_valid"],
            "coverage_percentage": mapping_result[
                "coverage_percentage"
            ],
            "total_requirements": mapping_result[
                "total_requirements"
            ],
            "mapped_requirements": mapping_result[
                "mapped_requirements"
            ],
            "total_tables": len(tables),
            "total_relationships": len(
                relationships
            ),
            "schema_errors": schema_result.get(
                "errors",
                [],
            ),
            "schema_warnings": schema_result.get(
                "warnings",
                [],
            ),
            "mapping_errors": mapping_result.get(
                "errors",
                [],
            ),
            "mapping_warnings": mapping_result.get(
                "warnings",
                [],
            ),
            "execution_time_seconds": elapsed_seconds,
            "artifacts": result.get(
                "artifacts",
                {},
            ),
            "error": None,
        }

        print("\nCase result:")
        print(
            "Schema valid:",
            case_result["schema_valid"],
        )
        print(
            "Mapping valid:",
            case_result["mapping_valid"],
        )
        print(
            "Coverage:",
            f"{case_result['coverage_percentage']}%",
        )
        print(
            "Overall valid:",
            case_result["overall_valid"],
        )
        print(
            "Execution time:",
            f"{elapsed_seconds}s",
        )

        return case_result

    except Exception as error:
        elapsed_seconds = round(
            time.perf_counter() - start_time,
            2,
        )

        print(
            f"\nERROR in {case_id}: "
            f"{type(error).__name__}: {error}"
        )

        return {
            "case_id": case_id,
            "project_id": project.project_id,
            "status": "failed",
            "generation_method": "gemini",
            "nlp_model": "roberta",
            "schema_valid": False,
            "mapping_valid": False,
            "overall_valid": False,
            "coverage_percentage": 0.0,
            "total_requirements": sum(
                req.database_relevant
                for req in project.requirements
            ),
            "mapped_requirements": 0,
            "total_tables": 0,
            "total_relationships": 0,
            "schema_errors": [],
            "schema_warnings": [],
            "mapping_errors": [],
            "mapping_warnings": [],
            "execution_time_seconds": elapsed_seconds,
            "artifacts": {},
            "error": (
                f"{type(error).__name__}: {error}"
            ),
        }


# --------------------------------------------------
# Calculate summary statistics
# --------------------------------------------------

def calculate_summary(results):
    total = len(results)

    completed = [
        result
        for result in results
        if result["status"] == "completed"
    ]

    passed = [
        result
        for result in results
        if result["overall_valid"]
    ]

    schema_passed = [
        result
        for result in results
        if result["schema_valid"]
    ]

    mapping_passed = [
        result
        for result in results
        if result["mapping_valid"]
    ]

    total_time = sum(
        result["execution_time_seconds"]
        for result in results
    )

    average_coverage = (
        sum(
            result["coverage_percentage"]
            for result in results
        ) / total
        if total
        else 0.0
    )

    return {
        "total_cases": total,
        "completed_cases": len(completed),
        "failed_cases": total - len(completed),
        "schema_valid_cases": len(schema_passed),
        "mapping_valid_cases": len(mapping_passed),
        "overall_valid_cases": len(passed),
        "overall_validity_rate_percentage": round(
            len(passed) / total * 100,
            2,
        ) if total else 0.0,
        "average_requirement_coverage_percentage": round(
            average_coverage,
            2,
        ),
        "total_execution_time_seconds": round(
            total_time,
            2,
        ),
        "average_execution_time_seconds": round(
            total_time / total,
            2,
        ) if total else 0.0,
    }


# --------------------------------------------------
# Save JSON and CSV reports
# --------------------------------------------------

def save_reports(results, summary):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "evaluation_name": (
            "DesignTrace AI - RoBERTa + Gemini Evaluation"
        ),
        "evaluated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "dataset": str(DATASET_PATH),
        "summary": summary,
        "case_results": results,
    }

    json_path = (
        OUTPUT_DIR / "evaluation_report.json"
    )

    with json_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    csv_path = (
        OUTPUT_DIR / "evaluation_summary.csv"
    )

    fieldnames = [
        "case_id",
        "project_id",
        "status",
        "schema_valid",
        "mapping_valid",
        "overall_valid",
        "coverage_percentage",
        "total_requirements",
        "mapped_requirements",
        "total_tables",
        "total_relationships",
        "execution_time_seconds",
        "error",
    ]

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for result in results:
            writer.writerow(
                {
                    key: result.get(key)
                    for key in fieldnames
                }
            )

    return json_path, csv_path


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    print(
        "DesignTrace AI - All LLM Cases Evaluation"
    )
    print("=" * 60)

    cases = load_evaluation_cases()

    print("Dataset:", DATASET_PATH)
    print("Total evaluation cases:", len(cases))
    print("NLP model: RoBERTa")
    print("LLM: Gemini")

    results = []

    for index, case in enumerate(
        cases,
        start=1,
    ):
        try:
            result = evaluate_case(
                case,
                index,
                len(cases),
            )

        except Exception as error:
            # Covers dataset parsing or ProjectInput
            # construction failures.
            case_id = case.get(
                "case_id",
                f"CASE-{index:03d}",
            ) if isinstance(case, dict) else f"CASE-{index:03d}"

            print(
                f"\nERROR preparing {case_id}: {error}"
            )

            result = {
                "case_id": case_id,
                "project_id": (
                    case.get("project_id", "")
                    if isinstance(case, dict)
                    else ""
                ),
                "status": "failed",
                "generation_method": "gemini",
                "nlp_model": "roberta",
                "schema_valid": False,
                "mapping_valid": False,
                "overall_valid": False,
                "coverage_percentage": 0.0,
                "total_requirements": 0,
                "mapped_requirements": 0,
                "total_tables": 0,
                "total_relationships": 0,
                "schema_errors": [],
                "schema_warnings": [],
                "mapping_errors": [],
                "mapping_warnings": [],
                "execution_time_seconds": 0.0,
                "artifacts": {},
                "error": str(error),
            }

        results.append(result)

    summary = calculate_summary(results)

    json_path, csv_path = save_reports(
        results,
        summary,
    )

    print("\n" + "=" * 60)
    print("FINAL EVALUATION SUMMARY")
    print("=" * 60)

    print(
        "Total cases:",
        summary["total_cases"],
    )
    print(
        "Completed cases:",
        summary["completed_cases"],
    )
    print(
        "Failed cases:",
        summary["failed_cases"],
    )
    print(
        "Overall valid cases:",
        summary["overall_valid_cases"],
    )
    print(
        "Validity rate:",
        f"{summary['overall_validity_rate_percentage']}%",
    )
    print(
        "Average requirement coverage:",
        f"{summary['average_requirement_coverage_percentage']}%",
    )
    print(
        "Average execution time:",
        f"{summary['average_execution_time_seconds']}s",
    )

    print("\nSaved reports:")
    print("JSON:", json_path)
    print("CSV:", csv_path)

    print("\nEvaluation completed!")


if __name__ == "__main__":
    main()
