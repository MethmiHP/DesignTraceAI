"""
DesignTrace AI - Real-World RoBERTa Evaluation
==========================================

Evaluates the trained project-split RoBERTa model
on manually annotated real-world requirements.

Input:
    datasets/nlp/real_world_test.json

Model:
    outputs/nlp_models/roberta_project_split/

Output:
    outputs/nlp_models/roberta_project_split/
    real_world_test_metrics.json

Metrics:
    Strict entity-level Precision, Recall and F1
    Per-label classification report
"""

import json
from pathlib import Path

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
)
from seqeval.metrics import (
    classification_report,
    precision_score,
    recall_score,
    f1_score,
)


# ------------------------------------------
# 1. Paths and configuration
# ------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    BASE_DIR / "outputs" / "nlp_models"
    / "roberta_project_split"
)

DATA_DIR = BASE_DIR / "datasets" / "nlp"

REAL_WORLD_TEST_PATH = (
    BASE_DIR / "datasets" / "nlp"
    / "real_world_test.json"
)

OUTPUT_PATH = (
    MODEL_DIR / "real_world_test_metrics.json"
)

VALID_LABELS = {"ENTITY", "ATTRIBUTE", "ACTION"}


# ------------------------------------------
# 2. Load real-world dataset
# ------------------------------------------

def load_real_world_test():

    if not REAL_WORLD_TEST_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {REAL_WORLD_TEST_PATH}"
        )

    with open(
        REAL_WORLD_TEST_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, list) or not data:
        raise ValueError(
            "real_world_test.json must contain "
            "a non-empty JSON list."
        )

    return data


# ------------------------------------------
# 3. Prepare annotated requirements
# ------------------------------------------

def prepare_real_world_test(
    data,
    tokenizer,
    label2id,
):
    """
    Converts character-level annotations to
    BIO labels using the same first-subword
    strategy used during RoBERTa training.
    """

    prepared = []

    for example in data:

        requirement_id = example["requirement_id"]
        text = example["text"]

        annotations = sorted(
            example.get("annotations", []),
            key=lambda item: item["start"],
        )

        previous_end = 0

        # Validate annotations.
        for annotation in annotations:

            start = annotation["start"]
            end = annotation["end"]
            label = annotation["label"]

            if label not in VALID_LABELS:
                raise ValueError(
                    f"{requirement_id}: "
                    f"Unsupported label {label}"
                )

            if (
                not isinstance(start, int)
                or not isinstance(end, int)
                or start < previous_end
                or end > len(text)
                or start >= end
                or text[start:end] != annotation["text"]
            ):
                raise ValueError(
                    f"{requirement_id}: "
                    f"Invalid annotation {annotation}"
                )

            previous_end = end

        # Tokenize as words first, matching
        # the project's BIO conversion pipeline.
        import re

        token_matches = list(
            re.finditer(
                r"\w+|[^\w\s]",
                text,
                re.UNICODE,
            )
        )

        words = [
            match.group()
            for match in token_matches
        ]

        word_labels = ["O"] * len(words)
        occupied = set()

        for annotation in annotations:

            matching = [
                i
                for i, match in enumerate(token_matches)
                if (
                    match.start() >= annotation["start"]
                    and match.end() <= annotation["end"]
                )
            ]

            overlapping = [
                i
                for i, match in enumerate(token_matches)
                if (
                    match.start() < annotation["end"]
                    and match.end() > annotation["start"]
                )
            ]

            if not matching or matching != overlapping:
                raise ValueError(
                    f"{requirement_id}: "
                    f"Annotation does not align "
                    f"with word tokens: {annotation}"
                )

            if any(i in occupied for i in matching):
                raise ValueError(
                    f"{requirement_id}: "
                    "Overlapping annotations."
                )

            for position, index in enumerate(matching):

                prefix = (
                    "B" if position == 0 else "I"
                )

                word_labels[index] = (
                    f"{prefix}-{annotation['label']}"
                )

                occupied.add(index)

        encoding = tokenizer(
            words,
            is_split_into_words=True,
            truncation=True,
            max_length=128,
        )

        word_ids = encoding.word_ids()

        aligned_labels = []
        previous_word_id = None

        for word_id in word_ids:

            if word_id is None:
                aligned_labels.append(-100)

            elif word_id != previous_word_id:
                aligned_labels.append(
                    label2id[word_labels[word_id]]
                )

            else:
                aligned_labels.append(-100)

            previous_word_id = word_id

        if len(set(word_ids) - {None}) != len(words):
            raise ValueError(
                f"{requirement_id}: "
                "Requirement was truncated. "
                "Increase max_length consistently "
                "with training before evaluation."
            )

        prepared.append({
            "requirement_id": requirement_id,
            "input_ids": encoding["input_ids"],
            "attention_mask": encoding["attention_mask"],
            "labels": aligned_labels,
        })

    return prepared


