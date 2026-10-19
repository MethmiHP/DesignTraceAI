import csv
import pickle
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


BASE_DIR = Path(__file__).resolve().parent

CHALLENGE_FILE = (
    BASE_DIR
    / "adr_significance_challenge.csv"
)

MODEL_FILE = (
    BASE_DIR.parent
    / "models"
    / "tfidf_logreg"
    / "model.pkl"
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


def build_text(row):
    """
    Match the full TF-IDF training representation.
    """

    return " ".join(
        [
            row.get("title", ""),
            row.get("context", ""),
            row.get("decision", ""),
            row.get("rationale", ""),
            row.get("alternatives", ""),
            row.get("trade_offs", ""),
        ]
    ).strip()


def main():
    rows = load_rows(
        CHALLENGE_FILE
    )

    with MODEL_FILE.open(
        "rb"
    ) as file:
        model = pickle.load(
            file
        )

    texts = [
        build_text(row)
        for row in rows
    ]

    y_true = [
        int(row["label"])
        for row in rows
    ]

    y_pred = model.predict(
        texts
    )

    probabilities = None

    if hasattr(
        model,
        "predict_proba",
    ):
        probabilities = model.predict_proba(
            texts
        )[:, 1]

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
    )

    print()
    print(
        "ADR Hard Challenge TF-IDF Evaluation"
    )
    print(
        "===================================="
    )

    print(
        f"Challenge records: {len(rows)}"
    )

    print(
        "Model: full TF-IDF + Logistic Regression"
    )

    print(
        "Training performed: NO"
    )

    print()
    print(
        f"Accuracy:  {accuracy:.4f}"
    )

    print(
        f"Precision: {precision:.4f}"
    )

    print(
        f"Recall:    {recall:.4f}"
    )

    print(
        f"F1:        {f1:.4f}"
    )

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

    for index, row in enumerate(rows):
        expected = y_true[index]
        predicted = int(
            y_pred[index]
        )

        if expected != predicted:
            item = {
                "decision_id": row[
                    "decision_id"
                ],
                "scenario_family": row[
                    "scenario_family"
                ],
                "expected": expected,
                "predicted": predicted,
            }

            if probabilities is not None:
                item["probability"] = float(
                    probabilities[index]
                )

            incorrect.append(
                item
            )

    print()
    print(
        f"Incorrect predictions: "
        f"{len(incorrect)}"
    )

    if incorrect:
        print()
        print(
            "Misclassified examples"
        )
        print(
            "----------------------"
        )

        for item in incorrect:
            line = (
                f"{item['decision_id']} | "
                f"{item['scenario_family']} | "
                f"expected={item['expected']} | "
                f"predicted={item['predicted']}"
            )

            if "probability" in item:
                line += (
                    f" | significant_probability="
                    f"{item['probability']:.4f}"
                )

            print(line)


if __name__ == "__main__":
    main()