"""
Create family-level summaries for ADR significance records that are still
pending review.

Input:
    processed/adr_significance_review_updated.csv

Output:
    processed/adr_significance_remaining_summary.txt

The script groups remaining records by:
- source_module
- scenario_family
- provisional_label

It does not modify the review dataset.
"""

import csv
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = (
    BASE_DIR
    / "processed"
    / "adr_significance_review_updated.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "processed"
    / "adr_significance_remaining_summary.txt"
)


def load_rows():
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def get_pending_rows(rows):
    return [
        row
        for row in rows
        if row["review_status"] != "reviewed"
    ]


def group_rows(rows):
    groups = defaultdict(list)

    for row in rows:
        key = (
            row["source_module"],
            row["scenario_family"],
            row["provisional_label"],
        )

        groups[key].append(row)

    return groups


def difficulty_rank(value):
    return {
        "hard": 3,
        "medium": 2,
        "easy": 1,
    }.get(value, 0)


def build_summary(groups):
    sections = []

    sorted_groups = sorted(
        groups.items(),
        key=lambda item: (
            -max(
                difficulty_rank(row["difficulty"])
                for row in item[1]
            ),
            item[0][0],
            item[0][2],
            item[0][1],
        ),
    )

    for index, (key, rows) in enumerate(
        sorted_groups,
        start=1,
    ):
        source_module, scenario_family, label = key

        sample = rows[0]

        domains = sorted(
            {
                row["domain"]
                for row in rows
            }
        )

        difficulties = sorted(
            {
                row["difficulty"]
                for row in rows
            }
        )

        label_text = (
            "SIGNIFICANT"
            if label == "1"
            else "NOT SIGNIFICANT"
        )

        section = [
            "=" * 78,
            f"FAMILY {index}",
            "=" * 78,
            "",
            f"Source module: {source_module}",
            f"Scenario family: {scenario_family}",
            f"Current label: {label} ({label_text})",
            f"Difficulty: {', '.join(difficulties)}",
            f"Records: {len(rows)}",
            f"Domains: {', '.join(domains)}",
            "",
            "Sample title:",
            sample["title"],
            "",
            "Sample context:",
            sample["context"],
            "",
            "Sample decision:",
            sample["decision"],
            "",
            "Sample rationale:",
            sample["rationale"],
            "",
            "Alternatives:",
            sample["alternatives"] or "(none)",
            "",
            "Trade-offs:",
            sample["trade_offs"] or "(none)",
            "",
            "REVIEW:",
            "  Recommended action: ____________________",
            "  Reviewed label: ________________________",
            "  Comment: _______________________________",
            "",
        ]

        sections.extend(section)

    return "\n".join(sections)


def main():
    rows = load_rows()

    pending_rows = get_pending_rows(rows)

    groups = group_rows(
        pending_rows
    )

    summary = build_summary(
        groups
    )

    OUTPUT_PATH.write_text(
        summary,
        encoding="utf-8",
    )

    significant_groups = sum(
        1
        for (_, _, label) in groups
        if label == "1"
    )

    non_significant_groups = sum(
        1
        for (_, _, label) in groups
        if label == "0"
    )

    print()
    print("ADR Remaining Review Summary")
    print("============================")

    print(
        f"Total records: {len(rows)}"
    )

    print(
        f"Pending records: {len(pending_rows)}"
    )

    print(
        f"Remaining families: {len(groups)}"
    )

    print(
        f"Significant families: {significant_groups}"
    )

    print(
        f"Not significant families: {non_significant_groups}"
    )

    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()