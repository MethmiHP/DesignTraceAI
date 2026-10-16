"""
Evaluate the existing ADR deterministic significance detector
against the frozen group-aware validation and test datasets.

This compares the existing rule-based ADR significance logic
against the same labels used for the ML baselines.

No model training occurs here.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import csv
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from modules.adr.schemas import DesignDecision
from modules.adr.significance_detector import (
    ADRSignificanceDetector,
)


BASE_DIR = Path(__file__).resolve().parent

SPLIT_DIR = BASE_DIR / "splits"

VALIDATION_PATH = (
    SPLIT_DIR
    / "validation.csv"
)

TEST_PATH = (
    SPLIT_DIR
    / "test.csv"
)


def load_rows(path):
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def split_pipe(value):
    if not value:
        return []

    return [
        item.strip()
        for item in value.split("|")
        if item.strip()
    ]


def build_decision(row):
    """
    Convert a dataset row into the DesignDecision contract
    expected by the ADR significance detector.
    """

    return DesignDecision(
        decision_id=row["decision_id"],
        project_id="ADR-SIGNIFICANCE-EVALUATION",
        source_module=row["source_module"],
        title=row["title"],
        context=row["context"],
        decision=row["decision"],
        rationale=row.get(
            "rationale",
            "",
        ),
        alternatives=split_pipe(
            row.get(
                "alternatives",
                "",
            )
        ),
        trade_offs=split_pipe(
            row.get(
                "trade_offs",
                "",
            )
        ),
        requirement_ids=split_pipe(
            row.get(
                "requirement_ids",
                "",
            )
        ),
        design_element_ids=split_pipe(
            row.get(
                "design_element_ids",
                "",
            )
        ),
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
        ),
    }


def evaluate_split(
    name,
    rows,
    detector,
):
    y_true = []
    y_pred = []

    prediction_details = []

    for row in rows:
        decision = build_decision(
            row
        )

        result = detector.evaluate(
            decision
        )

        expected = int(
            row["label"]
        )

        predicted = (
            1
            if result.significant
            else 0
        )

        y_true.append(
            expected
        )

        y_pred.append(
            predicted
        )

        prediction_details.append(
            {
                "decision_id": row[
                    "decision_id"
                ],
                "scenario_family": row[
                    "scenario_family"
                ],
                "expected": expected,
                "predicted": predicted,
                "score": result.score,
                "correct": (
                    expected == predicted
                ),
            }
        )

    metrics = calculate_metrics(
        y_true,
        y_pred,
    )

    print()
    print(name)
    print("-" * len(name))

    print(
        f"Records:   "
        f"{len(rows)}"
    )

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

    incorrect = [
        item
        for item in prediction_details
        if not item["correct"]
    ]

    print()
    print(
        f"Incorrect predictions: "
        f"{len(incorrect)}"
    )

    if incorrect:
        print()
        print("Misclassified examples")
        print("----------------------")

        for item in incorrect:
            print(
                f"{item['decision_id']} | "
                f"{item['scenario_family']} | "
                f"expected={item['expected']} | "
                f"predicted={item['predicted']} | "
                f"score={item['score']:.4f}"
            )

    return metrics


def main():
    validation_rows = load_rows(
        VALIDATION_PATH
    )

    test_rows = load_rows(
        TEST_PATH
    )

    detector = (
        ADRSignificanceDetector()
    )

    print()
    print(
        "ADR Deterministic Significance "
        "Detector Evaluation"
    )
    print(
        "========================================="
    )

    print(
        f"Validation records: "
        f"{len(validation_rows)}"
    )

    print(
        f"Test records: "
        f"{len(test_rows)}"
    )

    evaluate_split(
        "VALIDATION RESULTS",
        validation_rows,
        detector,
    )

    evaluate_split(
        "TEST RESULTS",
        test_rows,
        detector,
    )


if __name__ == "__main__":
    main()