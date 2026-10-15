"""
DesignTrace AI - Synthetic Requirement Template Similarity
===========================================================

Checks similarity between project-independent
training and test requirements.

Checks:
1. Exact duplicate texts
2. Near-duplicate texts
3. Similar sentence templates

Input:
    datasets/nlp/project_split/train.json
    datasets/nlp/project_split/test.json

Output:
    outputs/nlp_models/template_similarity_report.json
"""

import json
import re
from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "datasets" / "nlp" / "project_split"

TRAIN_PATH = DATA_DIR / "train.json"
TEST_PATH = DATA_DIR / "test.json"

OUTPUT_PATH = (
    BASE_DIR
    / "outputs"
    / "nlp_models"
    / "template_similarity_report.json"
)

NEAR_DUPLICATE_THRESHOLD = 0.85
TEMPLATE_THRESHOLD = 0.85

LABELS = {"ENTITY", "ATTRIBUTE", "ACTION"}


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(text):
    """Normalize text for exact matching."""
    return " ".join(text.lower().split())


def replace_annotated_concepts(example):
    """
    Replace annotated ENTITY, ATTRIBUTE, ACTION
    spans with their label names.

    Example:
    'Patients can update their addresses.'
    becomes:
    '<ENTITY> can <ACTION> their <ATTRIBUTE>.'
    """

    text = example["text"]

    annotations = sorted(
        example.get("annotations", []),
        key=lambda item: item["start"],
        reverse=True,
    )

    for annotation in annotations:
        label = annotation["label"]

        if label not in LABELS:
            continue

        start = annotation["start"]
        end = annotation["end"]

        text = (
            text[:start]
            + f"<{label}>"
            + text[end:]
        )

    return normalize_text(text)


def similarity(text1, text2):
    return SequenceMatcher(
        None,
        text1,
        text2,
    ).ratio()


def main():

    print("DesignTrace AI - Template Similarity Check")
    print("-" * 45)

    train_data = load_json(TRAIN_PATH)
    test_data = load_json(TEST_PATH)

    print("Training requirements:", len(train_data))
    print("Test requirements:", len(test_data))

    train_texts = [
        normalize_text(item["text"])
        for item in train_data
    ]

    test_texts = [
        normalize_text(item["text"])
        for item in test_data
    ]

    train_text_set = set(train_texts)

    exact_duplicates = []

    near_duplicates = []

    template_matches = []

    train_templates = [
        replace_annotated_concepts(item)
        for item in train_data
    ]

    test_templates = [
        replace_annotated_concepts(item)
        for item in test_data
    ]

    for test_index, test_item in enumerate(test_data):

        test_text = test_texts[test_index]
        test_template = test_templates[test_index]

        if test_text in train_text_set:
            exact_duplicates.append(
                test_item["requirement_id"]
            )

        best_text_score = 0.0
        best_text_match = None

        best_template_score = 0.0
        best_template_match = None

        for train_index, train_item in enumerate(train_data):

            text_score = similarity(
                test_text,
                train_texts[train_index],
            )

            if text_score > best_text_score:
                best_text_score = text_score
                best_text_match = train_item

            template_score = similarity(
                test_template,
                train_templates[train_index],
            )

            if template_score > best_template_score:
                best_template_score = template_score
                best_template_match = train_item

        if best_text_score >= NEAR_DUPLICATE_THRESHOLD:
            near_duplicates.append(
                {
                    "test_requirement_id": test_item[
                        "requirement_id"
                    ],
                    "test_text": test_item["text"],
                    "train_requirement_id": best_text_match[
                        "requirement_id"
                    ],
                    "train_text": best_text_match["text"],
                    "similarity": round(best_text_score, 4),
                }
            )

        if best_template_score >= TEMPLATE_THRESHOLD:
            template_matches.append(
                {
                    "test_requirement_id": test_item[
                        "requirement_id"
                    ],
                    "test_template": test_template,
                    "train_requirement_id": best_template_match[
                        "requirement_id"
                    ],
                    "train_template": replace_annotated_concepts(
                        best_template_match
                    ),
                    "similarity": round(
                        best_template_score,
                        4,
                    ),
                }
            )

    summary = {
        "train_requirements": len(train_data),
        "test_requirements": len(test_data),
        "exact_duplicate_count": len(exact_duplicates),
        "near_duplicate_count": len(near_duplicates),
        "template_match_count": len(template_matches),
        "near_duplicate_threshold": (
            NEAR_DUPLICATE_THRESHOLD
        ),
        "template_threshold": TEMPLATE_THRESHOLD,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "summary": summary,
                "exact_duplicates": exact_duplicates,
                "near_duplicates": near_duplicates,
                "template_matches": template_matches,
            },
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\nSIMILARITY CHECK SUMMARY")
    print("-" * 45)

    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\nReport saved to:", OUTPUT_PATH)
    print("Template similarity check completed.")


if __name__ == "__main__":
    main()
