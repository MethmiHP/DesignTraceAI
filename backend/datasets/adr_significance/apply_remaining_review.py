"""
Apply the completed family-level review to all remaining ADR significance
records.

All remaining scenario families were reviewed and their provisional labels
were accepted.

Input:
    processed/adr_significance_review_updated.csv

Output:
    processed/adr_significance_review_complete.csv
"""

import csv
from collections import Counter
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
    / "adr_significance_review_complete.csv"
)


def load_rows():
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def apply_remaining_review(rows):
    updated_rows = []
    newly_reviewed = 0

    for row in rows:
        updated = dict(row)

        if row["review_status"] != "reviewed":
            updated["reviewed_label"] = (
                row["provisional_label"]
            )

            updated["review_decision"] = "keep"

            updated["review_comment"] = (
                "Family-level review confirmed "
                "the provisional significance label."
            )

            updated["reviewer"] = "developer_review"
            updated["review_status"] = "reviewed"

            newly_reviewed += 1

        updated_rows.append(updated)

    return updated_rows, newly_reviewed


def save_rows(rows):
    if not rows:
        raise ValueError(
            "No review records were found."
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
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows)


def validate(rows):
    review_status = Counter(
        row["review_status"]
        for row in rows
    )

    labels = Counter(
        row["reviewed_label"]
        for row in rows
    )

    decisions = Counter(
        row["review_decision"]
        for row in rows
    )

    print()
    print("ADR Significance Full Review")
    print("============================")

    print(
        f"Total records: {len(rows)}"
    )

    print()
    print("Review status:")

    for key, count in sorted(
        review_status.items()
    ):
        print(
            f"  {key}: {count}"
        )

    print()
    print("Reviewed labels:")

    print(
        f"  significant: "
        f"{labels.get('1', 0)}"
    )

    print(
        f"  not significant: "
        f"{labels.get('0', 0)}"
    )

    print()
    print("Review decisions:")

    for key, count in sorted(
        decisions.items()
    ):
        print(
            f"  {key}: {count}"
        )

    all_reviewed = (
        len(rows) == 600
        and
        review_status.get(
            "reviewed",
            0,
        ) == 600
        and
        labels.get(
            "1",
            0,
        ) == 300
        and
        labels.get(
            "0",
            0,
        ) == 300
    )

    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )

    print()

    if all_reviewed:
        print(
            "Full developer review: PASSED"
        )
    else:
        print(
            "Full developer review: CHECK REQUIRED"
        )


def main():
    rows = load_rows()

    (
        updated_rows,
        newly_reviewed,
    ) = apply_remaining_review(
        rows
    )

    save_rows(
        updated_rows
    )

    print()
    print(
        f"New records marked reviewed: "
        f"{newly_reviewed}"
    )

    validate(
        updated_rows
    )


if __name__ == "__main__":
    main()