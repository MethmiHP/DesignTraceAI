"""
Train and evaluate a TF-IDF + Logistic Regression baseline
for ADR significance classification.

Training features:
- title
- context
- decision
- rationale
- alternatives
- trade_offs

Metadata such as:
- scenario_family
- difficulty
- domain
- requirement_ids
- design_element_ids
- review_status

is intentionally NOT used as predictive input.

Outputs:
- validation metrics
- test metrics
- confusion matrices
- trained model pipeline
"""

import json
import pickle
from pathlib import Path

import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline


BASE_DIR = Path(__file__).resolve().parent

SPLIT_DIR = BASE_DIR / "splits"

TRAIN_PATH = SPLIT_DIR / "train.csv"
VALIDATION_PATH = SPLIT_DIR / "validation.csv"
TEST_PATH = SPLIT_DIR / "test.csv"

MODEL_DIR = BASE_DIR / "models" / "tfidf_logreg"

MODEL_PATH = MODEL_DIR / "model.pkl"
RESULTS_PATH = MODEL_DIR / "metrics.json"


TEXT_COLUMNS = [
    "title",
    "context",
    "decision",
    "rationale",
    "alternatives",
    "trade_offs",
]


def load_split(path):
    return pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
    )


def build_text(row):
    """
    Build the classifier input from natural-language decision evidence.
    """

    parts = []

    for column in TEXT_COLUMNS:
        value = str(
            row.get(
                column,
                "",
            )
        ).strip()

        if value:
            parts.append(
                value
            )

    return " ".join(
        parts
    )


def prepare_xy(dataframe):
    texts = dataframe.apply(
        build_text,
        axis=1,
    ).tolist()

    labels = (
        dataframe["label"]
        .astype(int)
        .tolist()
    )

    return texts, labels


def build_pipeline():
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def calculate_metrics(
    y_true,
    y_pred,
):
    return {
        "accuracy": accuracy_score(
            y_true,
            y_pred,
        ),
        "precision": precision_score(
            y_true,
            y_pred,
            zero_division=0,
        ),
        "recall": recall_score(
            y_true,
            y_pred,
            zero_division=0,
        ),
        "f1": f1_score(
            y_true,
            y_pred,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(
            y_true,
            y_pred,
        ).tolist(),
        "classification_report": (
            classification_report(
                y_true,
                y_pred,
                output_dict=True,
                zero_division=0,
            )
        ),
    }


def print_metrics(
    name,
    metrics,
):
    print()
    print(name)
    print("-" * len(name))

    print(
        f"Accuracy:  "
        f"{metrics['accuracy']:.4f}"
    )

    print(
        f"Precision: "
        f"{metrics['precision']:.4f}"
    )

    print(
        f"Recall:    "
        f"{metrics['recall']:.4f}"
    )

    print(
        f"F1:        "
        f"{metrics['f1']:.4f}"
    )

    matrix = metrics[
        "confusion_matrix"
    ]

    print()
    print("Confusion Matrix")
    print(
        "                 Pred 0   Pred 1"
    )
    print(
        f"Actual 0         "
        f"{matrix[0][0]:>6}   "
        f"{matrix[0][1]:>6}"
    )
    print(
        f"Actual 1         "
        f"{matrix[1][0]:>6}   "
        f"{matrix[1][1]:>6}"
    )


def main():
    train_df = load_split(
        TRAIN_PATH
    )

    validation_df = load_split(
        VALIDATION_PATH
    )

    test_df = load_split(
        TEST_PATH
    )

    (
        x_train,
        y_train,
    ) = prepare_xy(
        train_df
    )

    (
        x_validation,
        y_validation,
    ) = prepare_xy(
        validation_df
    )

    (
        x_test,
        y_test,
    ) = prepare_xy(
        test_df
    )

    print()
    print("ADR Significance TF-IDF + Logistic Regression")
    print("==============================================")

    print(
        f"Training records:   "
        f"{len(x_train)}"
    )

    print(
        f"Validation records: "
        f"{len(x_validation)}"
    )

    print(
        f"Test records:       "
        f"{len(x_test)}"
    )

    pipeline = build_pipeline()

    print()
    print(
        "Training model..."
    )

    pipeline.fit(
        x_train,
        y_train,
    )

    validation_predictions = (
        pipeline.predict(
            x_validation
        )
    )

    test_predictions = (
        pipeline.predict(
            x_test
        )
    )

    validation_metrics = (
        calculate_metrics(
            y_validation,
            validation_predictions,
        )
    )

    test_metrics = (
        calculate_metrics(
            y_test,
            test_predictions,
        )
    )

    print_metrics(
        "VALIDATION RESULTS",
        validation_metrics,
    )

    print_metrics(
        "TEST RESULTS",
        test_metrics,
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with MODEL_PATH.open(
        "wb"
    ) as file:
        pickle.dump(
            pipeline,
            file,
        )

    results = {
        "model": (
            "TF-IDF + Logistic Regression"
        ),
        "random_seed": 42,
        "text_features": TEXT_COLUMNS,
        "train_records": len(
            x_train
        ),
        "validation_records": len(
            x_validation
        ),
        "test_records": len(
            x_test
        ),
        "validation": (
            validation_metrics
        ),
        "test": (
            test_metrics
        ),
    }

    RESULTS_PATH.write_text(
        json.dumps(
            results,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        f"Model saved to: "
        f"{MODEL_PATH}"
    )

    print(
        f"Metrics saved to: "
        f"{RESULTS_PATH}"
    )


if __name__ == "__main__":
    main()