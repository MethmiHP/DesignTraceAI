"""
DesignTrace AI - NLP Annotation Validator

Validates annotated software requirements before
NLP model training.
"""

import json
from pathlib import Path


VALID_LABELS = {"ENTITY", "ATTRIBUTE", "ACTION"}


def validate_annotations(dataset_path: str) -> dict:
    path = Path(dataset_path)

    with path.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    errors = []
    seen_ids = set()
    total_annotations = 0

    if not isinstance(dataset, list):
        raise ValueError("Dataset must be a JSON list.")

    for index, record in enumerate(dataset):
        requirement_id = record.get("requirement_id")
        text = record.get("text", "")
        annotations = record.get("annotations", [])

        if not requirement_id:
            errors.append(f"Record {index}: Missing requirement ID.")
        elif requirement_id in seen_ids:
            errors.append(f"{requirement_id}: Duplicate requirement ID.")
        else:
            seen_ids.add(requirement_id)

        if not isinstance(text, str):
            errors.append(f"{requirement_id}: Text must be a string.")
            continue

        if not isinstance(annotations, list):
            errors.append(f"{requirement_id}: Annotations must be a list.")
            continue

        spans = []

        for annotation in annotations:
            total_annotations += 1

            label = annotation.get("label")
            start = annotation.get("start")
            end = annotation.get("end")
            annotated_text = annotation.get("text")

            if label not in VALID_LABELS:
                errors.append(
                    f"{requirement_id}: Invalid label {label}."
                )

            if (
                type(start) is not int
                or type(end) is not int
                or start < 0
                or end > len(text)
                or start >= end
            ):
                errors.append(
                    f"{requirement_id}: Invalid character positions."
                )
                continue

            if text[start:end] != annotated_text:
                errors.append(
                    f"{requirement_id}: Text mismatch at "
                    f"positions {start}-{end}."
                )

            spans.append((start, end))

        spans.sort()

        for previous, current in zip(spans, spans[1:]):
            if current[0] < previous[1]:
                errors.append(
                    f"{requirement_id}: Overlapping annotations."
                )

    return {
        "total_requirements": len(dataset),
        "total_annotations": total_annotations,
        "total_errors": len(errors),
        "valid": len(errors) == 0,
        "errors": errors,
    }



if __name__ == "__main__":
    dataset_path = (
        Path(__file__).resolve().parent
        / "synthetic_annotated_requirements_1000.json"
    )

    report = validate_annotations(str(dataset_path))

    print("NLP Annotation Validation")
    print("-------------------------")
    print("Requirements:", report["total_requirements"])
    print("Annotations:", report["total_annotations"])
    print("Errors:", report["total_errors"])
    print("Validation:", "PASS" if report["valid"] else "FAIL")

    for error in report["errors"]:
        print("-", error)

