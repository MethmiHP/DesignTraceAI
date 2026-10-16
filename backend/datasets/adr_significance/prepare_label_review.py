"""
Prepare the ADR significance candidate dataset for manual label review.

The generated review file preserves the original provisional label and
adds fields that can be completed during human/developer review.

No original dataset records are modified.
"""

import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = (
    BASE_DIR
    / "raw"
    / "adr_significance_candidates.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "processed"
    / "adr_significance_review.csv"
)


REVIEW_FIELDS = [
    "decision_id",
    "source_module",
    "domain",
    "title",
    "context",
    "decision",
    "rationale",
    "alternatives",
    "trade_offs",
    "scenario_family",
    "difficulty",
    "provisional_label",
    "reviewed_label",
    "review_decision",
    "review_comment",
    "reviewer",
    "review_status",
]


def load_dataset():
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def build_review_rows(rows):
    review_rows = []

    for row in rows:
        review_rows.append(
            {
                "decision_id": row["decision_id"],
                "source_module": row["source_module"],
                "domain": row["domain"],
                "title": row["title"],
                "context": row["context"],
                "decision": row["decision"],
                "rationale": row["rationale"],
                "alternatives": row["alternatives"],
                "trade_offs": row["trade_offs"],
                "scenario_family": row["scenario_family"],
                "difficulty": row["difficulty"],
                "provisional_label": row["label"],

                # Initially preserve the provisional label.
                # The reviewer can change this if necessary.
                "reviewed_label": row["label"],

                "review_decision": "pending",
                "review_comment": "",
                "reviewer": "",
                "review_status": "pending_review",
            }
        )

    return review_rows


def save_review_file(rows):
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
            fieldnames=REVIEW_FIELDS,
        )

        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = load_dataset()

    review_rows = build_review_rows(
        rows
    )

    save_review_file(
        review_rows
    )

    print()
    print("ADR Significance Label Review File")
    print("==================================")
    print(f"Input records: {len(rows)}")
    print(f"Review records: {len(review_rows)}")
    print(f"Output: {OUTPUT_PATH}")

    print()
    print("Allowed review decisions:")
    print("  keep")
    print("  change_label")
    print("  rewrite")
    print("  remove")

    print()
    print(
        "The original candidate dataset has not been modified."
    )


if __name__ == "__main__":
    main()