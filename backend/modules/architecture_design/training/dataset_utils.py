"""
Dataset utilities for supervised Architecture Quality Attribute classification.

Official label space:
- Security
- Scalability
- Performance
- Reliability
- Maintainability
- Availability

The task is multi-label classification, therefore one requirement may contain
more than one quality attribute.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


LABEL_LIST = [
    "Security",
    "Scalability",
    "Performance",
    "Reliability",
    "Maintainability",
    "Availability",
]

LABEL_TO_ID = {
    label: index
    for index, label in enumerate(LABEL_LIST)
}


def labels_to_multihot(labels: list[str]) -> list[int]:
    """
    Convert a list of quality-attribute labels into a six-element multi-hot
    representation.

    Example:
        ["Security", "Performance"]

    becomes:
        [1, 0, 1, 0, 0, 0]
    """

    unknown = set(labels) - set(LABEL_LIST)

    if unknown:
        raise ValueError(
            f"Unsupported quality attribute labels: {sorted(unknown)}"
        )

    return [
        1 if label in labels else 0
        for label in LABEL_LIST
    ]


def normalize_statement(statement: str) -> str:
    """
    Normalize a requirement statement for duplicate detection.

    This normalization is intentionally conservative. We lowercase and
    normalize whitespace without changing the semantic wording.
    """

    return " ".join(statement.strip().lower().split())


def load_split(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSON dataset split."""

    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    validate_dataset(data)

    return data


def validate_dataset(records: list[dict[str, Any]]) -> None:
    """
    Validate the structure and label space of an Architecture QA dataset.
    """

    if not isinstance(records, list):
        raise ValueError("Dataset must be a JSON list.")

    seen_ids: set[str] = set()
    seen_statements: set[str] = set()

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(
                f"Record at index {index} must be a JSON object."
            )

        required_fields = {
            "example_id",
            "statement",
            "labels",
            "source_type",
            "domain",
        }

        missing = required_fields - set(record.keys())

        if missing:
            raise ValueError(
                f"Record at index {index} is missing fields: "
                f"{sorted(missing)}"
            )

        example_id = record["example_id"]
        statement = record["statement"]
        labels = record["labels"]

        if not isinstance(example_id, str) or not example_id.strip():
            raise ValueError(
                f"Invalid example_id at index {index}."
            )

        if example_id in seen_ids:
            raise ValueError(
                f"Duplicate example_id detected: {example_id}"
            )

        seen_ids.add(example_id)

        if not isinstance(statement, str) or not statement.strip():
            raise ValueError(
                f"Empty statement at index {index}."
            )

        normalized = normalize_statement(statement)

        if normalized in seen_statements:
            raise ValueError(
                f"Duplicate requirement statement detected: {statement}"
            )

        seen_statements.add(normalized)

        if not isinstance(labels, list) or len(labels) == 0:
            raise ValueError(
                f"Record {example_id} must contain at least one label."
            )

        if len(labels) != len(set(labels)):
            raise ValueError(
                f"Record {example_id} contains duplicate labels."
            )

        unknown_labels = set(labels) - set(LABEL_LIST)

        if unknown_labels:
            raise ValueError(
                f"Record {example_id} contains unsupported labels: "
                f"{sorted(unknown_labels)}"
            )


def add_multihot_labels(
    records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Return copies of records containing an additional 'label_vector' field.

    This function will be useful when preparing data for BERT, DistilBERT,
    and RoBERTa training.
    """

    output = []

    for record in records:
        enriched = dict(record)
        enriched["label_vector"] = labels_to_multihot(
            record["labels"]
        )
        output.append(enriched)

    return output