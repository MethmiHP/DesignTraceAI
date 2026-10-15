"""
DesignTrace AI - RoBERTa Concept Extraction Training
=================================================

Fine-tunes RoBERTa for database concept extraction.

Labels:
    ENTITY
    ATTRIBUTE
    ACTION

Input:
    datasets/nlp/project_split/roberta/train_aligned.json
    datasets/nlp/project_split/roberta/validation_aligned.json

Output:
    outputs/nlp_models/roberta_project_split/
"""

import json
from pathlib import Path

import numpy as np
import torch

from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    Trainer,
    TrainingArguments,
    DataCollatorForTokenClassification,
)
from seqeval.metrics import (
    precision_score,
    recall_score,
    f1_score,
)

# --------------------------------------------------
# 1. Paths and configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = (
    BASE_DIR
    / "datasets"
    / "nlp"
    / "project_split"
    / "roberta"
)

TRAIN_PATH = DATA_DIR / "train_aligned.json"
VALIDATION_PATH = DATA_DIR / "validation_aligned.json"

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "nlp_models"
    / "roberta_project_split"
)

MODEL_NAME = "roberta-base"

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

id2label = {
    index: label
    for index, label in enumerate(LABELS)
}


# --------------------------------------------------
# 2. Load aligned datasets
# --------------------------------------------------

def load_dataset_file(filename):

    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list) or not data:
        raise ValueError(
            f"{filename} must contain a non-empty list."
        )

    required_fields = {
        "input_ids",
        "attention_mask",
        "labels",
    }

    for index, example in enumerate(data):

        missing = required_fields - example.keys()

        if missing:
            raise ValueError(
                f"{filename}, example {index}: "
                f"missing fields {missing}"
            )

        lengths = [
            len(example["input_ids"]),
            len(example["attention_mask"]),
            len(example["labels"]),
        ]

        if len(set(lengths)) != 1:
            raise ValueError(
                f"{filename}, example {index}: "
                "input_ids, attention_mask and labels "
                "must have equal lengths."
            )

        for label in example["labels"]:
            if label != -100 and label not in id2label:
                raise ValueError(
                    f"Invalid label ID: {label}. "
                    "Check BIO label ordering."
                )

    return Dataset.from_list(data)


# --------------------------------------------------
# 3. Evaluation metrics
# --------------------------------------------------

def compute_metrics(eval_prediction):

    predictions, labels = eval_prediction

    if isinstance(predictions, tuple):
        predictions = predictions[0]

    predicted_ids = np.argmax(
        predictions,
        axis=2,
    )

    true_predictions = []
    true_labels = []

    for prediction, label_sequence in zip(
        predicted_ids,
        labels,
    ):

        predicted_tags = []
        actual_tags = []

        for predicted_id, label_id in zip(
            prediction,
            label_sequence,
        ):

            if int(label_id) == -100:
                continue

            predicted_tags.append(
                id2label[int(predicted_id)]
            )

            actual_tags.append(
                id2label[int(label_id)]
            )

        true_predictions.append(predicted_tags)
        true_labels.append(actual_tags)

    return {
        "precision": precision_score(
            true_labels,
            true_predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            true_labels,
            true_predictions,
            zero_division=0,
        ),
        "f1": f1_score(
            true_labels,
            true_predictions,
            zero_division=0,
        ),
    }


# --------------------------------------------------
# 4. Train RoBERTa
# --------------------------------------------------

def main():

    print("DesignTrace AI - RoBERTa Training")
    print("--------------------------------")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Loading datasets...")

    train_dataset = load_dataset_file(
        "train_aligned.json"
    )

    validation_dataset = load_dataset_file(
        "validation_aligned.json"
    )

    print(
        "Training requirements:",
        len(train_dataset),
    )

    print(
        "Validation requirements:",
        len(validation_dataset),
    )

    print("Loading RoBERTa tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
        add_prefix_space=True,
    )

    print("Loading pretrained RoBERTa...")

    model = (
        AutoModelForTokenClassification
        .from_pretrained(
            MODEL_NAME,
            num_labels=len(LABELS),
            label2id=label2id,
            id2label=id2label,
        )
    )

    # IMPORTANT:
    # The aligned JSON files must have been
    # generated using this same tokenizer
    # and the same BIO label ID ordering.

    data_collator = (
        DataCollatorForTokenClassification(
            tokenizer=tokenizer
        )
    )

    training_args = TrainingArguments(

        output_dir=str(OUTPUT_DIR),

        # Small pilot experiment
        num_train_epochs=3,

        per_device_train_batch_size=4,

        per_device_eval_batch_size=4,

        learning_rate=2e-5,

        weight_decay=0.01,

        # Evaluate after each epoch
        eval_strategy="epoch",

        save_strategy="epoch",

        logging_strategy="epoch",

        # Select checkpoint using validation F1
        load_best_model_at_end=True,

        metric_for_best_model="f1",

        greater_is_better=True,

        save_total_limit=2,

        report_to="none",

        seed=42,

        data_seed=42,

        fp16=False,
    )

    trainer = Trainer(

        model=model,

        args=training_args,

        train_dataset=train_dataset,

        eval_dataset=validation_dataset,

        processing_class=tokenizer,

        data_collator=data_collator,

        compute_metrics=compute_metrics,
    )

    print("Starting RoBERTa fine-tuning...")

    trainer.train()

    print("Evaluating on validation dataset...")

    results = trainer.evaluate()

    print("--------------------------------")
    print("Validation Results")
    print("--------------------------------")

    for key, value in results.items():

        if isinstance(value, (float, int)):
            print(f"{key}: {value:.4f}")

    print("Saving trained model...")

    trainer.save_model(str(OUTPUT_DIR))

    tokenizer.save_pretrained(
        str(OUTPUT_DIR)
    )

    metrics_path = (
        OUTPUT_DIR / "validation_metrics.json"
    )

    with open(
        metrics_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
        )

    print("--------------------------------")
    print("RoBERTa training completed.")
    print("Model saved to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
