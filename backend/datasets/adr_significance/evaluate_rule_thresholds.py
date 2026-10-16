"""
Evaluate different thresholds for the deterministic ADR significance detector.

Uses the validation split to inspect threshold behaviour.
The test split must not be used to choose the threshold.
"""

import csv
import sys
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

BACKEND_DIR = Path(__file__).resolve().parents[2]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from modules.adr.schemas import DesignDecision
from modules.adr.significance_detector import ADRSignificanceDetector


BASE_DIR = Path(__file__).resolve().parent

VALIDATION_PATH = (
    BASE_DIR
    / "splits"
    / "validation.csv"
)


THRESHOLDS = [
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
]


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
        project_id="ADR-THRESHOLD-EVALUATION",
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


def main():
    rows = load_rows(
        VALIDATION_PATH
    )

    detector = ADRSignificanceDetector()

    scores = []
    labels = []

    for row in rows:
        result = detector.evaluate(
            build_decision(row)
        )

        scores.append(
            result.score
        )

        labels.append(
            int(row["label"])
        )

    print()
    print("ADR Rule Threshold Evaluation")
    print("=============================")

    print()
    print(
        f"{'Threshold':<12}"
        f"{'Accuracy':<12}"
        f"{'Precision':<12}"
        f"{'Recall':<12}"
        f"{'F1':<12}"
    )

    best_threshold = None
    best_f1 = -1

    for threshold in THRESHOLDS:
        predictions = [
            1 if score >= threshold else 0
            for score in scores
        ]

        accuracy = accuracy_score(
            labels,
            predictions,
        )

        precision = precision_score(
            labels,
            predictions,
            zero_division=0,
        )

        recall = recall_score(
            labels,
            predictions,
            zero_division=0,
        )

        f1 = f1_score(
            labels,
            predictions,
            zero_division=0,
        )

        print(
            f"{threshold:<12.2f}"
            f"{accuracy:<12.4f}"
            f"{precision:<12.4f}"
            f"{recall:<12.4f}"
            f"{f1:<12.4f}"
        )

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold

    print()
    print(
        f"Best validation threshold: "
        f"{best_threshold:.2f}"
    )

    print(
        f"Best validation F1: "
        f"{best_f1:.4f}"
    )

    print()
    print(
        "Important: choose the threshold using "
        "validation data only."
    )


if __name__ == "__main__":
    main()