"""
Finalize and freeze the reviewed ADR significance dataset.

Input:
    processed/adr_significance_review_complete.csv
    raw/adr_significance_candidates.csv

Output:
    processed/adr_significance_final.csv

This version restores requirement_ids and design_element_ids
from the original candidate dataset using decision_id.
"""

import csv
import re
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

REVIEW_INPUT_PATH = (
    BASE_DIR
    / "processed"
    / "adr_significance_review_complete.csv"
)

RAW_INPUT_PATH = (
    BASE_DIR
    / "raw"
    / "adr_significance_candidates.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "processed"
    / "adr_significance_final.csv"
)


FINAL_FIELDS = [
    "decision_id",
    "source_module",
    "domain",
    "title",
    "context",
    "decision",
    "rationale",
    "alternatives",
    "trade_offs",
    "requirement_ids",
    "design_element_ids",
    "scenario_family",
    "difficulty",
    "label",
    "label_source",
    "review_status",
]


TEXT_FIELDS = [
    "title",
    "context",
    "decision",
    "rationale",
    "alternatives",
    "trade_offs",
]


TEXT_REPLACEMENTS = {
    "student record records": "student records",
    "transaction transactions": "transactions",
    "appointment appointments": "appointments",
    "order orders": "orders",
    "shipment shipments": "shipments",
    "course courses": "courses",
}


def load_csv(path):
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def clean_text(value):
    if not value:
        return value

    cleaned = value.strip()

    for old, new in TEXT_REPLACEMENTS.items():
        cleaned = cleaned.replace(
            old,
            new,
        )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    )

    return cleaned


def build_raw_lookup(raw_rows):
    lookup = {}

    for row in raw_rows:
        decision_id = row["decision_id"]

        if decision_id in lookup:
            raise ValueError(
                f"Duplicate decision ID in raw dataset: "
                f"{decision_id}"
            )

        lookup[decision_id] = row

    return lookup


def finalize_row(review_row, raw_lookup):
    decision_id = review_row["decision_id"]

    if decision_id not in raw_lookup:
        raise ValueError(
            f"Decision {decision_id} is missing from "
            "the original candidate dataset."
        )

    raw_row = raw_lookup[
        decision_id
    ]

    final_row = {
        "decision_id": decision_id,
        "source_module": review_row[
            "source_module"
        ],
        "domain": review_row[
            "domain"
        ],
        "title": review_row[
            "title"
        ],
        "context": review_row[
            "context"
        ],
        "decision": review_row[
            "decision"
        ],
        "rationale": review_row[
            "rationale"
        ],
        "alternatives": review_row[
            "alternatives"
        ],
        "trade_offs": review_row[
            "trade_offs"
        ],

        # Restored from original candidate data.
        "requirement_ids": raw_row.get(
            "requirement_ids",
            "",
        ),

        "design_element_ids": raw_row.get(
            "design_element_ids",
            "",
        ),

        "scenario_family": review_row[
            "scenario_family"
        ],

        "difficulty": review_row[
            "difficulty"
        ],

        "label": review_row[
            "reviewed_label"
        ],

        "label_source": (
            "developer_reviewed"
        ),

        "review_status": (
            "reviewed"
        ),
    }

    for field in TEXT_FIELDS:
        final_row[field] = clean_text(
            final_row[field]
        )

    return final_row


