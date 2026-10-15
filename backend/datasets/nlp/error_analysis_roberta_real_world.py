"""
DesignTrace AI - Real-World RoBERTa Error Analysis
=================================================

Compares gold annotations with RoBERTa predictions
using strict character-span matching.

Reports:
    1. Correct concepts (TP)
    2. Missing concepts (FN)
    3. Incorrect concepts (FP)
    4. Per-label Precision, Recall and F1-score
    5. Example prediction errors

Model:
    outputs/nlp_models/roberta_project_split/

Dataset:
    datasets/nlp/real_world_test.json

Output:
    outputs/nlp_models/roberta_project_split/
        real_world_error_analysis.json
"""

import json
import re
from pathlib import Path
from collections import Counter

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
)


# --------------------------------------------------
# 1. Paths and configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    BASE_DIR
    / "outputs"
    / "nlp_models"
    / "roberta_project_split"
)

TEST_PATH = (
    BASE_DIR
    / "datasets"
    / "nlp"
    / "real_world_test.json"
)

OUTPUT_PATH = (
    MODEL_DIR
    / "real_world_error_analysis.json"
)

MODEL_NAME = "roberta-base"

LABELS = ("ENTITY", "ATTRIBUTE", "ACTION")

TOKEN_PATTERN = re.compile(
    r"\w+|[^\w\s]",
    re.UNICODE,
)

MAX_LENGTH = 128


# --------------------------------------------------
# 2. Reconstruct BIO spans
# --------------------------------------------------

def get_spans(words, tags):
    """
    Reconstruct labeled spans from BIO predictions.

    Example:
        words = ["farm", "code"]
        tags = ["B-ATTRIBUTE", "I-ATTRIBUTE"]

    Result:
        ATTRIBUTE: farm code
    """

    spans = []
    start = None
    current_label = None

    def close(end):
        if start is not None:
            spans.append({
                "label": current_label,
                "start_word": start,
                "end_word": end,
                "text": " ".join(words[start:end]),
            })

    for i, tag in enumerate(tags + ["O"]):

        if tag == "O":
            close(i)
            start = None
            current_label = None
            continue

        if "-" not in tag:
            raise ValueError(
                f"Invalid BIO tag: {tag}"
            )

        prefix, label = tag.split("-", 1)

        if prefix not in {"B", "I"}:
            raise ValueError(
                f"Invalid BIO prefix: {prefix}"
            )

        if label not in LABELS:
            raise ValueError(
                f"Unknown concept label: {label}"
            )

        if (
            prefix == "B"
            or label != current_label
            or start is None
        ):
            close(i)
            start = i
            current_label = label

    return spans


# --------------------------------------------------
# 3. Predict concepts using RoBERTa
# --------------------------------------------------

def predict_concepts(
    text,
    tokenizer,
    model,
    device,
):
    """
    Predict BIO labels using RoBERTa.

    Uses first-subword alignment, consistent with
    the RoBERTa training script.

    Converts predicted word spans back into
    original character offsets.
    """

    matches = list(
        TOKEN_PATTERN.finditer(text)
    )

    words = [
        match.group()
        for match in matches
    ]

    if not words:
        return []

    encoded = tokenizer(
        words,
        is_split_into_words=True,
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="pt",
    )

    word_ids = encoded.word_ids(
        batch_index=0
    )

    inputs = {
        "input_ids": encoded[
            "input_ids"
        ].to(device),

        "attention_mask": encoded[
            "attention_mask"
        ].to(device),
    }

    with torch.no_grad():
        outputs = model(**inputs)

        predictions = (
            outputs.logits
            .argmax(dim=-1)[0]
            .tolist()
        )

    tags = []
    seen = set()

    for i, word_id in enumerate(word_ids):

        if word_id is None:
            continue

        if word_id in seen:
            continue

        seen.add(word_id)

        predicted_id = int(
            predictions[i]
        )

        predicted_label = (
            model.config.id2label[
                predicted_id
            ]
        )

        tags.append(
            predicted_label
        )

    if len(tags) != len(words):
        raise ValueError(
            "Requirement was truncated. "
            "Check maximum sequence length."
        )

    predicted_spans = get_spans(
        words,
        tags,
    )

    results = []

    for span in predicted_spans:

        first = matches[
            span["start_word"]
        ]

        last = matches[
            span["end_word"] - 1
        ]

        start = first.start()
        end = last.end()

        results.append({
            "label": span["label"],
            "text": text[start:end],
            "start": start,
            "end": end,
        })

    return results


# --------------------------------------------------
# 4. Validate real-world dataset
# --------------------------------------------------

def load_real_world_dataset():

    if not TEST_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {TEST_PATH}"
        )

    with TEST_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError(
            "Real-world dataset must be a JSON list."
        )

    if not dataset:
        raise ValueError(
            "Real-world dataset is empty."
        )

    for example in dataset:

        requirement_id = example.get(
            "requirement_id",
            "UNKNOWN",
        )

        text = example.get("text")

        annotations = example.get(
            "annotations"
        )

        if not isinstance(text, str):
            raise ValueError(
                f"{requirement_id}: Invalid text."
            )

        if not isinstance(
            annotations,
            list,
        ):
            raise ValueError(
                f"{requirement_id}: "
                "Annotations must be a list."
            )

        previous_end = 0

        sorted_annotations = sorted(
            annotations,
            key=lambda item: item["start"],
        )

        for annotation in sorted_annotations:

            label = annotation["label"]
            start = annotation["start"]
            end = annotation["end"]

            if label not in LABELS:
                raise ValueError(
                    f"{requirement_id}: "
                    f"Unknown label {label}"
                )

            if (
                start < previous_end
                or start >= end
                or end > len(text)
            ):
                raise ValueError(
                    f"{requirement_id}: "
                    f"Invalid annotation boundaries: "
                    f"{annotation}"
                )

            actual_text = text[start:end]

            if actual_text != annotation["text"]:
                raise ValueError(
                    f"{requirement_id}: "
                    "Annotation text mismatch. "
                    f"Expected '{annotation['text']}', "
                    f"found '{actual_text}'."
                )

            previous_end = end

    return dataset


