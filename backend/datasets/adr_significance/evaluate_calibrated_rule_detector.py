"""
Evaluate the deterministic ADR significance detector using the
threshold selected from the validation set.

Selected threshold:
    0.25

IMPORTANT:
The threshold was selected using validation data only.
This script evaluates that frozen threshold on both validation
and test data without further tuning.
"""

import csv
import sys
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


BACKEND_DIR = Path(__file__).resolve().parents[2]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from modules.adr.schemas import DesignDecision
from modules.adr.significance_detector import (
    ADRSignificanceDetector,
)


BASE_DIR = Path(__file__).resolve().parent

VALIDATION_PATH = (
    BASE_DIR
    / "splits"
    / "validation.csv"
)

TEST_PATH = (
    BASE_DIR
    / "splits"
    / "test.csv"
)


SELECTED_THRESHOLD = 0.25


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
    return DesignDecision(
        decision_id=row["decision_id"],
        project_id="ADR-CALIBRATED-RULE-EVALUATION",
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

        # IMPORTANT:
        # Ignore result.significant here because it uses the
        # detector's original internal threshold.
        #
        # Use the validation-selected threshold instead.
        predicted = (
            1
            if result.score >= SELECTED_THRESHOLD
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
        f"Threshold: {SELECTED_THRESHOLD:.2f}"
    )

    print(
        f"Records:   {len(rows)}"
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
        if item["expected"]
        != item["predicted"]
    ]

    print()
    print(
        f"Incorrect predictions: "
        f"{len(incorrect)}"
    )

    if incorrect:
        print()
        print("Misclassified scenario families")
        print("-------------------------------")

        seen = set()

        for item in incorrect:
            family = item[
                "scenario_family"
            ]

            if family in seen:
                continue

            seen.add(
                family
            )

            print(
                f"{family:<35} "
                f"expected={item['expected']} "
                f"predicted={item['predicted']} "
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
        "ADR Calibrated Rule Detector Evaluation"
    )

    print(
        "======================================="
    )

    print(
        f"Validation-selected threshold: "
        f"{SELECTED_THRESHOLD:.2f}"
    )

    print()
    print(
        "Threshold selection source: "
        "validation split only"
    )

    validation_metrics = evaluate_split(
        "VALIDATION RESULTS",
        validation_rows,
        detector,
    )

    test_metrics = evaluate_split(
        "TEST RESULTS",
        test_rows,
        detector,
    )

    print()
    print("Comparison")
    print("----------")

    print(
        "Original rule threshold: 0.40"
    )

    print(
        "Original validation F1:   0.7000"
    )

    print(
        "Original test F1:         0.5882"
    )

    print()

    print(
        f"Calibrated validation F1: "
        f"{validation_metrics['f1']:.4f}"
    )

    print(
        f"Calibrated test F1:       "
        f"{test_metrics['f1']:.4f}"
    )


if __name__ == "__main__":
    main()