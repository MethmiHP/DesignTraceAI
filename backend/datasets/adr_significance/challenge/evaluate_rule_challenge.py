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


BACKEND_DIR = Path(__file__).resolve().parents[3]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from modules.adr.schemas import DesignDecision
from modules.adr.significance_detector import (
    ADRSignificanceDetector,
)


BASE_DIR = Path(__file__).resolve().parent

CHALLENGE_FILE = (
    BASE_DIR
    / "adr_significance_challenge.csv"
)


ORIGINAL_THRESHOLD = 0.40
CALIBRATED_THRESHOLD = 0.25


def load_rows(path):
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


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
        project_id="ADR-CHALLENGE-EVALUATION",
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


def evaluate_threshold(
    rows,
    scores,
    threshold,
    name,
):
    y_true = [
        int(row["label"])
        for row in rows
    ]

    y_pred = [
        1 if score >= threshold else 0
        for score in scores
    ]

    metrics = calculate_metrics(
        y_true,
        y_pred,
    )

    print()
    print(name)
    print("-" * len(name))

    print(
        f"Threshold: {threshold:.2f}"
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

    incorrect = []

    for row, score, predicted in zip(
        rows,
        scores,
        y_pred,
    ):
        expected = int(
            row["label"]
        )

        if expected != predicted:
            incorrect.append(
                {
                    "decision_id": row[
                        "decision_id"
                    ],
                    "source_module": row[
                        "source_module"
                    ],
                    "scenario_family": row[
                        "scenario_family"
                    ],
                    "expected": expected,
                    "predicted": predicted,
                    "score": score,
                }
            )

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
    rows = load_rows(
        CHALLENGE_FILE
    )

    detector = ADRSignificanceDetector()

    scores = []

    for row in rows:
        decision = build_decision(
            row
        )

        result = detector.evaluate(
            decision
        )

        scores.append(
            result.score
        )

    print()
    print(
        "ADR Hard Challenge Rule Evaluation"
    )
    print(
        "=================================="
    )

    print(
        f"Challenge records: {len(rows)}"
    )

    original_metrics = evaluate_threshold(
        rows,
        scores,
        ORIGINAL_THRESHOLD,
        "ORIGINAL RULE THRESHOLD",
    )

    calibrated_metrics = evaluate_threshold(
        rows,
        scores,
        CALIBRATED_THRESHOLD,
        "CALIBRATED RULE THRESHOLD",
    )

    print()
    print("Comparison")
    print("----------")

    print(
        f"Original threshold F1:   "
        f"{original_metrics['f1']:.4f}"
    )

    print(
        f"Calibrated threshold F1: "
        f"{calibrated_metrics['f1']:.4f}"
    )


if __name__ == "__main__":
    main()