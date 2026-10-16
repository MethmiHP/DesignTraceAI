"""
Select a balanced priority subset for ADR significance label review.

Goals:
- 120 priority records
- 60 significant
- 60 not significant
- balanced across the four source modules
- prioritise hard and medium examples
- prioritise potentially ambiguous scenario families

This script does not modify the full review dataset.
"""

import csv
from collections import Counter
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
    / "adr_significance_priority_review.csv"
)


TARGET_TOTAL = 120

TARGET_PER_LABEL = 60

TARGET_PER_SOURCE = 30


SOURCE_MODULES = [
    "architecture_decision",
    "database_design",
    "api_component_design",
    "quality_evaluation",
]


AMBIGUOUS_FAMILIES = {
    "pagination_contract",
    "database_connection_pooling",
    "cache_layer",
    "read_write_separation",
    "backend_for_frontend",
    "bulk_endpoint",
    "api_timeout_policy",
    "api_retry_policy",
    "graphql_selection",
    "grpc_internal",
    "soft_delete_strategy",
    "data_archival",
    "unique_id_strategy",
    "performance_budget",
    "availability_sla",
    "input_validation_policy",
    "component_description",
    "index_name",
    "example_payload",
    "response_message",
    "threshold_description",
    "security_comment",
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


def priority_score(row):
    """
    Higher score means higher review priority.
    """

    score = 0

    difficulty = row["difficulty"]

    if difficulty == "hard":
        score += 5

    elif difficulty == "medium":
        score += 3

    elif difficulty == "easy":
        score += 1

    if row["scenario_family"] in AMBIGUOUS_FAMILIES:
        score += 3

    return score


def select_balanced_rows(rows):
    selected = []

    # 120 total:
    # 4 modules × 2 labels × 15 rows = 120
    target_per_source_label = 15

    for source_module in SOURCE_MODULES:

        for label in ["0", "1"]:

            candidates = [
                row
                for row in rows
                if (
                    row["source_module"]
                    == source_module
                    and
                    row["provisional_label"]
                    == label
                )
            ]

            candidates.sort(
                key=lambda row: (
                    priority_score(row),
                    row["difficulty"],
                    row["scenario_family"],
                    row["decision_id"],
                ),
                reverse=True,
            )

            selected.extend(
                candidates[
                    :target_per_source_label
                ]
            )

    return selected


def save_rows(rows):
    if not rows:
        raise ValueError(
            "No priority review rows were selected."
        )

    fieldnames = list(
        rows[0].keys()
    )

    fieldnames.insert(
        12,
        "priority_score",
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

        for row in rows:
            output_row = dict(row)

            output_row[
                "priority_score"
            ] = priority_score(row)

            writer.writerow(
                output_row
            )


def print_summary(rows):
    difficulty_counts = Counter(
        row["difficulty"]
        for row in rows
    )

    label_counts = Counter(
        row["provisional_label"]
        for row in rows
    )

    source_counts = Counter(
        row["source_module"]
        for row in rows
    )

    print()
    print("Balanced ADR Priority Review Dataset")
    print("====================================")

    print(
        f"Priority records selected: "
        f"{len(rows)}"
    )

    print()
    print("Labels:")

    print(
        f"  significant: "
        f"{label_counts.get('1', 0)}"
    )

    print(
        f"  not significant: "
        f"{label_counts.get('0', 0)}"
    )

    print()
    print("Source modules:")

    for source in SOURCE_MODULES:
        print(
            f"  {source}: "
            f"{source_counts.get(source, 0)}"
        )

    print()
    print("Difficulty:")

    for difficulty in [
        "hard",
        "medium",
        "easy",
    ]:
        print(
            f"  {difficulty}: "
            f"{difficulty_counts.get(difficulty, 0)}"
        )

    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )

    balanced = (
        len(rows) == TARGET_TOTAL
        and
        label_counts.get("1", 0)
        == TARGET_PER_LABEL
        and
        label_counts.get("0", 0)
        == TARGET_PER_LABEL
        and
        all(
            source_counts.get(
                source,
                0,
            )
            == TARGET_PER_SOURCE
            for source in SOURCE_MODULES
        )
    )

    print()

    if balanced:
        print(
            "Priority review balance: PASSED"
        )
    else:
        print(
            "Priority review balance: FAILED"
        )


def main():
    rows = load_rows()

    selected = select_balanced_rows(
        rows
    )

    save_rows(
        selected
    )

    print_summary(
        selected
    )


if __name__ == "__main__":
    main()