# --------------------------------------------------
# 5. Calculate evaluation metrics
# --------------------------------------------------

def calculate_metrics(counts):

    tp = counts["correct"]
    fn = counts["missing"]
    fp = counts["incorrect"]

    precision = (
        tp / (tp + fp)
        if tp + fp
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "correct": tp,
        "missing": fn,
        "incorrect": fp,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


# --------------------------------------------------
# 6. Main
# --------------------------------------------------

def main():

    print(
        "DesignTrace AI - Real-World "
        "RoBERTa Error Analysis"
    )

    print("-----------------------------------------")

    if not MODEL_DIR.exists():
        raise FileNotFoundError(
            f"Trained RoBERTa model not found: "
            f"{MODEL_DIR}"
        )

    print(
        "Loading real-world dataset..."
    )

    dataset = load_real_world_dataset()

    print(
        "Requirements:",
        len(dataset),
    )

    print(
        "Loading trained RoBERTa model..."
    )

    tokenizer = AutoTokenizer.from_pretrained(
        str(MODEL_DIR),
        use_fast=True,
        add_prefix_space=True,
    )

    if not tokenizer.is_fast:
        raise ValueError(
            "A fast tokenizer is required."
        )

    model = (
        AutoModelForTokenClassification
        .from_pretrained(
            str(MODEL_DIR)
        )
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    model.to(device)
    model.eval()

    print("Device:", device)

    summary = {
        label: Counter(
            correct=0,
            missing=0,
            incorrect=0,
        )
        for label in LABELS
    }

    errors = []

    print(
        "Analyzing real-world requirements..."
    )

    for example in dataset:

        text = example["text"]

        requirement_id = example[
            "requirement_id"
        ]

        gold = [
            {
                "label": ann["label"],
                "text": ann["text"],
                "start": ann["start"],
                "end": ann["end"],
            }
            for ann in example["annotations"]
        ]

        predicted = predict_concepts(
            text,
            tokenizer,
            model,
            device,
        )

        gold_set = {
            (
                item["start"],
                item["end"],
                item["label"],
            )
            for item in gold
        }

        predicted_set = {
            (
                item["start"],
                item["end"],
                item["label"],
            )
            for item in predicted
        }

        correct = (
            gold_set & predicted_set
        )

        missing = (
            gold_set - predicted_set
        )

        incorrect = (
            predicted_set - gold_set
        )

        for _, _, label in correct:
            summary[label]["correct"] += 1

        for _, _, label in missing:
            summary[label]["missing"] += 1

        for _, _, label in incorrect:
            summary[label]["incorrect"] += 1

        if missing or incorrect:

            errors.append({
                "requirement_id": requirement_id,
                "text": text,

                "missing": [
                    item
                    for item in gold
                    if (
                        item["start"],
                        item["end"],
                        item["label"],
                    ) in missing
                ],

                "incorrect": [
                    item
                    for item in predicted
                    if (
                        item["start"],
                        item["end"],
                        item["label"],
                    ) in incorrect
                ],
            })

    print(
        "\n================================"
    )
    print(
        "REAL-WORLD ERROR SUMMARY"
    )
    print(
        "================================"
    )

    print(
        "Requirements analyzed:",
        len(dataset),
    )

    print(
        "Requirements with errors:",
        len(errors),
    )

    detailed_summary = {}

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for label in LABELS:

        metrics = calculate_metrics(
            summary[label]
        )

        detailed_summary[label] = metrics

        total_tp += metrics["correct"]
        total_fp += metrics["incorrect"]
        total_fn += metrics["missing"]

        print(f"\n{label}")

        print(
            "Correct:",
            metrics["correct"],
        )

        print(
            "Missing:",
            metrics["missing"],
        )

        print(
            "Incorrect:",
            metrics["incorrect"],
        )

        print(
            f"Precision: "
            f"{metrics['precision']:.4f}"
        )

        print(
            f"Recall: "
            f"{metrics['recall']:.4f}"
        )

        print(
            f"F1-score: "
            f"{metrics['f1']:.4f}"
        )

    overall_metrics = calculate_metrics(
        {
            "correct": total_tp,
            "missing": total_fn,
            "incorrect": total_fp,
        }
    )

    print(
        "\nSTRICT SPAN-LEVEL METRICS"
    )

    print(
        f"Precision: "
        f"{overall_metrics['precision']:.4f}"
    )

    print(
        f"Recall: "
        f"{overall_metrics['recall']:.4f}"
    )

    print(
        f"F1-score: "
        f"{overall_metrics['f1']:.4f}"
    )

    print("\nEXAMPLE ERRORS")

    for error in errors[:10]:

        print(
            "\nRequirement:",
            error["requirement_id"],
        )

        print(
            "Text:",
            error["text"],
        )

        print(
            "Missing:",
            error["missing"],
        )

        print(
            "Incorrect:",
            error["incorrect"],
        )

    output = {
        "model": "roberta_project_split",
        "base_model": MODEL_NAME,
        "dataset": "real_world_test",
        "requirements_analyzed": len(dataset),
        "requirements_with_errors": len(errors),
        "summary": detailed_summary,
        "overall_metrics": overall_metrics,
        "errors": errors,
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
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        "\nResults saved to:",
        OUTPUT_PATH,
    )

    print(
        "RoBERTa error analysis "
        "completed successfully."
    )


if __name__ == "__main__":
    main()
