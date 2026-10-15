"""
DesignTrace AI - Project-Independent RoBERTa Test Evaluation
===========================================================

Evaluates the trained RoBERTa model on the
project-independent test dataset.

Model:
    outputs/nlp_models/roberta_project_split/

Dataset:
    datasets/nlp/project_split/roberta/test_aligned.json

Reports:
    1. Overall Precision
    2. Overall Recall
    3. Overall F1-score
    4. Per-label results for ENTITY, ATTRIBUTE, ACTION

Output:
    outputs/nlp_models/roberta_project_split/
        project_test_metrics.json
"""

import json
from pathlib import Path
import numpy as np

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
    / "project_split"
    / "roberta"
    / "test_aligned.json"
)

OUTPUT_PATH = MODEL_DIR / "project_test_metrics.json"

EXPECTED_LABELS = {
    "O",
    "B-ENTITY",
    "I-ENTITY",
    "B-ATTRIBUTE",
    "I-ATTRIBUTE",
    "B-ACTION",
    "I-ACTION",
}


# --------------------------------------------------
# 2. Load test dataset
# --------------------------------------------------

def load_test_dataset():

    if not TEST_PATH.exists():
        raise FileNotFoundError(
            f"Test dataset not found: {TEST_PATH}"
        )

    with TEST_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list) or not data:
        raise ValueError(
            "Test dataset must contain a non-empty JSON list."
        )

    required_fields = {
        "input_ids",
        "attention_mask",
        "labels",
    }

    for index, example in enumerate(data):

        missing = required_fields - example.keys()

        if missing:
            raise ValueError(
                f"Example {index}: missing fields {missing}"
            )

        lengths = [
            len(example["input_ids"]),
            len(example["attention_mask"]),
            len(example["labels"]),
        ]

        if len(set(lengths)) != 1:
            raise ValueError(
                f"Example {index}: input_ids, "
                "attention_mask and labels "
                "must have equal lengths."
            )

    return data


# --------------------------------------------------
# 3. Evaluate RoBERTa
# --------------------------------------------------

def evaluate(test_data, model, device):

    all_predictions = []
    all_actual = []

    id2label = {
        int(key): value
        for key, value in model.config.id2label.items()
    }

    valid_ids = set(id2label)

    for example_index, example in enumerate(test_data):

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
            outputs.logits.argmax(dim=-1)[0].tolist()
        )

        actual_ids = example["labels"]

        predicted_tags = []
        actual_tags = []

        for predicted_id, actual_id in zip(
            predicted_ids,
            actual_ids,
        ):

            if actual_id == -100:
                continue

            if actual_id not in valid_ids:
                raise ValueError(
                    f"Example {example_index}: "
                    f"unknown label ID {actual_id}"
                )

            predicted_tags.append(
                id2label[int(predicted_id)]
            )

            actual_tags.append(
                id2label[int(actual_id)]
            )

        all_predictions.append(predicted_tags)
        all_actual.append(actual_tags)

    precision = precision_score(
        all_actual,
        all_predictions,
        zero_division=0,
    )

    recall = recall_score(
        all_actual,
        all_predictions,
        zero_division=0,
    )

    f1 = f1_score(
        all_actual,
        all_predictions,
        zero_division=0,
    )

    report_text = classification_report(
        all_actual,
        all_predictions,
        zero_division=0,
    )

    report_dict = classification_report(
        all_actual,
        all_predictions,
        output_dict=True,
        zero_division=0,
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "report_text": report_text,
        "report_dict": report_dict,
    }

def convert_to_json_serializable(obj):
    """
    Convert NumPy values into standard Python values
    so they can be saved as JSON.
    """

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, np.ndarray):
        return obj.tolist()

    if isinstance(obj, dict):
        return {
            key: convert_to_json_serializable(value)
            for key, value in obj.items()
        }

    if isinstance(obj, (list, tuple)):
        return [
            convert_to_json_serializable(value)
            for value in obj
        ]

    return obj


# --------------------------------------------------
# 4. Main
# --------------------------------------------------

def main():

    print(
        "DesignTrace AI - Project-Independent RoBERTa Evaluation"
    )
    print("-----------------------------------------------")

    if not MODEL_DIR.exists():
        raise FileNotFoundError(
            f"Trained model not found: {MODEL_DIR}"
        )

    print("Loading test dataset...")

    test_data = load_test_dataset()

    print("Test Requirements:", len(test_data))

    print("Loading trained RoBERTa model...")

    tokenizer = AutoTokenizer.from_pretrained(
        str(MODEL_DIR),
        use_fast=True,
        add_prefix_space=True,
    )

    model = AutoModelForTokenClassification.from_pretrained(
        str(MODEL_DIR)
    )

    model_labels = set(model.config.label2id)

    if model_labels != EXPECTED_LABELS:
        raise ValueError(
            "Model BIO labels do not match "
            "the expected ENTITY, ATTRIBUTE, ACTION labels."
        )

    # The aligned dataset was generated using
    # the roberta-base tokenizer.
    # Use the same tokenizer configuration
    # during training and evaluation.
    if tokenizer.name_or_path == "":
        raise ValueError(
            "Tokenizer could not be loaded correctly."
        )

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    model.to(device)
    model.eval()

    print("Device:", device)
    print("Evaluating on unseen project test data...")

    metrics = evaluate(
        test_data,
        model,
        device,
    )

    print("\n================================")
    print("PROJECT-INDEPENDENT TEST RESULTS")
    print("================================")

    print("Test Requirements:", len(test_data))

    print(
        f"Precision: {metrics['precision']:.4f}"
    )

    print(
        f"Recall:    {metrics['recall']:.4f}"
    )

    print(
        f"F1-score:  {metrics['f1']:.4f}"
    )

    print("\nPer-label Results:")
    print(metrics["report_text"])

    results = {
    "model": "roberta_project_split",
    "base_model": "roberta-base",
    "dataset": "project_independent_test",
    "test_requirements": len(test_data),
    "precision": metrics["precision"],
    "recall": metrics["recall"],
    "f1": metrics["f1"],
    "per_label_results": metrics["report_dict"],
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
            convert_to_json_serializable(results),
            file,
            indent=2,
        )

    print("\nResults saved to:", OUTPUT_PATH)
    print("Evaluation completed successfully.")


if __name__ == "__main__":
    main()