# ------------------------------------------
# 4. Evaluate RoBERTa
# ------------------------------------------

def evaluate(test_data, model, device):

    all_predictions = []
    all_actual = []

    id2label = {
        int(key): value
        for key, value
        in model.config.id2label.items()
    }

    for example in test_data:

        input_ids = torch.tensor(
            [example["input_ids"]],
            dtype=torch.long,
            device=device,
        )

        attention_mask = torch.tensor(
            [example["attention_mask"]],
            dtype=torch.long,
            device=device,
        )

        with torch.no_grad():

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

        predicted_ids = (
            outputs.logits
            .argmax(dim=-1)[0]
            .tolist()
        )

        predicted_tags = []
        actual_tags = []

        for predicted_id, actual_id in zip(
            predicted_ids,
            example["labels"],
        ):

            if actual_id == -100:
                continue

            predicted_tags.append(
                id2label[int(predicted_id)]
            )

            actual_tags.append(
                id2label[int(actual_id)]
            )

        all_predictions.append(predicted_tags)
        all_actual.append(actual_tags)

    report_dict = classification_report(
        all_actual,
        all_predictions,
        output_dict=True,
        zero_division=0,
    )

    report_text = classification_report(
        all_actual,
        all_predictions,
        zero_division=0,
    )

    return {
        "precision": float(
            precision_score(
                all_actual,
                all_predictions,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                all_actual,
                all_predictions,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                all_actual,
                all_predictions,
                zero_division=0,
            )
        ),
        "report": report_text,
        "per_label_results": report_dict,
    }


# ------------------------------------------
# 5. Main
# ------------------------------------------

def main():

    print(
        "DesignTrace AI - Real-World RoBERTa Evaluation"
    )
    print("------------------------------------------")

    print("Loading real-world dataset...")

    raw_data = load_real_world_test()

    print("Requirements:", len(raw_data))

    print("Loading trained RoBERTa model...")

    tokenizer = AutoTokenizer.from_pretrained(
        str(MODEL_DIR),
        use_fast=True,
        add_prefix_space=True,
    )

    model = (
        AutoModelForTokenClassification
        .from_pretrained(str(MODEL_DIR))
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    model.to(device)
    model.eval()

    print("Device:", device)

    print("Preparing annotated requirements...")

    test_data = prepare_real_world_test(
        raw_data,
        tokenizer,
        model.config.label2id,
    )

    print("Evaluating real-world requirements...")

    metrics = evaluate(
        test_data,
        model,
        device,
    )

    print("\n===================================")
    print("REAL-WORLD TEST RESULTS")
    print("===================================")

    print("Test Requirements:", len(test_data))

    print(
        f"Precision: {metrics['precision']:.4f}"
    )

    print(
        f"Recall: {metrics['recall']:.4f}"
    )

    print(
        f"F1-score: {metrics['f1']:.4f}"
    )

    print("\nPer-label Results:")
    print(metrics["report"])

    results = {
        "model": "roberta_project_split",
        "base_model": "roberta-base",
        "dataset": "real_world_test",
        "test_requirements": len(test_data),
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "per_label_results": metrics[
            "per_label_results"
        ],
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
            default=lambda obj: obj.item() if hasattr(obj, "item") else str(obj),
        )

    print("\nResults saved to:", OUTPUT_PATH)

    print(
        "Real-world evaluation completed successfully."
    )


if __name__ == "__main__":
    main()
