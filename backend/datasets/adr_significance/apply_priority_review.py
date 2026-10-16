"""
Apply approved family-level review decisions to the full ADR significance
review dataset.

The reviewed priority families have been manually checked and accepted.

For all matching records:
- reviewed_label = provisional_label
- review_decision = keep
- reviewer = developer_review
- review_status = reviewed

The original candidate dataset is not modified.
"""

import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = (
    BASE_DIR
    / "processed"
    / "adr_significance_review.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "processed"
    / "adr_significance_review_updated.csv"
)


# ---------------------------------------------------------------------
# Priority families manually reviewed and accepted
# ---------------------------------------------------------------------

REVIEWED_FAMILIES = {
    # Significant families
    ("api_component_design", "graphql_selection", "1"),
    ("api_component_design", "grpc_internal", "1"),
    ("api_component_design", "pagination_contract", "1"),

    ("architecture_decision", "backend_for_frontend", "1"),
    ("architecture_decision", "cache_layer", "1"),
    ("architecture_decision", "read_write_separation", "1"),

    ("database_design", "data_archival", "1"),
    ("database_design", "soft_delete_strategy", "1"),
    ("database_design", "unique_id_strategy", "1"),

    ("quality_evaluation", "availability_sla", "1"),
    ("quality_evaluation", "performance_budget", "1"),
    ("quality_evaluation", "input_validation_policy", "1"),

    # Non-significant families
    ("api_component_design", "response_message", "0"),
    ("api_component_design", "sample_header", "0"),
    ("api_component_design", "example_payload", "0"),

    ("architecture_decision", "component_description", "0"),
    ("architecture_decision", "documentation_order", "0"),
    ("architecture_decision", "folder_reorganisation", "0"),

    ("database_design", "alias_name", "0"),
    ("database_design", "fixture_order", "0"),
    ("database_design", "test_table_name", "0"),

    ("quality_evaluation", "security_comment", "0"),
    ("quality_evaluation", "test_file_name", "0"),
    ("quality_evaluation", "threshold_description", "0"),
}


def load_rows():
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def apply_review(rows):
    updated_rows = []

    reviewed_count = 0

    for row in rows:
        key = (
            row["source_module"],
            row["scenario_family"],
            row["provisional_label"],
        )

        updated = dict(row)

        if key in REVIEWED_FAMILIES:
            updated["reviewed_label"] = (
                row["provisional_label"]
            )

            updated["review_decision"] = (
                "keep"
            )

            updated["review_comment"] = (
                "Family-level review confirmed "
                "the provisional significance label."
            )

            updated["reviewer"] = (
                "developer_review"
            )

            updated["review_status"] = (
                "reviewed"
            )

            reviewed_count += 1

        updated_rows.append(
            updated
        )

    return (
        updated_rows,
        reviewed_count,
    )


def save_rows(rows):
    if not rows:
        raise ValueError(
            "No review rows found."
        )

    fieldnames = list(
        rows[0].keys()
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def print_summary(
    rows,
    reviewed_count,
):
    remaining = sum(
        row["review_status"]
        != "reviewed"
        for row in rows
    )

    reviewed_positive = sum(
        row["review_status"] == "reviewed"
        and
        row["reviewed_label"] == "1"
        for row in rows
    )

    reviewed_negative = sum(
        row["review_status"] == "reviewed"
        and
        row["reviewed_label"] == "0"
        for row in rows
    )

    print()
    print("ADR Priority Review Application")
    print("===============================")

    print(
        f"Total records: {len(rows)}"
    )

    print(
        f"Priority records marked reviewed: "
        f"{reviewed_count}"
    )

    print(
        f"Reviewed significant records: "
        f"{reviewed_positive}"
    )

    print(
        f"Reviewed not-significant records: "
        f"{reviewed_negative}"
    )

    print(
        f"Records still pending review: "
        f"{remaining}"
    )

    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )

    print()

    if reviewed_count == 120:
        print(
            "Priority review application: PASSED"
        )
    else:
        print(
            "Priority review application: CHECK REQUIRED"
        )


def main():
    rows = load_rows()

    (
        updated_rows,
        reviewed_count,
    ) = apply_review(
        rows
    )

    save_rows(
        updated_rows
    )

    print_summary(
        updated_rows,
        reviewed_count,
    )


if __name__ == "__main__":
    main()