"""
DesignTrace AI - NLP Dataset Quality Checker

Checks:
1. Dataset sizes
2. Duplicate requirements
3. Cross-split data leakage
4. Annotation validity
5. Annotation overlaps
6. Label distribution
7. Project distribution
8. Similar requirement templates

Saves a JSON report to:
backend/outputs/nlp_models/dataset_quality_report.json
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "datasets" / "nlp"

OUTPUT_PATH = (
    BASE_DIR
    / "outputs"
    / "nlp_models"
    / "dataset_quality_report.json"
)

SPLITS = {
    "train": "train.json",
    "validation": "validation.json",
    "test": "test.json",
    "independent": "independent_test.json",
}

VALID_LABELS = {"ENTITY", "ATTRIBUTE", "ACTION"}


def load_dataset(filename):
    path = DATA_DIR / filename

    if not path.exists():
        print(f"WARNING: Missing file: {filename}")
        return None

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            f"{filename} must contain a JSON list."
        )

    return data


def normalize_text(text):
    """Normalize text for duplicate checking."""

    return " ".join(
        text.lower().split()
    )


def template_text(text):
    """
    Normalize requirement wording to identify
    possible repeated sentence templates.

    This is only a heuristic.
    """

    text = normalize_text(text)

    text = re.sub(r"\d+", "<NUMBER>", text)

    text = re.sub(
        r"\bshall\b|\bmust\b|\bmay\b|\bcan\b",
        "<MODAL>",
        text,
    )

    return text


def validate_annotations(example):
    """Validate annotations in one requirement."""

    errors = []

    requirement_id = example.get(
        "requirement_id", "UNKNOWN"
    )

    text = example.get("text")

    if not isinstance(text, str) or not text.strip():
        return ["Missing or invalid requirement text"]

    annotations = example.get("annotations")

    if not isinstance(annotations, list):
        return ["Annotations must be a list"]

    valid_spans = []

    for index, annotation in enumerate(annotations):

        if not isinstance(annotation, dict):
            errors.append(
                f"{requirement_id}: annotation {index} "
                "is not an object"
            )
            continue

        label = annotation.get("label")
        start = annotation.get("start")
        end = annotation.get("end")
        span_text = annotation.get("text")

        if label not in VALID_LABELS:
            errors.append(
                f"{requirement_id}: invalid label {label}"
            )

        if (
            type(start) is not int
            or type(end) is not int
            or start < 0
            or end > len(text)
            or start >= end
        ):
            errors.append(
                f"{requirement_id}: invalid offsets "
                f"at annotation {index}"
            )
            continue

        if text[start:end] != span_text:
            errors.append(
                f"{requirement_id}: annotation text "
                f"mismatch at annotation {index}"
            )

        valid_spans.append((start, end))

    valid_spans.sort()

    for previous, current in zip(
        valid_spans, valid_spans[1:]
    ):
        if current[0] < previous[1]:
            errors.append(
                f"{requirement_id}: overlapping annotations"
            )

    return errors


def analyze_split(name, data):
    """Analyze one dataset split."""

    label_counts = Counter()
    project_counts = Counter()
    text_counts = Counter()
    id_counts = Counter()
    template_counts = Counter()

    errors = []
    annotated_examples = 0
    multiword_counts = Counter()

    for index, example in enumerate(data):

        if not isinstance(example, dict):
            errors.append(
                f"Row {index}: requirement must be an object"
            )
            continue

        requirement_id = example.get(
            "requirement_id"
        )

        project_id = example.get(
            "project_id", "UNKNOWN"
        )

        text = example.get("text", "")

        if not isinstance(requirement_id, str) or not requirement_id:
            errors.append(
                f"Row {index}: missing requirement_id"
            )
        else:
            id_counts[requirement_id] += 1

        if not isinstance(project_id, str) or not project_id:
            errors.append(
                f"Row {index}: invalid project_id"
            )
        else:
            project_counts[project_id] += 1

        if isinstance(text, str) and text.strip():
            normalized = normalize_text(text)
            text_counts[normalized] += 1
            template_counts[template_text(text)] += 1

        errors.extend(
            validate_annotations(example)
        )

        annotations = example.get(
            "annotations", []
        )

        if not isinstance(annotations, list):
            continue

        if annotations:
            annotated_examples += 1

        for annotation in annotations:

            if not isinstance(annotation, dict):
                continue

            label = annotation.get("label")
            span_text = annotation.get("text")

            if label in VALID_LABELS:
                label_counts[label] += 1

                if (
                    isinstance(span_text, str)
                    and len(span_text.split()) > 1
                ):
                    multiword_counts[label] += 1

    duplicate_texts = {
        text: count
        for text, count in text_counts.items()
        if count > 1
    }

    duplicate_ids = {
        key: count
        for key, count in id_counts.items()
        if count > 1
    }

    repeated_templates = {
        text: count
        for text, count in template_counts.items()
        if count > 1
    }

    return {
        "requirements": len(data),
        "annotated_requirements": annotated_examples,
        "projects": dict(project_counts),
        "label_counts": dict(label_counts),
        "multiword_label_counts": dict(multiword_counts),
        "duplicate_texts": duplicate_texts,
        "duplicate_ids": duplicate_ids,
        "repeated_templates": repeated_templates,
        "annotation_errors": errors,
    }


def check_cross_split_leakage(datasets):
    """
    Find exact duplicate texts and shared project IDs
    between dataset splits.
    """

    results = {}

    names = list(datasets.keys())

    for i, first_name in enumerate(names):

        for second_name in names[i + 1:]:

            first = datasets[first_name]
            second = datasets[second_name]

            first_texts = {
                normalize_text(item["text"])
                for item in first
                if isinstance(item, dict)
                and isinstance(item.get("text"), str)
            }

            second_texts = {
                normalize_text(item["text"])
                for item in second
                if isinstance(item, dict)
                and isinstance(item.get("text"), str)
            }

            first_projects = {
                item["project_id"]
                for item in first
                if isinstance(item, dict)
                and isinstance(item.get("project_id"), str)
            }

            second_projects = {
                item["project_id"]
                for item in second
                if isinstance(item, dict)
                and isinstance(item.get("project_id"), str)
            }

            key = f"{first_name}_vs_{second_name}"

            results[key] = {
                "duplicate_text_count": len(
                    first_texts & second_texts
                ),
                "duplicate_text_examples": sorted(
                    first_texts & second_texts
                )[:10],
                "shared_projects": sorted(
                    first_projects & second_projects
                ),
            }

    return results


def main():

    print("DesignTrace AI - NLP Dataset Quality Check")
    print("------------------------------------------")

    datasets = {}

    for split, filename in SPLITS.items():

        data = load_dataset(filename)

        if data is not None:
            datasets[split] = data

    if not datasets:
        print("No datasets found.")
        return

    report = {
        "splits": {},
        "cross_split_checks": {},
    }

    for name, data in datasets.items():

        result = analyze_split(name, data)

        report["splits"][name] = result

        print(f"\n{name.upper()} DATASET")
        print("Requirements:", result["requirements"])
        print("Projects:", len(result["projects"]))
        print("Labels:", result["label_counts"])
        print(
            "Multiword labels:",
            result["multiword_label_counts"]
        )
        print(
            "Duplicate texts:",
            len(result["duplicate_texts"])
        )
        print(
            "Duplicate IDs:",
            len(result["duplicate_ids"])
        )
        print(
            "Repeated templates:",
            len(result["repeated_templates"])
        )
        print(
            "Annotation errors:",
            len(result["annotation_errors"])
        )

    report["cross_split_checks"] = (
        check_cross_split_leakage(datasets)
    )

    print("\nCROSS-SPLIT CHECKS")
    print("------------------")

    for comparison, result in (
        report["cross_split_checks"].items()
    ):

        print(f"\n{comparison}")
        print(
            "Duplicate texts:",
            result["duplicate_text_count"]
        )
        print(
            "Shared projects:",
            result["shared_projects"]
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n------------------------------------------")
    print("Dataset quality check completed.")
    print("Report saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
