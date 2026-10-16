"""
Validate ADR Significance Seed Dataset V2.

Checks:
- dataset size
- class balance
- source distribution
- domain distribution
- difficulty distribution
- scenario families
- duplicate IDs
- duplicate decision text
- missing values
- valid labels
- provisional labelling metadata
"""

import csv
from collections import Counter
from pathlib import Path


DATASET_PATH = (
    Path(__file__).resolve().parent
    / "raw"
    / "adr_significance_dataset.csv"
)


REQUIRED_FIELDS = [
    "decision_id",
    "source_module",
    "domain",
    "title",
    "context",
    "decision",
    "rationale",
    "scenario_family",
    "difficulty",
    "label",
    "label_source",
    "review_status",
]


VALID_LABELS = {
    "0",
    "1",
}


VALID_DIFFICULTIES = {
    "easy",
    "medium",
    "hard",
}


VALID_DOMAINS = {
    "banking",
    "healthcare",
    "ecommerce",
    "logistics",
    "education",
}


VALID_SOURCE_MODULES = {
    "architecture_decision",
    "database_design",
    "api_component_design",
    "quality_evaluation",
}


def load_dataset():
    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def print_distribution(
    title,
    counter,
):
    print()
    print(title)

    for value, count in sorted(
        counter.items()
    ):
        print(
            f"  {value}: {count}"
        )


def main():
    rows = load_dataset()

    print()
    print("ADR Significance Dataset V2 Validation")
    print("======================================")

    print(
        f"Total records: {len(rows)}"
    )

    labels = Counter(
        row["label"]
        for row in rows
    )

    readable_labels = Counter()

    readable_labels["Not significant"] = (
        labels.get("0", 0)
    )

    readable_labels["Significant"] = (
        labels.get("1", 0)
    )

    print_distribution(
        "Class distribution:",
        readable_labels,
    )

    sources = Counter(
        row["source_module"]
        for row in rows
    )

    print_distribution(
        "Source distribution:",
        sources,
    )

    domains = Counter(
        row["domain"]
        for row in rows
    )

    print_distribution(
        "Domain distribution:",
        domains,
    )

    difficulties = Counter(
        row["difficulty"]
        for row in rows
    )

    print_distribution(
        "Difficulty distribution:",
        difficulties,
    )

    scenario_families = Counter(
        row["scenario_family"]
        for row in rows
    )

    print()
    print(
        f"Scenario families: "
        f"{len(scenario_families)}"
    )

    # --------------------------------------------------------------
    # Duplicate IDs
    # --------------------------------------------------------------

    decision_ids = [
        row["decision_id"]
        for row in rows
    ]

    duplicate_ids = (
        len(decision_ids)
        - len(set(decision_ids))
    )

    print(
        f"Duplicate decision IDs: "
        f"{duplicate_ids}"
    )

    # --------------------------------------------------------------
    # Exact duplicate model input text
    # --------------------------------------------------------------

    text_signatures = [
        (
            row["title"]
            .strip()
            .lower(),

            row["context"]
            .strip()
            .lower(),

            row["decision"]
            .strip()
            .lower(),
        )
        for row in rows
    ]

    duplicate_text = (
        len(text_signatures)
        - len(set(text_signatures))
    )

    print(
        "Exact duplicate decision texts: "
        f"{duplicate_text}"
    )

    # --------------------------------------------------------------
    # Missing values
    # --------------------------------------------------------------

    missing_required = []

    for row in rows:
        for field in REQUIRED_FIELDS:
            if not row.get(
                field,
                "",
            ).strip():
                missing_required.append(
                    (
                        row.get(
                            "decision_id",
                            "UNKNOWN",
                        ),
                        field,
                    )
                )

    print(
        "Missing required values: "
        f"{len(missing_required)}"
    )

    # --------------------------------------------------------------
    # Valid binary labels
    # --------------------------------------------------------------

    invalid_labels = [
        row["decision_id"]
        for row in rows
        if row["label"]
        not in VALID_LABELS
    ]

    print(
        "Valid binary labels: "
        f"{len(invalid_labels) == 0}"
    )

    # --------------------------------------------------------------
    # Difficulty validation
    # --------------------------------------------------------------

    invalid_difficulty = [
        row["decision_id"]
        for row in rows
        if row["difficulty"]
        not in VALID_DIFFICULTIES
    ]

    print(
        "Valid difficulty values: "
        f"{len(invalid_difficulty) == 0}"
    )

    # --------------------------------------------------------------
    # Domain validation
    # --------------------------------------------------------------

    invalid_domains = [
        row["decision_id"]
        for row in rows
        if row["domain"]
        not in VALID_DOMAINS
    ]

    print(
        "Valid domains: "
        f"{len(invalid_domains) == 0}"
    )

    # --------------------------------------------------------------
    # Source module validation
    # --------------------------------------------------------------

    invalid_sources = [
        row["decision_id"]
        for row in rows
        if row["source_module"]
        not in VALID_SOURCE_MODULES
    ]

    print(
        "Valid source modules: "
        f"{len(invalid_sources) == 0}"
    )

    # --------------------------------------------------------------
    # Labelling metadata
    # --------------------------------------------------------------

    label_sources = Counter(
        row["label_source"]
        for row in rows
    )

    review_statuses = Counter(
        row["review_status"]
        for row in rows
    )

    print_distribution(
        "Label source distribution:",
        label_sources,
    )

    print_distribution(
        "Review status distribution:",
        review_statuses,
    )

    # --------------------------------------------------------------
    # Final result
    # --------------------------------------------------------------

    passed = all(
        [
            len(rows) == 100,
            labels.get("0", 0) == 50,
            labels.get("1", 0) == 50,
            duplicate_ids == 0,
            duplicate_text == 0,
            len(missing_required) == 0,
            len(invalid_labels) == 0,
            len(invalid_difficulty) == 0,
            len(invalid_domains) == 0,
            len(invalid_sources) == 0,
        ]
    )

    print()
    print("--------------------------------------")

    if passed:
        print(
            "Seed dataset V2 validation: PASSED"
        )
    else:
        print(
            "Seed dataset V2 validation: FAILED"
        )

    print("--------------------------------------")


if __name__ == "__main__":
    main()