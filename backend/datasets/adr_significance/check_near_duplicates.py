"""
Check semantic near-duplicates in the ADR significance dataset.

This script:
- loads the provisional ADR significance CSV
- combines important textual fields
- creates sentence embeddings
- calculates cosine similarity between records
- reports highly similar record pairs

The script does NOT delete or modify any dataset rows.
It is only used for inspection before the final benchmark is created.
"""

import csv
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


DATASET_PATH = (
    Path(__file__).resolve().parent
    / "raw"
    / "adr_significance_dataset.csv"
)


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

SIMILARITY_THRESHOLD = 0.90


def load_dataset():
    """
    Load the ADR significance dataset.
    """

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def build_model_text(row):
    """
    Combine important textual fields into one semantic representation.
    """

    parts = [
        row.get("title", ""),
        row.get("context", ""),
        row.get("decision", ""),
        row.get("rationale", ""),
    ]

    return " ".join(
        part.strip()
        for part in parts
        if part and part.strip()
    )


def main():
    rows = load_dataset()

    if not rows:
        print("Dataset is empty.")
        return

    print()
    print("ADR Significance Near-Duplicate Check")
    print("=====================================")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Total records: {len(rows)}")
    print(f"Model: {MODEL_NAME}")
    print(
        f"Similarity threshold: "
        f"{SIMILARITY_THRESHOLD:.2f}"
    )

    print()
    print("Loading sentence-transformer model...")

    model = SentenceTransformer(
        MODEL_NAME
    )

    texts = [
        build_model_text(row)
        for row in rows
    ]

    print(
        "Generating semantic embeddings..."
    )

    embeddings = model.encode(
        texts,
        convert_to_tensor=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    print(
        "Calculating pairwise similarities..."
    )

    similarity_matrix = cos_sim(
        embeddings,
        embeddings,
    )

    suspicious_pairs = []

    for first_index in range(len(rows)):
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

            if (
                similarity
                >= SIMILARITY_THRESHOLD
            ):
                suspicious_pairs.append(
                    (
                        similarity,
                        first_index,
                        second_index,
                    )
                )

    suspicious_pairs.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    print()
    print(
        "Near-duplicate pairs found: "
        f"{len(suspicious_pairs)}"
    )

    if not suspicious_pairs:
        print()
        print(
            "No record pairs exceeded the "
            "configured similarity threshold."
        )

        print()
        print(
            "Near-duplicate check: PASSED"
        )

        return

    print()
    print(
        "Suspicious semantic pairs"
    )
    print(
        "-------------------------"
    )

    for pair_number, (
        similarity,
        first_index,
        second_index,
    ) in enumerate(
        suspicious_pairs,
        start=1,
    ):
        first = rows[first_index]
        second = rows[second_index]

        print()
        print(
            f"Pair {pair_number}"
        )

        print(
            f"Similarity: "
            f"{similarity:.4f}"
        )

        print()
        print(
            "Record A:"
        )

        print(
            f"  ID: "
            f"{first['decision_id']}"
        )

        print(
            f"  Source: "
            f"{first['source_module']}"
        )

        print(
            f"  Domain: "
            f"{first['domain']}"
        )

        print(
            f"  Family: "
            f"{first['scenario_family']}"
        )

        print(
            f"  Label: "
            f"{first['label']}"
        )

        print(
            f"  Title: "
            f"{first['title']}"
        )

        print(
            f"  Decision: "
            f"{first['decision']}"
        )

        print()
        print(
            "Record B:"
        )

        print(
            f"  ID: "
            f"{second['decision_id']}"
        )

        print(
            f"  Source: "
            f"{second['source_module']}"
        )

        print(
            f"  Domain: "
            f"{second['domain']}"
        )

        print(
            f"  Family: "
            f"{second['scenario_family']}"
        )

        print(
            f"  Label: "
            f"{second['label']}"
        )

        print(
            f"  Title: "
            f"{second['title']}"
        )

        print(
            f"  Decision: "
            f"{second['decision']}"
        )

        print()
        print(
            "-" * 60
        )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "These pairs are only candidates for review."
    )

    print(
        "High semantic similarity does not automatically "
        "mean one record should be deleted."
    )


if __name__ == "__main__":
    main()