"""
Validate the diversified ADR significance candidate dataset.

Checks:
- total record count
- class balance
- source-module balance
- domain balance
- difficulty distribution
- scenario-family diversity
- duplicate identifiers
- exact duplicate text
- missing required fields
- valid labels
- valid domains
- valid source modules
- provisional review metadata
"""

import csv
from collections import Counter
from pathlib import Path


DATASET_PATH = (
    Path(__file__).resolve().parent
    / "raw"
    / "adr_significance_candidates.csv"
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


def print_counter(title, counter):
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
    print("ADR Candidate Dataset Validation")
    print("================================")

    print(
        f"Total records: {len(rows)}"
    )

    # ----------------------------------------------------------
    # Class distribution
    # ----------------------------------------------------------

    labels = Counter(
        row["label"]
        for row in rows
    )

    readable_labels = Counter(
        {
            "Not significant": labels.get("0", 0),
            "Significant": labels.get("1", 0),
        }
    )

    print_counter(
        "Class distribution:",
        readable_labels,
    )

    # ----------------------------------------------------------
    # Source-module distribution
    # ----------------------------------------------------------

    sources = Counter(
        row["source_module"]
        for row in rows
    )

    print_counter(
        "Source distribution:",
        sources,
    )

    # ----------------------------------------------------------
    # Domain distribution
    # ----------------------------------------------------------

    domains = Counter(
        row["domain"]
        for row in rows
    )

    print_counter(
        "Domain distribution:",
        domains,
    )

    # ----------------------------------------------------------
    # Difficulty distribution
    # ----------------------------------------------------------

    difficulties = Counter(
        row["difficulty"]
        for row in rows
    )

    print_counter(
        "Difficulty distribution:",
        difficulties,
    )

    # ----------------------------------------------------------
    # Scenario families
    # ----------------------------------------------------------

    scenario_families = Counter(
        (
            row["source_module"],
            row["scenario_family"],
            row["label"],
        )
        for row in rows
    )

    print()
    print(
        "Distinct module/family/label groups: "
        f"{len(scenario_families)}"
    )

    raw_family_names = set(
        row["scenario_family"]
        for row in rows
    )

    print(
        "Distinct scenario-family names: "
        f"{len(raw_family_names)}"
    )

    # ----------------------------------------------------------
    # Duplicate decision IDs
    # ----------------------------------------------------------

    ids = [
        row["decision_id"]
        for row in rows
    ]

    duplicate_ids = (
        len(ids)
        - len(set(ids))
    )

    print()
    print(
        f"Duplicate decision IDs: "
        f"{duplicate_ids}"
    )

    # ----------------------------------------------------------
    # Exact duplicate semantic input text
    # ----------------------------------------------------------

    text_signatures = [
        (
            row["source_module"].strip().lower(),
            row["domain"].strip().lower(),
            row["title"].strip().lower(),
            row["context"].strip().lower(),
            row["decision"].strip().lower(),
            row["rationale"].strip().lower(),
        )
        for row in rows
    ]

    duplicate_text = (
        len(text_signatures)
        - len(set(text_signatures))
    )

    print(
        "Exact duplicate full-text records: "
        f"{duplicate_text}"
    )

    # ----------------------------------------------------------
    # Duplicate core decision text
    # ----------------------------------------------------------

    core_signatures = [
        (
            row["title"].strip().lower(),
            row["context"].strip().lower(),
            row["decision"].strip().lower(),
        )
        for row in rows
    ]

    duplicate_core = (
        len(core_signatures)
        - len(set(core_signatures))
    )

    print(
        "Exact duplicate core decision texts: "
        f"{duplicate_core}"
    )

    # ----------------------------------------------------------
    # Missing values
    # ----------------------------------------------------------

    missing_values = []

    for row in rows:
        for field in REQUIRED_FIELDS:
            if not row.get(
                field,
                "",
            ).strip():
                missing_values.append(
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
        f"{len(missing_values)}"
    )

    # ----------------------------------------------------------
    # Valid labels
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # Difficulty validation
    # ----------------------------------------------------------

    invalid_difficulties = [
        row["decision_id"]
        for row in rows
        if row["difficulty"]
        not in VALID_DIFFICULTIES
    ]

    print(
        "Valid difficulty values: "
        f"{len(invalid_difficulties) == 0}"
    )

    # ----------------------------------------------------------
    # Domain validation
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # Source-module validation
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # Review metadata
    # ----------------------------------------------------------

    label_sources = Counter(
        row["label_source"]
        for row in rows
    )

    review_statuses = Counter(
        row["review_status"]
        for row in rows
    )

    print_counter(
        "Label source distribution:",
        label_sources,
    )

    print_counter(
        "Review status distribution:",
        review_statuses,
    )

    # ----------------------------------------------------------
    # Expected balancing
    # ----------------------------------------------------------

    expected_source_balance = all(
        sources.get(
            source,
            0,
        ) == 150
        for source in VALID_SOURCE_MODULES
    )

    expected_domain_balance = all(
        domains.get(
            domain,
            0,
        ) == 120
        for domain in VALID_DOMAINS
    )

    # ----------------------------------------------------------
    # Final result
    # ----------------------------------------------------------

    passed = all(
        [
            len(rows) == 600,
            labels.get("0", 0) == 300,
            labels.get("1", 0) == 300,
            expected_source_balance,
            expected_domain_balance,
            len(scenario_families) == 120,
            duplicate_ids == 0,
            duplicate_text == 0,
            duplicate_core == 0,
            len(missing_values) == 0,
            len(invalid_labels) == 0,
            len(invalid_difficulties) == 0,
            len(invalid_domains) == 0,
            len(invalid_sources) == 0,
        ]
    )

    print()
    print("--------------------------------")

    if passed:
        print(
            "Candidate dataset validation: PASSED"
        )
    else:
        print(
            "Candidate dataset validation: FAILED"
        )

    print("--------------------------------")


if __name__ == "__main__":
    main()