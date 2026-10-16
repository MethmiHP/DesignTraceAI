"""
Semantic near-duplicate analysis for the ADR candidate dataset.

This script checks:
1. same-family semantic similarity
2. cross-family semantic similarity
3. cross-label semantic similarity

It does not modify the dataset.
"""

import csv
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


DATASET_PATH = (
    Path(__file__).resolve().parent
    / "raw"
    / "adr_significance_candidates.csv"
)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

HIGH_THRESHOLD = 0.90
VERY_HIGH_THRESHOLD = 0.95

MAX_EXAMPLES_PER_SECTION = 20


def load_dataset():
    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def build_model_text(row):
    parts = [
        row.get("title", ""),
        row.get("context", ""),
        row.get("decision", ""),
        row.get("rationale", ""),
        row.get("alternatives", ""),
        row.get("trade_offs", ""),
    ]

    return " ".join(
        part.strip()
        for part in parts
        if part and part.strip()
    )


def describe_pair(
    first,
    second,
    similarity,
):
    print(
        f"Similarity: {similarity:.4f}"
    )

    print(
        f"A: {first['decision_id']} | "
        f"{first['source_module']} | "
        f"{first['domain']} | "
        f"{first['scenario_family']} | "
        f"label={first['label']}"
    )

    print(
        f"   {first['title']}"
    )

    print(
        f"   {first['decision']}"
    )

    print(
        f"B: {second['decision_id']} | "
        f"{second['source_module']} | "
        f"{second['domain']} | "
        f"{second['scenario_family']} | "
        f"label={second['label']}"
    )

    print(
        f"   {second['title']}"
    )

    print(
        f"   {second['decision']}"
    )

    print("-" * 80)


def main():
    rows = load_dataset()

    print()
    print("ADR Candidate Semantic Similarity Analysis")
    print("==========================================")
    print(f"Records: {len(rows)}")
    print(f"Model: {MODEL_NAME}")
    print(f"High threshold: {HIGH_THRESHOLD}")
    print(f"Very high threshold: {VERY_HIGH_THRESHOLD}")

    texts = [
        build_model_text(row)
        for row in rows
    ]

    print()
    print("Loading embedding model...")

    model = SentenceTransformer(
        MODEL_NAME
    )

    print(
        "Generating embeddings..."
    )

    embeddings = model.encode(
        texts,
        convert_to_tensor=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    similarity_matrix = cos_sim(
        embeddings,
        embeddings,
    )

    same_family_pairs = []
    cross_family_pairs = []
    cross_label_pairs = []

    high_pair_count = 0
    very_high_pair_count = 0

    for first_index in range(
        len(rows)
    ):
        for second_index in range(
            first_index + 1,
            len(rows),
        ):
            similarity = float(
                similarity_matrix[
                    first_index,
                    second_index,
                ]
            )

            if similarity < HIGH_THRESHOLD:
                continue

            high_pair_count += 1

            if similarity >= VERY_HIGH_THRESHOLD:
                very_high_pair_count += 1

            first = rows[first_index]
            second = rows[second_index]

            same_family = (
                first["source_module"]
                == second["source_module"]
                and
                first["scenario_family"]
                == second["scenario_family"]
            )

            same_label = (
                first["label"]
                == second["label"]
            )

            pair = (
                similarity,
                first_index,
                second_index,
            )

            if same_family:
                same_family_pairs.append(
                    pair
                )
            else:
                cross_family_pairs.append(
                    pair
                )

            if not same_label:
                cross_label_pairs.append(
                    pair
                )

    same_family_pairs.sort(
        reverse=True
    )

    cross_family_pairs.sort(
        reverse=True
    )

    cross_label_pairs.sort(
        reverse=True
    )

    print()
    print("Summary")
    print("-------")

    print(
        f"Pairs >= {HIGH_THRESHOLD:.2f}: "
        f"{high_pair_count}"
    )

    print(
        f"Pairs >= {VERY_HIGH_THRESHOLD:.2f}: "
        f"{very_high_pair_count}"
    )

    print(
        "High-similarity same-family pairs: "
        f"{len(same_family_pairs)}"
    )

    print(
        "High-similarity cross-family pairs: "
        f"{len(cross_family_pairs)}"
    )

    print(
        "High-similarity cross-label pairs: "
        f"{len(cross_label_pairs)}"
    )

    print()
    print(
        "Top same-family similarities"
    )
    print(
        "----------------------------"
    )

    for (
        similarity,
        first_index,
        second_index,
    ) in same_family_pairs[
        :MAX_EXAMPLES_PER_SECTION
    ]:
        describe_pair(
            rows[first_index],
            rows[second_index],
            similarity,
        )

    print()
    print(
        "Top cross-family similarities"
    )
    print(
        "-----------------------------"
    )

    for (
        similarity,
        first_index,
        second_index,
    ) in cross_family_pairs[
        :MAX_EXAMPLES_PER_SECTION
    ]:
        describe_pair(
            rows[first_index],
            rows[second_index],
            similarity,
        )

    print()
    print(
        "Cross-label similarities"
    )
    print(
        "------------------------"
    )

    if not cross_label_pairs:
        print(
            "No opposite-label pairs exceeded "
            f"{HIGH_THRESHOLD:.2f} similarity."
        )

    for (
        similarity,
        first_index,
        second_index,
    ) in cross_label_pairs[
        :MAX_EXAMPLES_PER_SECTION
    ]:
        describe_pair(
            rows[first_index],
            rows[second_index],
            similarity,
        )


if __name__ == "__main__":
    main()