def validate(rows):
    errors = []

    if len(rows) != 600:
        errors.append(
            f"Expected 600 records, "
            f"found {len(rows)}."
        )

    labels = Counter(
        row["label"]
        for row in rows
    )

    if labels.get("1", 0) != 300:
        errors.append(
            "Expected 300 significant records."
        )

    if labels.get("0", 0) != 300:
        errors.append(
            "Expected 300 non-significant records."
        )

    ids = [
        row["decision_id"]
        for row in rows
    ]

    duplicate_ids = (
        len(ids)
        - len(set(ids))
    )

    if duplicate_ids:
        errors.append(
            f"Found {duplicate_ids} duplicate IDs."
        )

    signatures = [
        (
            row["source_module"].lower(),
            row["domain"].lower(),
            row["title"].lower(),
            row["context"].lower(),
            row["decision"].lower(),
            row["rationale"].lower(),
        )
        for row in rows
    ]

    duplicate_texts = (
        len(signatures)
        - len(set(signatures))
    )

    if duplicate_texts:
        errors.append(
            f"Found {duplicate_texts} "
            "exact duplicate records."
        )

    missing_required = []

    required_fields = [
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
    ]

    for row in rows:
        for field in required_fields:
            if not row[
                field
            ].strip():
                missing_required.append(
                    (
                        row["decision_id"],
                        field,
                    )
                )

    if missing_required:
        errors.append(
            f"Found {len(missing_required)} "
            "missing required values."
        )

    missing_requirement_ids = sum(
        not row[
            "requirement_ids"
        ].strip()
        for row in rows
        if row["label"] == "1"
    )

    missing_design_ids = sum(
        not row[
            "design_element_ids"
        ].strip()
        for row in rows
    )

    if missing_requirement_ids:
        errors.append(
            f"{missing_requirement_ids} significant "
            "records are missing requirement IDs."
        )

    if missing_design_ids:
        errors.append(
            f"{missing_design_ids} records are "
            "missing design element IDs."
        )

    return {
        "errors": errors,
        "labels": labels,
        "duplicate_ids": duplicate_ids,
        "duplicate_texts": duplicate_texts,
        "missing_requirement_ids": (
            missing_requirement_ids
        ),
        "missing_design_ids": (
            missing_design_ids
        ),
    }


def save_rows(rows):
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
            fieldnames=FINAL_FIELDS,
        )

        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows, result):
    source_counts = Counter(
        row["source_module"]
        for row in rows
    )

    domain_counts = Counter(
        row["domain"]
        for row in rows
    )

    difficulty_counts = Counter(
        row["difficulty"]
        for row in rows
    )

    family_count = len(
        {
            (
                row["source_module"],
                row["scenario_family"],
                row["label"],
            )
            for row in rows
        }
    )

    print()
    print("ADR Significance Frozen Dataset")
    print("===============================")

    print(
        f"Total records: {len(rows)}"
    )

    print()
    print("Labels:")
    print(
        f"  significant: "
        f"{result['labels'].get('1', 0)}"
    )
    print(
        f"  not significant: "
        f"{result['labels'].get('0', 0)}"
    )

    print()
    print("Source modules:")

    for key, count in sorted(
        source_counts.items()
    ):
        print(
            f"  {key}: {count}"
        )

    print()
    print("Domains:")

    for key, count in sorted(
        domain_counts.items()
    ):
        print(
            f"  {key}: {count}"
        )

    print()
    print("Difficulty:")

    for key, count in sorted(
        difficulty_counts.items()
    ):
        print(
            f"  {key}: {count}"
        )

    print()
    print(
        f"Distinct module/family/label groups: "
        f"{family_count}"
    )

    print(
        f"Duplicate IDs: "
        f"{result['duplicate_ids']}"
    )

    print(
        f"Exact duplicate records: "
        f"{result['duplicate_texts']}"
    )

    print(
        "Missing requirement IDs "
        "(significant records): "
        f"{result['missing_requirement_ids']}"
    )

    print(
        "Missing design element IDs: "
        f"{result['missing_design_ids']}"
    )

    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )

    print()
    print("--------------------------------")

    if not result["errors"]:
        print(
            "FROZEN DATASET VALIDATION: PASSED"
        )
    else:
        print(
            "FROZEN DATASET VALIDATION: FAILED"
        )

        print()

        for error in result["errors"]:
            print(
                f"- {error}"
            )

    print("--------------------------------")


def main():
    review_rows = load_csv(
        REVIEW_INPUT_PATH
    )

    raw_rows = load_csv(
        RAW_INPUT_PATH
    )

    raw_lookup = build_raw_lookup(
        raw_rows
    )

    final_rows = [
        finalize_row(
            row,
            raw_lookup,
        )
        for row in review_rows
    ]

    result = validate(
        final_rows
    )

    if not result["errors"]:
        save_rows(
            final_rows
        )

    print_summary(
        final_rows,
        result,
    )


if __name__ == "__main__":
    main()