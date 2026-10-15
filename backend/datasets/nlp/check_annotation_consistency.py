"""
DesignTrace AI - Annotation Consistency Checker
================================================

Checks training annotations for:

1. Same phrase assigned different labels.
2. Multiword concepts split into smaller annotations.
3. Similar phrases with inconsistent boundaries.
4. Invalid annotation offsets.
5. Duplicate or overlapping annotation spans.

Input:
    datasets/nlp/project_split/train.json
    datasets/nlp/project_split/validation.json

Output:
    outputs/nlp_models/annotation_consistency_report.json

This script does NOT change the original datasets.
"""

import json
from pathlib import Path
from collections import defaultdict, Counter


# --------------------------------------------------
# 1. Paths and configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = (
    BASE_DIR
    / "datasets"
    / "nlp"
    / "project_split"
)

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "nlp_models"
)

TRAIN_PATH = DATA_DIR / "train.json"
VALIDATION_PATH = DATA_DIR / "validation.json"

REPORT_PATH = (
    OUTPUT_DIR
    / "annotation_consistency_report.json"
)

VALID_LABELS = {
    "ENTITY",
    "ATTRIBUTE",
    "ACTION",
}

# Known multiword concepts to inspect.
# These are review candidates, not automatic corrections.

REVIEW_PHRASES = [
    "farm code",
    "soil moisture",
    "crop variety",
    "harvested weight",
    "expected yield",
    "planting season",
    "water usage",
    "irrigation zone",
    "pickup date",
    "registration numbers",
    "branch locations",
    "transaction reference",
]


# --------------------------------------------------
# 2. Load dataset
# --------------------------------------------------

def load_dataset(path):

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            f"{path.name} must contain a JSON list."
        )

    return data


# --------------------------------------------------
# 3. Normalize phrases
# --------------------------------------------------

def normalize_phrase(text):

    return " ".join(
        text.lower().strip().split()
    )


# --------------------------------------------------
# 4. Validate annotation structure
# --------------------------------------------------

def validate_annotations(data, split_name):

    issues = []

    for index, example in enumerate(data):

        requirement_id = example.get(
            "requirement_id",
            f"{split_name}_{index}",
        )

        text = example.get("text", "")
        annotations = example.get(
            "annotations",
            [],
        )

        if not isinstance(text, str):
            issues.append({
                "requirement_id": requirement_id,
                "issue": "Invalid requirement text",
            })
            continue

        if not isinstance(annotations, list):
            issues.append({
                "requirement_id": requirement_id,
                "issue": "Annotations must be a list",
            })
            continue

        valid_spans = []
        seen = set()

        for annotation in annotations:

            if not isinstance(annotation, dict):
                issues.append({
                    "requirement_id": requirement_id,
                    "issue": "Invalid annotation object",
                })
                continue

            start = annotation.get("start")
            end = annotation.get("end")
            label = annotation.get("label")
            phrase = annotation.get("text", "")

            if label not in VALID_LABELS:
                issues.append({
                    "requirement_id": requirement_id,
                    "issue": "Unknown label",
                    "annotation": annotation,
                })

            if (
                not isinstance(start, int)
                or isinstance(start, bool)
                or not isinstance(end, int)
                or isinstance(end, bool)
                or start < 0
                or end > len(text)
                or start >= end
            ):
                issues.append({
                    "requirement_id": requirement_id,
                    "issue": "Invalid character offsets",
                    "annotation": annotation,
                })
                continue

            actual_text = text[start:end]

            if actual_text != phrase:
                issues.append({
                    "requirement_id": requirement_id,
                    "issue": "Annotation text mismatch",
                    "expected": actual_text,
                    "annotated": phrase,
                })

            span_key = (
                start,
                end,
                label,
            )

            if span_key in seen:
                issues.append({
                    "requirement_id": requirement_id,
                    "issue": "Duplicate annotation",
                    "annotation": annotation,
                })

            seen.add(span_key)

            valid_spans.append(
                (start, end, label, phrase)
            )

        valid_spans.sort(key=lambda item: item[0])

        for first, second in zip(
            valid_spans,
            valid_spans[1:],
        ):

            if second[0] < first[1]:
                issues.append({
                    "requirement_id": requirement_id,
                    "issue": "Overlapping annotations",
                    "first": first[3],
                    "second": second[3],
                })

    return issues


# --------------------------------------------------
# 5. Detect inconsistent phrase labels
# --------------------------------------------------

def check_phrase_labels(data, split_name):

    phrase_labels = defaultdict(list)

    for example in data:

        requirement_id = example.get(
            "requirement_id",
            "UNKNOWN",
        )

        for annotation in example.get(
            "annotations",
            [],
        ):

            if not isinstance(annotation, dict):
                continue

            phrase = annotation.get("text", "")
            label = annotation.get("label")

            if not isinstance(phrase, str):
                continue

            normalized = normalize_phrase(phrase)

            if not normalized or label not in VALID_LABELS:
                continue

            phrase_labels[normalized].append({
                "requirement_id": requirement_id,
                "split": split_name,
                "label": label,
            })

    return phrase_labels


# --------------------------------------------------
# 6. Find conflicting labels
# --------------------------------------------------

