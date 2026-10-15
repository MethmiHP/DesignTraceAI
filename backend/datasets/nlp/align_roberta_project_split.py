"""
DesignTrace AI - RoBERTa Token Alignment
=======================================

Converts project-independent BIO datasets into
RoBERTa-compatible token classification datasets.

Input:
    datasets/nlp/project_split/train_bio.json
    datasets/nlp/project_split/validation_bio.json
    datasets/nlp/project_split/test_bio.json

Output:
    datasets/nlp/project_split/roberta/train_aligned.json
    datasets/nlp/project_split/roberta/validation_aligned.json
    datasets/nlp/project_split/roberta/test_aligned.json

Model tokenizer:
    roberta-base

This script does not modify the original datasets.
"""

import json
from pathlib import Path
from collections import Counter

from transformers import AutoTokenizer


# --------------------------------------------------
# 1. Paths and configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = (
    BASE_DIR
    / "datasets"
    / "nlp"
    / "project_split"
)

OUTPUT_DIR = DATA_DIR / "roberta"

MODEL_NAME = "roberta-base"

MAX_LENGTH = 128

LABELS = [
    "O",
    "B-ENTITY",
    "I-ENTITY",
    "B-ATTRIBUTE",
    "I-ATTRIBUTE",
    "B-ACTION",
    "I-ACTION",
]

label2id = {
    label: index
    for index, label in enumerate(LABELS)
}


# --------------------------------------------------
# 2. Load BIO dataset
# --------------------------------------------------

def load_bio_dataset(path):

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            f"{path.name} must contain a JSON list."
        )

    return data


# --------------------------------------------------
# 3. Convert word-level BIO to token-level BIO
# --------------------------------------------------

def align_example(example, tokenizer):

    words = example.get("tokens")
    word_labels = example.get("ner_tags")

    if words is None or word_labels is None:
        raise ValueError(
            "Each BIO example must contain "
            "'tokens' and 'labels'."
        )

    if len(words) != len(word_labels):
        raise ValueError(
            "Token and label counts do not match."
        )

    if not all(isinstance(word, str) for word in words):
        raise ValueError(
            "All tokens must be strings."
        )

    if not all(label in label2id for label in word_labels):
        invalid = [
            label
            for label in word_labels
            if label not in label2id
        ]

        raise ValueError(
            f"Unknown BIO labels: {invalid}"
        )

    encoding = tokenizer(
        words,
        is_split_into_words=True,
        truncation=True,
        max_length=MAX_LENGTH,
        padding=False,
    )

    word_ids = encoding.word_ids()

    aligned_labels = []

    previous_word_id = None

    for word_id in word_ids:

        if word_id is None:
            aligned_labels.append(-100)
            previous_word_id = None
            continue

        label = word_labels[word_id]

        if word_id != previous_word_id:
            # First subtoken of a word
            aligned_labels.append(
                label2id[label]
            )

        else:
            # Additional subtokens
            # Ignore them during loss calculation
            aligned_labels.append(-100)

        previous_word_id = word_id

    if not (
        len(encoding["input_ids"])
        == len(encoding["attention_mask"])
        == len(aligned_labels)
    ):
        raise ValueError(
            "RoBERTa token alignment failed."
        )

    return {
        "input_ids": encoding["input_ids"],
        "attention_mask": encoding["attention_mask"],
        "labels": aligned_labels,
    }


# --------------------------------------------------
# 4. Align complete dataset
# --------------------------------------------------

def align_dataset(data, tokenizer, split_name):

    aligned = []

    label_counts = Counter()

    truncated_examples = 0

    for index, example in enumerate(data):

        try:
            aligned_example = align_example(
                example,
                tokenizer,
            )

            aligned.append(aligned_example)

            for label_id in aligned_example["labels"]:
                if label_id != -100:
                    label_counts[LABELS[label_id]] += 1

            # Detect whether the input exceeded the
            # configured maximum sequence length.
            full_encoding = tokenizer(
                example["tokens"],
                is_split_into_words=True,
                truncation=False,
            )

            if len(full_encoding["input_ids"]) > MAX_LENGTH:
                truncated_examples += 1

        except Exception as error:

            requirement_id = example.get(
                "requirement_id",
                f"{split_name}_{index}",
            )

            raise ValueError(
                f"Alignment failed for "
                f"{requirement_id}: {error}"
            ) from error

    return aligned, label_counts, truncated_examples


# --------------------------------------------------
# 5. Save JSON
# --------------------------------------------------

def save_json(path, data):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


# --------------------------------------------------
# 6. Main
# --------------------------------------------------

def main():

    print(
        "DesignTrace AI - RoBERTa Token Alignment"
    )
    print("------------------------------------------")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Loading RoBERTa tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
        add_prefix_space=True,
    )

    if not tokenizer.is_fast:
        raise ValueError(
            "A fast tokenizer is required "
            "for word alignment."
        )

    splits = [
        "train",
        "validation",
        "test",
    ]

    report = {
        "model": MODEL_NAME,
        "max_length": MAX_LENGTH,
        "label2id": label2id,
        "splits": {},
    }

    for split_name in splits:

        input_path = (
            DATA_DIR
            / f"{split_name}_bio.json"
        )

        output_path = (
            OUTPUT_DIR
            / f"{split_name}_aligned.json"
        )

        print(
            f"\nProcessing {split_name} dataset..."
        )

        data = load_bio_dataset(input_path)

        aligned, label_counts, truncated = (
            align_dataset(
                data,
                tokenizer,
                split_name,
            )
        )

        save_json(
            output_path,
            aligned,
        )

        report["splits"][split_name] = {
            "requirements": len(aligned),
            "truncated_requirements": truncated,
            "label_counts": dict(label_counts),
        }

        print(
            f"{split_name}: "
            f"{len(aligned)} requirements aligned"
        )

        print(
            "Truncated requirements:",
            truncated,
        )

        print(
            "Label counts:",
            dict(label_counts),
        )

    report_path = (
        OUTPUT_DIR
        / "alignment_report.json"
    )

    save_json(
        report_path,
        report,
    )

    print("\n------------------------------------------")
    print("RoBERTa token alignment completed.")
    print("Aligned datasets saved to:", OUTPUT_DIR)
    print("Report saved to:", report_path)


if __name__ == "__main__":
    main()
