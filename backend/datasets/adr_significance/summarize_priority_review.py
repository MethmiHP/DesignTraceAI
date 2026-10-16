"""
Create a compact family-level summary for the ADR priority review dataset.

The goal is to review decision families instead of manually reading
every individual record.

The script groups records by:
- source module
- scenario family
- provisional label

For each group it reports:
- difficulty
- number of records
- covered domains
- sample title
- sample context
- sample decision
- sample rationale

The script does not modify the review dataset.
"""

import csv
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = (
    BASE_DIR
    / "processed"
    / "adr_significance_priority_review.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "processed"
    / "adr_significance_priority_summary.txt"
)


def load_rows():
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


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
    order = {
        "hard": 3,
        "medium": 2,
        "easy": 1,
    }

    return order.get(
        value,
        0,
    )


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
            item[0][1],
        ),
    )

    for index, (
        key,
        rows,
    ) in enumerate(
        sorted_groups,
        start=1,
    ):
        (
            source_module,
            scenario_family,
            label,
        ) = key

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
            f"Records in priority set: {len(rows)}",
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

    groups = group_rows(
        rows
    )

    summary = build_summary(
        groups
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        summary,
        encoding="utf-8",
    )

    significant_groups = sum(
        1
        for (
            _,
            _,
            label,
        ) in groups
        if label == "1"
    )

    non_significant_groups = sum(
        1
        for (
            _,
            _,
            label,
        ) in groups
        if label == "0"
    )

    print()
    print("ADR Priority Review Family Summary")
    print("==================================")

    print(
        f"Priority records: {len(rows)}"
    )

    print(
        f"Distinct review families: "
        f"{len(groups)}"
    )

    print(
        f"Significant families: "
        f"{significant_groups}"
    )

    print(
        f"Not significant families: "
        f"{non_significant_groups}"
    )

    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )

    print()
    print(
        "Review the generated summary family-by-family."
    )


if __name__ == "__main__":
    main()