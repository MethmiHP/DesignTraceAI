"""
Inspect the strongest features learned by the
TF-IDF + Logistic Regression ADR significance baseline.

This helps identify whether the classifier is learning
meaningful decision-significance patterns or simply exploiting
obvious lexical cues in the synthetic dataset.
"""

import pickle
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "tfidf_logreg"
    / "model.pkl"
)


TOP_N = 40


def main():
    with MODEL_PATH.open("rb") as file:
        pipeline = pickle.load(file)

    vectorizer = pipeline.named_steps[
        "tfidf"
    ]

    classifier = pipeline.named_steps[
        "classifier"
    ]

    feature_names = (
        vectorizer.get_feature_names_out()
    )

    coefficients = (
        classifier.coef_[0]
    )

    positive_indices = (
        coefficients.argsort()[-TOP_N:][::-1]
    )

    negative_indices = (
        coefficients.argsort()[:TOP_N]
    )

    print()
    print("ADR TF-IDF Feature Analysis")
    print("===========================")

    print()
    print(
        "Strongest features for "
        "SIGNIFICANT decisions"
    )
    print(
        "-------------------------------"
    )

    for rank, index in enumerate(
        positive_indices,
        start=1,
    ):
        print(
            f"{rank:>2}. "
            f"{feature_names[index]:<35} "
            f"{coefficients[index]:.4f}"
        )

    print()
    print(
        "Strongest features for "
        "NOT SIGNIFICANT decisions"
    )
    print(
        "-----------------------------------"
    )

    for rank, index in enumerate(
        negative_indices,
        start=1,
    ):
        print(
            f"{rank:>2}. "
            f"{feature_names[index]:<35} "
            f"{coefficients[index]:.4f}"
        )


if __name__ == "__main__":
    main()