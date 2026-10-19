# Evaluates and compares trained NFR quality-attribute classification models
# on the same held-out test dataset using accuracy, weighted and macro metrics,
# confusion matrices, classification reports, and inference time, then selects
# the best-performing model based on Macro F1-score.

from pathlib import Path
import json
import time

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
    / "nfr_category_test.json"
)

MODEL_BASE_DIR = (
    BASE_DIR
    / "trained_models"
    / "requirement_analysis"
    / "nfr_category"
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

    "roberta_balanced":
        MODEL_BASE_DIR
        / "roberta_balanced"
        / "final",  

    "roberta_balanced_augmented":
        MODEL_BASE_DIR
        / "roberta_balanced_augmented"
        / "final",  

}



# LABELS

NFR_LABELS = [
    "Availability",
    "Fault Tolerance",
    "Legal",
    "Look and Feel",
    "Maintainability",
    "Operational",
    "Performance",
    "Portability",
    "Scalability",
    "Security",
    "Usability",
]


LABEL_TO_ID = {
    label: index
    for index, label in enumerate(NFR_LABELS)
}


ID_TO_LABEL = {
    index: label
    for label, index in LABEL_TO_ID.items()
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
        f"EVALUATING NFR MODEL: {model_key}"
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

        if index % 20 == 0:

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

    weighted_precision, weighted_recall, weighted_f1, _ = (
        precision_recall_fscore_support(
            gold_labels,
            predictions,
            average="weighted",
            zero_division=0,
        )
    )

    macro_precision, macro_recall, macro_f1, _ = (
        precision_recall_fscore_support(
            gold_labels,
            predictions,
            average="macro",
            zero_division=0,
        )
    )

    matrix = confusion_matrix(
        gold_labels,
        predictions,
        labels=list(
            range(
                len(NFR_LABELS)
            )
        )
    )

    report = classification_report(
        gold_labels,
        predictions,
        labels=list(
            range(
                len(NFR_LABELS)
            )
        ),
        target_names=NFR_LABELS,
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
        "Weighted Precision:",
        round(
            weighted_precision,
            4
        )
    )

    print(
        "Weighted Recall:",
        round(
            weighted_recall,
            4
        )
    )

    print(
        "Weighted F1:",
        round(
            weighted_f1,
            4
        )
    )

    print(
        "\nMacro Precision:",
        round(
            macro_precision,
            4
        )
    )

    print(
        "Macro Recall:",
        round(
            macro_recall,
            4
        )
    )

    print(
        "Macro F1:",
        round(
            macro_f1,
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

        "weighted_precision":
            weighted_precision,

        "weighted_recall":
            weighted_recall,

        "weighted_f1":
            weighted_f1,

        "macro_precision":
            macro_precision,

        "macro_recall":
            macro_recall,

        "macro_f1":
            macro_f1,

        "inference_time":
            inference_time,
    }


# MAIN

if __name__ == "__main__":

    test_data = load_test_data()

    print(
        f"NFR test records: "
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


    # FINAL COMPARISON

    print(
        "\n================================"
    )

    print(
        "FINAL NFR MODEL COMPARISON"
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
            f"Weighted F1: "
            f"{result['weighted_f1']:.4f}"
        )

        print(
            f"Macro F1: "
            f"{result['macro_f1']:.4f}"
        )

        print(
            f"Inference time: "
            f"{result['inference_time']:.2f}s"
        )


    # BEST MODEL

    # For NFR category classification,
    # use Macro F1 because the classes are imbalanced.

    best_model = max(
        all_results,
        key=lambda x: x["macro_f1"]
    )

    print(
        "\n================================"
    )

    print(
        "BEST NFR MODEL"
    )

    print(
        "================================"
    )

    print(
        best_model["model"]
    )

    print(
        f"Macro F1: "
        f"{best_model['macro_f1']:.4f}"
    )

    print(
        f"Weighted F1: "
        f"{best_model['weighted_f1']:.4f}"
    )

    print(
        f"Accuracy: "
        f"{best_model['accuracy']:.4f}"
    )