"""
DesignTrace AI - NLP Token Alignment

Aligns word-level BIO labels with the subword
tokens used by Hugging Face transformer models.
"""

import json
from pathlib import Path

from transformers import AutoTokenizer


DATA_DIR = (
    Path(__file__).resolve().parent
    / "project_split"
)

MODEL_NAME = "bert-base-uncased"

LABEL_LIST = [
    "O",
    "B-ENTITY",
    "I-ENTITY",
    "B-ATTRIBUTE",
    "I-ATTRIBUTE",
    "B-ACTION",
    "I-ACTION",
]

LABEL2ID = {
    label: index
    for index, label in enumerate(LABEL_LIST)
}

ID2LABEL = {
    index: label
    for label, index in LABEL2ID.items()
}


def load_bio_dataset(filename: str) -> list[dict]:
    path = DATA_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def align_labels(examples: list[dict], tokenizer):
    """
    Align word-level BIO tags with subword tokens.

    Only the first subword receives a label.
    Other subwords and special tokens receive -100.
    """

    aligned_examples = []

    for example in examples:
        tokens = example["tokens"]
        tags = example["ner_tags"]

        if len(tokens) != len(tags):
            raise ValueError(
                f"Token/label mismatch: "
                f"{example['requirement_id']}"
            )

        encoded = tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            max_length=128,
        )

        word_ids = encoded.word_ids()

        aligned_labels = []
        previous_word_id = None

        for word_id in word_ids:

            if word_id is None:
                aligned_labels.append(-100)

            elif word_id != previous_word_id:
                aligned_labels.append(
                    LABEL2ID[tags[word_id]]
                )

            else:
                aligned_labels.append(-100)

            previous_word_id = word_id

        aligned_examples.append({
            "input_ids": encoded["input_ids"],
            "attention_mask": encoded["attention_mask"],
            "labels": aligned_labels,
        })

    return aligned_examples


def reconstruct_word_predictions(
    tokens: list[str],
    tokenizer,
    predicted_ids: list[int],
    id2label: dict,
) -> list[dict]:
    """
    Convert BERT subword predictions into word-level predictions.

    Uses the first subword prediction for each original word,
    matching the current training alignment strategy.
    """

    encoded = tokenizer(
        tokens,
        is_split_into_words=True,
        truncation=True,
        max_length=128,
    )

    word_ids = encoded.word_ids()

    if len(predicted_ids) != len(word_ids):
        raise ValueError(
            "Prediction length does not match tokenized input."
        )

    results = []
    seen_word_ids = set()

    for token_index, word_id in enumerate(word_ids):

        if word_id is None:
            continue

        if word_id in seen_word_ids:
            continue

        seen_word_ids.add(word_id)

        label_id = int(predicted_ids[token_index])

        label = id2label.get(
            label_id,
            id2label.get(str(label_id)),
        )

        if label is None:
            raise ValueError(
                f"Unknown predicted label ID: {label_id}"
            )

        results.append({
            "token": tokens[word_id],
            "label": label,
        })

    return results

def main():
    print("DesignTrace AI - Token Alignment")
    print("--------------------------------")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
    )

    for split in ("train", "validation", "test"):
        examples = load_bio_dataset(
            f"{split}_bio.json"
        )

        aligned = align_labels(examples, tokenizer)

        output_path = DATA_DIR / f"{split}_aligned.json"

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(aligned, file, indent=2)

        print(
            f"{split}: {len(aligned)} requirements aligned"
        )

    print("--------------------------------")
    print("Token alignment completed successfully.")


if __name__ == "__main__":
    main()