def find_label_conflicts(phrase_labels):

    conflicts = []

    for phrase, occurrences in phrase_labels.items():

        labels = sorted({
            item["label"]
            for item in occurrences
        })

        if len(labels) > 1:

            conflicts.append({
                "phrase": phrase,
                "labels": labels,
                "occurrences": occurrences,
            })

    return conflicts


# --------------------------------------------------
# 7. Check multiword phrase boundaries
# --------------------------------------------------

def check_multiword_phrases(data, split_name):

    findings = []

    for example in data:

        text = example.get("text", "")

        if not isinstance(text, str):
            continue

        requirement_id = example.get(
            "requirement_id",
            "UNKNOWN",
        )

        annotations = example.get(
            "annotations",
            [],
        )

        if not isinstance(annotations, list):
            continue

        for phrase in REVIEW_PHRASES:

            normalized_text = text.lower()
            normalized_phrase = phrase.lower()

            search_position = 0

            while True:

                start = normalized_text.find(
                    normalized_phrase,
                    search_position,
                )

                if start == -1:
                    break

                end = start + len(phrase)

                search_position = end

                # Only match complete phrases,
                # not substrings inside other words.

                if (
                    start > 0
                    and normalized_text[start - 1].isalnum()
                ):
                    continue

                if (
                    end < len(text)
                    and normalized_text[end].isalnum()
                ):
                    continue

                overlapping = []

                for annotation in annotations:

                    if not isinstance(annotation, dict):
                        continue

                    ann_start = annotation.get("start")
                    ann_end = annotation.get("end")

                    if (
                        not isinstance(ann_start, int)
                        or not isinstance(ann_end, int)
                    ):
                        continue

                    if (
                        ann_start < end
                        and ann_end > start
                    ):
                        overlapping.append(annotation)

                exact_matches = [
                    annotation
                    for annotation in overlapping
                    if (
                        annotation.get("start") == start
                        and annotation.get("end") == end
                    )
                ]

                if exact_matches:
                    status = "FULL_SPAN"
                elif overlapping:
                    status = "SPLIT_OR_PARTIAL"
                else:
                    status = "UNANNOTATED"

                findings.append({
                    "requirement_id": requirement_id,
                    "split": split_name,
                    "phrase": text[start:end],
                    "status": status,
                    "annotations": overlapping,
                })

    return findings


# --------------------------------------------------
# 8. Generate summary
# --------------------------------------------------

def summarize_findings(
    structural_issues,
    label_conflicts,
    multiword_findings,
):

    status_counts = Counter(
        item["status"]
        for item in multiword_findings
    )

    return {
        "structural_issue_count": len(
            structural_issues
        ),
        "label_conflict_count": len(
            label_conflicts
        ),
        "multiword_occurrences": len(
            multiword_findings
        ),
        "full_span_count": status_counts[
            "FULL_SPAN"
        ],
        "split_or_partial_count": status_counts[
            "SPLIT_OR_PARTIAL"
        ],
        "unannotated_count": status_counts[
            "UNANNOTATED"
        ],
    }


# --------------------------------------------------
# 9. Main
# --------------------------------------------------

def main():

    print(
        "DesignTrace AI - Annotation Consistency Check"
    )
    print("------------------------------------------")

    train_data = load_dataset(TRAIN_PATH)
    validation_data = load_dataset(VALIDATION_PATH)

    print(
        "Training requirements:",
        len(train_data),
    )

    print(
        "Validation requirements:",
        len(validation_data),
    )

    structural_issues = []

    structural_issues.extend(
        validate_annotations(
            train_data,
            "train",
        )
    )

    structural_issues.extend(
        validate_annotations(
            validation_data,
            "validation",
        )
    )

    phrase_labels = defaultdict(list)

    for split_name, data in [
        ("train", train_data),
        ("validation", validation_data),
    ]:

        split_phrases = check_phrase_labels(
            data,
            split_name,
        )

        for phrase, occurrences in split_phrases.items():
            phrase_labels[phrase].extend(
                occurrences
            )

    label_conflicts = find_label_conflicts(
        phrase_labels
    )

    multiword_findings = []

    for split_name, data in [
        ("train", train_data),
        ("validation", validation_data),
    ]:

        multiword_findings.extend(
            check_multiword_phrases(
                data,
                split_name,
            )
        )

    summary = summarize_findings(
        structural_issues,
        label_conflicts,
        multiword_findings,
    )

    report = {
        "training_requirements": len(
            train_data
        ),
        "validation_requirements": len(
            validation_data
        ),
        "summary": summary,
        "structural_issues": structural_issues,
        "label_conflicts": label_conflicts,
        "multiword_findings": multiword_findings,
    }

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        REPORT_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\nANNOTATION CONSISTENCY SUMMARY")
    print("------------------------------------------")

    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\nExample label conflicts:")

    for conflict in label_conflicts[:10]:
        print(
            f"  {conflict['phrase']}: "
            f"{conflict['labels']}"
        )

    print("\nExample multiword issues:")

    problematic = [
        item
        for item in multiword_findings
        if item["status"] != "FULL_SPAN"
    ]

    for item in problematic[:10]:
        print(
            f"  {item['requirement_id']}: "
            f"{item['phrase']} -> "
            f"{item['status']}"
        )

    print("\nReport saved to:", REPORT_PATH)
    print("Annotation consistency check completed.")


if __name__ == "__main__":
    main()
