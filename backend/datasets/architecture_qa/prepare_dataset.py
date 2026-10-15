"""
Architecture QA supervised dataset preparation.

This script:

1. Reads all _raw*.json files.
2. Validates labels.
3. Removes exact normalized duplicate statements.
4. Assigns stable example IDs.
5. Creates qa_dataset.json.
6. Creates deterministic 70/15/15 train/validation/test splits.
7. Writes dataset_statistics.json.

The current dataset is synthetic/developer-assisted and pending expert
validation. It must not be described as expert-labelled ground truth.
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent

BACKEND_DIR = CURRENT_DIR.parent.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from modules.architecture_design.training.dataset_utils import (
    LABEL_LIST,
    normalize_statement,
    validate_dataset,
)


RANDOM_SEED = 42

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15


def load_raw_files() -> list[dict]:
    """Load all files whose names begin with _raw."""

    raw_files = sorted(CURRENT_DIR.glob("_raw*.json"))

    if not raw_files:
        raise FileNotFoundError(
            "No _raw*.json files were found in architecture_qa."
        )

    records: list[dict] = []

    for path in raw_files:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(
                f"{path.name} must contain a JSON list."
            )

        print(
            f"Loaded {len(data):4d} records from {path.name}"
        )

        records.extend(data)

    return records


def clean_records(
    raw_records: list[dict],
) -> tuple[list[dict], int]:
    """
    Normalize records, validate labels and reject duplicate statements.
    """

    cleaned: list[dict] = []

    seen: set[str] = set()
    duplicates = 0

    allowed_labels = set(LABEL_LIST)

    for record in raw_records:
        statement = str(
            record.get("statement", "")
        ).strip()

        labels = record.get("labels", [])
        domain = str(
            record.get("domain", "unknown")
        ).strip().lower()

        if not statement:
            continue

        if not labels:
            continue

        unknown = set(labels) - allowed_labels

        if unknown:
            raise ValueError(
                f"Unsupported labels {unknown} in statement:\n"
                f"{statement}"
            )

        normalized = normalize_statement(statement)

        if normalized in seen:
            duplicates += 1
            continue

        seen.add(normalized)

        cleaned.append(
            {
                "statement": statement,
                "labels": sorted(
                    set(labels),
                    key=LABEL_LIST.index,
                ),
                "source_type": record.get(
                    "source_type",
                    "synthetic",
                ),
                "domain": domain,
            }
        )

    for index, record in enumerate(
        cleaned,
        start=1,
    ):
        record["example_id"] = f"QA-{index:04d}"

    return cleaned, duplicates


def iterative_multilabel_split(
    records: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Deterministic multi-label-aware greedy split.

    It attempts to preserve label distribution across the three splits
    without introducing an additional machine-learning dependency.
    """

    random.seed(RANDOM_SEED)

    shuffled = records.copy()
    random.shuffle(shuffled)

    total = len(shuffled)

    train_target = round(total * TRAIN_RATIO)
    validation_target = round(total * VALIDATION_RATIO)

    test_target = (
        total
        - train_target
        - validation_target
    )

    target_sizes = {
        "train": train_target,
        "validation": validation_target,
        "test": test_target,
    }

    global_counts = Counter()

    for record in shuffled:
        global_counts.update(record["labels"])

    target_label_counts = {}

    ratios = {
        "train": TRAIN_RATIO,
        "validation": VALIDATION_RATIO,
        "test": TEST_RATIO,
    }

    for split_name, ratio in ratios.items():
        target_label_counts[split_name] = {
            label: global_counts[label] * ratio
            for label in LABEL_LIST
        }

    splits = {
        "train": [],
        "validation": [],
        "test": [],
    }

    split_counts = {
        split: Counter()
        for split in splits
    }

    # Put harder multi-label samples first.
    shuffled.sort(
        key=lambda r: len(r["labels"]),
        reverse=True,
    )

    for record in shuffled:

        possible_splits = [
            name
            for name in splits
            if len(splits[name]) < target_sizes[name]
        ]

        if not possible_splits:
            possible_splits = list(splits)

        best_split = None
        best_score = None

        for split_name in possible_splits:

            label_need = 0.0

            for label in record["labels"]:
                desired = target_label_counts[
                    split_name
                ][label]

                current = split_counts[
                    split_name
                ][label]

                label_need += desired - current

            size_need = (
                target_sizes[split_name]
                - len(splits[split_name])
            )

            score = (
                label_need
                + (size_need / max(total, 1))
            )

            if (
                best_score is None
                or score > best_score
            ):
                best_score = score
                best_split = split_name

        splits[best_split].append(record)
        split_counts[best_split].update(
            record["labels"]
        )

    return (
        splits["train"],
        splits["validation"],
        splits["test"],
    )


