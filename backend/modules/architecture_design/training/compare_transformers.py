"""
Milestone 7.1C

Compare supervised transformer models using their final held-out
test metrics.

This script does not train models.
"""

from __future__ import annotations

import json
from pathlib import Path


BACKEND_DIR = (
    Path(__file__)
    .resolve()
    .parents[3]
)

OUTPUT_ROOT = (
    BACKEND_DIR
    / "outputs"
    / "architecture_models"
)


MODEL_KEYS = [
    "distilbert",
    "bert",
    "roberta",
]


def load_result(
    model_key: str,
) -> dict:

    path = (
        OUTPUT_ROOT
        / model_key
        / "evaluation.json"
    )

    if not path.exists():

        raise FileNotFoundError(
            f"Missing evaluation result: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def main() -> None:

    results = [
        load_result(
            model_key
        )
        for model_key
        in MODEL_KEYS
    ]

    print()
    print("=" * 87)

    print(
        "Architecture QA Transformer Comparison"
    )

    print("=" * 87)

    print(
        f"{'Model':<18}"
        f"{'Precision':>12}"
        f"{'Recall':>12}"
        f"{'Micro-F1':>12}"
        f"{'Macro-F1':>12}"
        f"{'Best Epoch':>12}"
    )

    print("-" * 87)

    ranking = []

    for result in results:

        metrics = (
            result["test"]["metrics"]
        )

        ranking.append(
            (
                metrics["micro_f1"],
                result,
            )
        )

        print(
            f"{result['display_name']:<18}"
            f"{metrics['micro_precision']:>12.4f}"
            f"{metrics['micro_recall']:>12.4f}"
            f"{metrics['micro_f1']:>12.4f}"
            f"{metrics['macro_f1']:>12.4f}"
            f"{result['best_epoch']:>12}"
        )

    print("-" * 87)

    ranking.sort(
        key=lambda item: (
            item[0],
            item[1]["test"]["metrics"][
                "macro_f1"
            ],
        ),
        reverse=True,
    )

    best = ranking[0][1]

    print()
    print(
        "Best supervised model "
        "(by test Micro-F1 for reporting):"
    )

    print(
        f"  {best['display_name']}"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Model/hyperparameter decisions should primarily "
        "be based on validation performance."
    )

    print(
        "The held-out test set is for final reporting."
    )

    print("=" * 87)


if __name__ == "__main__":
    main()