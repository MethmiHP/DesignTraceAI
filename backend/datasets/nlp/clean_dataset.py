"""
DesignTrace AI - NLP Dataset Cleaning

Cleans annotated requirement datasets before BERT training.

Features:
1. Removes duplicate requirement texts within each dataset.
2. Removes duplicate texts across dataset splits.
3. Preserves annotations and character offsets.
4. Detects shared projects across splits.
5. Detects conflicting annotations for duplicate texts.
6. Saves cleaned datasets separately.
7. Generates a cleaning report.

Input:
    train.json
    validation.json
    test.json
    independent_test.json

Output:
    cleaned/train.json
    cleaned/validation.json
    cleaned/test.json
    cleaned/independent_test.json
    cleaned/cleaning_report.json

Run:
    python datasets/nlp/clean_dataset.py
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DATA_DIR / "cleaned"

SPLITS = [
    "train",
    "validation",
    "test",
    "independent_test",
]

VALID_LABELS = {"ENTITY", "ATTRIBUTE", "ACTION"}


def normalize_text(text):
    """Normalize whitespace and case for duplicate detection."""
    return " ".join(text.casefold().split())


def load_dataset(split):
    path = DATA_DIR / f"{split}.json"

    if not path.exists():
        raise FileNotFoundError(f"Missing dataset: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"{path.name} must contain a list.")

    return data


def validate_requirement(requirement):
    """Validate annotations without modifying their offsets."""

    required = ["requirement_id", "project_id", "text"]

    for field in required:
        if field not in requirement:
            raise ValueError(f"Missing field: {field}")

    text = requirement["text"]
    annotations = requirement.get("annotations", [])

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Requirement text must not be empty.")

    if not isinstance(annotations, list):
        raise ValueError("Annotations must be a list.")

    previous_end = -1

    for annotation in sorted(
        annotations,
        key=lambda item: item["start"],
    ):
        start = annotation["start"]
        end = annotation["end"]
        label = annotation["label"]

        if label not in VALID_LABELS:
            raise ValueError(f"Invalid label: {label}")

        if (
            not isinstance(start, int)
            or not isinstance(end, int)
            or start < 0
            or end > len(text)
            or start >= end
        ):
            raise ValueError(
                f"Invalid offsets: {requirement['requirement_id']}"
            )

        if text[start:end] != annotation["text"]:
            raise ValueError(
                f"Annotation mismatch: "
                f"{requirement['requirement_id']}"
            )

        if start < previous_end:
            raise ValueError(
                f"Overlapping annotations: "
                f"{requirement['requirement_id']}"
            )

        previous_end = end


def annotation_signature(requirement):
    """
    Represent annotations by their labeled text spans.

    Used to detect conflicting annotations for duplicate
    requirement texts.
    """

    return tuple(
        sorted(
            (
                item["label"],
                normalize_text(item["text"]),
            )
            for item in requirement.get("annotations", [])
        )
    )


def main():

    print("DesignTrace AI - NLP Dataset Cleaning")
    print("-------------------------------------")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    datasets = {
        split: load_dataset(split)
        for split in SPLITS
    }

    for split, requirements in datasets.items():
        for requirement in requirements:
            validate_requirement(requirement)

    # Detect annotation conflicts before removing duplicates.
    text_groups = defaultdict(list)

    for split, requirements in datasets.items():
        for requirement in requirements:
            key = normalize_text(requirement["text"])
            text_groups[key].append((split, requirement))

    conflicts = []

    for text_key, occurrences in text_groups.items():

        signatures = {
            annotation_signature(requirement)
            for _, requirement in occurrences
        }

        if len(signatures) > 1:
            conflicts.append({
                "text": text_key,
                "occurrences": [
                    {
                        "split": split,
                        "requirement_id": req["requirement_id"],
                        "project_id": req["project_id"],
                    }
                    for split, req in occurrences
                ],
            })

    # Priority protects independent evaluation data.
    # A duplicated text is retained in the highest-priority
    # split and removed from the other splits.
    priority = [
        "independent_test",
        "test",
        "validation",
        "train",
    ]

    seen_texts = set()
    cleaned = {}
    removed = {}

    for split in priority:

        cleaned[split] = []
        removed[split] = []

        for requirement in datasets[split]:

            key = normalize_text(requirement["text"])

            if key in seen_texts:
                removed[split].append({
                    "requirement_id": requirement["requirement_id"],
                    "project_id": requirement["project_id"],
                    "text": requirement["text"],
                    "reason": "duplicate_text",
                })
                continue

            seen_texts.add(key)
            cleaned[split].append(requirement)

    # Check project overlap after cleaning.
    project_sets = {
        split: {
            str(item["project_id"])
            for item in requirements
        }
        for split, requirements in cleaned.items()
    }

    project_overlaps = {}

    for index, split_a in enumerate(SPLITS):
        for split_b in SPLITS[index + 1:]:

            shared = sorted(
                project_sets[split_a] & project_sets[split_b]
            )

            project_overlaps[f"{split_a}_vs_{split_b}"] = shared

    # Save cleaned datasets.
    report = {
        "original_counts": {},
        "cleaned_counts": {},
        "removed_counts": {},
        "removed_requirements": removed,
        "annotation_conflicts": conflicts,
        "project_overlaps": project_overlaps,
    }

    for split in SPLITS:

        original_count = len(datasets[split])
        cleaned_count = len(cleaned[split])
        removed_count = len(removed[split])

        report["original_counts"][split] = original_count
        report["cleaned_counts"][split] = cleaned_count
        report["removed_counts"][split] = removed_count

        output_path = OUTPUT_DIR / f"{split}.json"

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(
                cleaned[split],
                file,
                indent=2,
                ensure_ascii=False,
            )

        print(f"\n{split.upper()}")
        print(" Original:", original_count)
        print(" Cleaned :", cleaned_count)
        print(" Removed :", removed_count)

    report_path = OUTPUT_DIR / "cleaning_report.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\nAnnotation conflicts:", len(conflicts))

    print("\nProject overlap warnings:")

    overlap_found = False

    for pair, projects in project_overlaps.items():
        if projects:
            overlap_found = True
            print(f" {pair}: {projects}")

    if not overlap_found:
        print(" None")

    print("\n-------------------------------------")
    print("Dataset cleaning completed.")
    print("Cleaned datasets saved to:", OUTPUT_DIR)
    print("Report saved to:", report_path)

    if conflicts:
        print(
            "\nWARNING: Conflicting annotations detected. "
            "Review cleaning_report.json before retraining."
        )

    if any(project_overlaps.values()):
        print(
            "\nWARNING: Some projects appear in multiple splits. "
            "Text deduplication does not guarantee "
            "project-independent evaluation."
        )


if __name__ == "__main__":
    main()
