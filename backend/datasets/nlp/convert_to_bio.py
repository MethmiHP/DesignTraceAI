"""
DesignTrace AI - Annotation to BIO Converter
============================================

Converts manually annotated requirements into
BIO-tagged token sequences.

Input files:
    train.json
    validation.json
    test.json

Output files:
    train_bio.json
    validation_bio.json
    test_bio.json

Supported labels:
    ENTITY
    ATTRIBUTE
    ACTION
"""

import json
import re
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "cleaned"

LABELS = {"ENTITY", "ATTRIBUTE", "ACTION"}

TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def tokenize_with_offsets(text: str):
    """
    Tokenize text while keeping character positions.

    Returns:
        List of (token, start, end) tuples.
    """
    return [
        (match.group(), match.start(), match.end())
        for match in TOKEN_PATTERN.finditer(text)
    ]


def convert_requirement_to_bio(requirement: dict) -> dict:
    """
    Convert one annotated requirement to BIO format.
    """

    text = requirement["text"]
    annotations = requirement.get("annotations", [])

    token_data = tokenize_with_offsets(text)

    tokens = [item[0] for item in token_data]
    bio_labels = ["O"] * len(tokens)

    # Validate annotations and prevent overlapping spans.
    occupied = set()

    for annotation in sorted(
        annotations,
        key=lambda item: item["start"],
    ):
        label = annotation["label"]
        start = annotation["start"]
        end = annotation["end"]
        annotated_text = annotation["text"]

        if label not in LABELS:
            raise ValueError(
                f"Unsupported label: {label}"
            )

        if (
            not isinstance(start, int)
            or not isinstance(end, int)
            or start < 0
            or end > len(text)
            or start >= end
        ):
            raise ValueError(
                f"Invalid annotation offsets: "
                f"{requirement['requirement_id']}"
            )

        if text[start:end] != annotated_text:
            raise ValueError(
                f"Annotation text mismatch in "
                f"{requirement['requirement_id']}: "
                f"expected {annotated_text!r}, "
                f"found {text[start:end]!r}"
            )

        # Find tokens completely inside the annotation.
        matching_indices = [
            index
            for index, (_, token_start, token_end)
            in enumerate(token_data)
            if token_start >= start and token_end <= end
        ]

        if not matching_indices:
            raise ValueError(
                f"No tokens found for annotation "
                f"{annotated_text!r}"
            )

        # Reject annotations that cut through tokens.
        overlapping_indices = [
            index
            for index, (_, token_start, token_end)
            in enumerate(token_data)
            if token_start < end and token_end > start
        ]

        if matching_indices != overlapping_indices:
            raise ValueError(
                f"Annotation does not align with tokens: "
                f"{annotated_text!r}"
            )

        if any(index in occupied for index in matching_indices):
            raise ValueError(
                f"Overlapping annotations in "
                f"{requirement['requirement_id']}"
            )

        for position, index in enumerate(matching_indices):
            prefix = "B" if position == 0 else "I"
            bio_labels[index] = f"{prefix}-{label}"
            occupied.add(index)

    return {
        "requirement_id": requirement["requirement_id"],
        "project_id": requirement["project_id"],
        "text": text,
        "tokens": tokens,
        "ner_tags": bio_labels,
    }


def convert_file(input_name: str, output_name: str):
    """
    Convert a dataset split into BIO format.
    """

    input_path = DATA_DIR / input_name
    output_path = DATA_DIR / output_name

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    with input_path.open("r", encoding="utf-8") as file:
        requirements = json.load(file)

    if not isinstance(requirements, list):
        raise ValueError(
            f"{input_name} must contain a JSON list."
        )

    converted = []

    for requirement in requirements:
        converted.append(
            convert_requirement_to_bio(requirement)
        )

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            converted,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"{output_name}: "
        f"{len(converted)} requirements converted"
    )


def main():

    print("DesignTrace AI - BIO Conversion")
    print("--------------------------------")

    convert_file(
        "train.json",
        "train_bio.json",
    )

    convert_file(
        "validation.json",
        "validation_bio.json",
    )

    convert_file(
        "test.json",
        "test_bio.json",
    )

    print("--------------------------------")
    print("BIO conversion completed successfully.")


if __name__ == "__main__":
    main()
