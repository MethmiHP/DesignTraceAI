# Evaluates and compares the trained FR/NFR classification models using the
# held-out test dataset. The script calculates accuracy, precision, recall,
# F1-score, confusion matrix, classification report, and inference time,
# then selects the best-performing model based on F1-score.

from pathlib import Path
import json
import time

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
)
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)


# PATHS

BASE_DIR = Path(__file__).resolve().parents[2]

TEST_FILE = (
    BASE_DIR
    / "training"
    / "requirement_analysis"
    / "prepared_data"
    / "fr_nfr_test.json"
)

MODEL_BASE_DIR = (
    BASE_DIR
    / "trained_models"
    / "requirement_analysis"
    / "fr_nfr"
)



# MODELS

MODELS = {
    "distilbert":
        MODEL_BASE_DIR
        / "distilbert"
        / "final",

    "bert":
        MODEL_BASE_DIR
        / "bert"
        / "final",

    "roberta":
        MODEL_BASE_DIR
        / "roberta"
        / "final",
}


LABEL_TO_ID = {
    "FR": 0,
    "NFR": 1,
}

ID_TO_LABEL = {
    0: "FR",
    1: "NFR",
}



# LOAD TEST DATA

def load_test_data():

    with TEST_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)



# EVALUATE ONE MODEL

def evaluate_model(
    model_key: str,
    model_path: Path,
    test_data: list[dict],
):

    print(
        "\n================================"
    )

    print(
        f"EVALUATING: {model_key}"
    )

    print(
        "================================"
    )

    tokenizer = (
        AutoTokenizer.from_pretrained(
            model_path
        )
    )

    model = (
        AutoModelForSequenceClassification
        .from_pretrained(
            model_path
        )
    )

    model.eval()

    texts = [
        item["text"]
        for item in test_data
    ]

    gold_labels = [
        LABEL_TO_ID[
            item["label"]
        ]
        for item in test_data
    ]

    predictions = []

    start_time = time.time()

    for index, text in enumerate(
        texts,
        start=1
    ):

        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128,
        )

        with torch.no_grad():

            outputs = model(
                **inputs
            )

        predicted_id = (
            torch.argmax(
                outputs.logits,
                dim=-1
            )
            .item()
        )

        predictions.append(
            predicted_id
        )

        if index % 25 == 0:

            print(
                f"Processed "
                f"{index}/{len(texts)}"
            )

    inference_time = (
        time.time()
        -
        start_time
    )


    # METRICS

    accuracy = accuracy_score(
        gold_labels,
        predictions
    )

    precision, recall, f1, _ = (
        precision_recall_fscore_support(
            gold_labels,
            predictions,
            average="weighted",
            zero_division=0,
        )
    )

    matrix = confusion_matrix(
        gold_labels,
        predictions
    )

    report = classification_report(
        gold_labels,
        predictions,
        target_names=[
            "FR",
            "NFR"
        ],
        digits=4,
        zero_division=0,
    )

    print(
        "\nAccuracy:",
        round(
            accuracy,
            4
        )
    )

    print(
        "Precision:",
        round(
            precision,
            4
        )
    )

    print(
        "Recall:",
        round(
            recall,
            4
        )
    )

    print(
        "F1:",
        round(
            f1,
            4
        )
    )

    print(
        "\nConfusion Matrix:"
    )

    print(
        matrix
    )

    print(
        "\nClassification Report:"
    )

    print(
        report
    )

    print(
        "Inference time:",
        round(
            inference_time,
            2
        ),
        "seconds"
    )

    return {
        "model":
            model_key,

        "accuracy":
            accuracy,

        "precision":
            precision,

        "recall":
            recall,

        "f1":
            f1,

        "inference_time":
            inference_time,
    }



# MAIN

if __name__ == "__main__":

    test_data = load_test_data()

    print(
        f"Test records: "
        f"{len(test_data)}"
    )

    all_results = []

    for model_key, model_path in (
        MODELS.items()
    ):

        result = evaluate_model(
            model_key,
            model_path,
            test_data,
        )

        all_results.append(
            result
        )

    print(
        "\n================================"
    )

    print(
        "FINAL MODEL COMPARISON"
    )

    print(
        "================================"
    )

    for result in all_results:

        print(
            f"\n{result['model']}"
        )

        print(
            f"Accuracy: "
            f"{result['accuracy']:.4f}"
        )

        print(
            f"Precision: "
            f"{result['precision']:.4f}"
        )

        print(
            f"Recall: "
            f"{result['recall']:.4f}"
        )

        print(
            f"F1: "
            f"{result['f1']:.4f}"
        )

        print(
            f"Inference time: "
            f"{result['inference_time']:.2f}s"
        )

    best_model = max(
        all_results,
        key=lambda x: x["f1"]
    )

    print(
        "\n================================"
    )

    print(
        "BEST MODEL"
    )

    print(
        "================================"
    )

    print(
        best_model["model"]
    )

    print(
        f"F1: "
        f"{best_model['f1']:.4f}"
    )