def save_json(
    filename: str,
    data,
) -> None:

    path = CURRENT_DIR / filename

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def label_counts(
    records: list[dict],
) -> dict[str, int]:

    counter = Counter()

    for record in records:
        counter.update(record["labels"])

    return {
        label: counter[label]
        for label in LABEL_LIST
    }


def build_statistics(
    full: list[dict],
    train: list[dict],
    validation: list[dict],
    test: list[dict],
    duplicate_count: int,
) -> dict:

    total_label_counts = label_counts(full)

    single_label_count = sum(
        1
        for r in full
        if len(r["labels"]) == 1
    )

    multi_label_count = sum(
        1
        for r in full
        if len(r["labels"]) > 1
    )

    total_labels = sum(
        len(r["labels"])
        for r in full
    )

    domains = Counter(
        r["domain"]
        for r in full
    )

    total = len(full)

    percentages = {
        label: round(
            (
                total_label_counts[label]
                / total
                * 100
            )
            if total
            else 0,
            2,
        )
        for label in LABEL_LIST
    }

    return {
        "random_seed": RANDOM_SEED,
        "total_records": total,
        "duplicates_rejected": duplicate_count,
        "train_count": len(train),
        "validation_count": len(validation),
        "test_count": len(test),
        "label_counts_total": total_label_counts,
        "label_counts_train": label_counts(train),
        "label_counts_validation": label_counts(
            validation
        ),
        "label_counts_test": label_counts(test),
        "label_percentages": percentages,
        "single_label_count": single_label_count,
        "multi_label_count": multi_label_count,
        "multi_label_percentage": round(
            (
                multi_label_count
                / total
                * 100
            )
            if total
            else 0,
            2,
        ),
        "avg_labels_per_example": round(
            (
                total_labels / total
            )
            if total
            else 0,
            4,
        ),
        "domain_counts": dict(
            sorted(domains.items())
        ),
    }


def print_summary(stats: dict) -> None:

    print()
    print("=" * 58)
    print(" Architecture QA Dataset")
    print("=" * 58)

    print(
        f"Total:      "
        f"{stats['total_records']:5d}"
    )

    print(
        f"Train:      "
        f"{stats['train_count']:5d}"
    )

    print(
        f"Validation: "
        f"{stats['validation_count']:5d}"
    )

    print(
        f"Test:       "
        f"{stats['test_count']:5d}"
    )

    print()
    print("Label Distribution")
    print("-" * 58)

    for label, count in stats[
        "label_counts_total"
    ].items():

        percentage = stats[
            "label_percentages"
        ][label]

        print(
            f"{label:<18}"
            f"{count:>5} "
            f"({percentage:>6.2f}%)"
        )

    print()
    print(
        "Single-label examples: "
        f"{stats['single_label_count']}"
    )

    print(
        "Multi-label examples:  "
        f"{stats['multi_label_count']} "
        f"({stats['multi_label_percentage']}%)"
    )

    print(
        "Average labels/example: "
        f"{stats['avg_labels_per_example']}"
    )

    print(
        "Duplicates rejected:    "
        f"{stats['duplicates_rejected']}"
    )

    print("=" * 58)


def main() -> None:

    raw_records = load_raw_files()

    cleaned_records, duplicate_count = (
        clean_records(raw_records)
    )

    train, validation, test = (
        iterative_multilabel_split(
            cleaned_records
        )
    )

    validate_dataset(cleaned_records)
    validate_dataset(train)
    validate_dataset(validation)
    validate_dataset(test)

    save_json(
        "qa_dataset.json",
        cleaned_records,
    )

    save_json(
        "train.json",
        train,
    )

    save_json(
        "validation.json",
        validation,
    )

    save_json(
        "test.json",
        test,
    )

    statistics = build_statistics(
        cleaned_records,
        train,
        validation,
        test,
        duplicate_count,
    )

    save_json(
        "dataset_statistics.json",
        statistics,
    )

    print_summary(statistics)


if __name__ == "__main__":
    main()