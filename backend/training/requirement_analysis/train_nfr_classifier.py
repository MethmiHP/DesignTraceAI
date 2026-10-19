# Trains an NFR quality-attribute classifier using:
# 1. RoBERTa
# 2. Class-weighted cross-entropy
# 3. Additional domain-generic augmentation examples
#
# The augmented model is saved separately from the baseline
# and balanced-only models so they can be compared fairly.

from pathlib import Path
import json
import time
from collections import Counter

import numpy as np
import torch

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
)

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)

from training.requirement_analysis.model_config import (
    MODELS,
    TRAINING_CONFIG,
)


# PATHS

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = (
    BASE_DIR
    / "training"
    / "requirement_analysis"
    / "prepared_data"
)

MODEL_OUTPUT_DIR = (
    BASE_DIR
    / "trained_models"
    / "requirement_analysis"
)


# NFR LABELS

NFR_LABELS = [
    "Availability",
    "Fault Tolerance",
    "Legal",
    "Look and Feel",
    "Maintainability",
    "Operational",
    "Performance",
    "Portability",
    "Scalability",
    "Security",
    "Usability",
]


LABEL_TO_ID = {
    label: index
    for index, label in enumerate(NFR_LABELS)
}


ID_TO_LABEL = {
    index: label
    for label, index in LABEL_TO_ID.items()
}


# LOAD JSON

def load_json(
    file_path: Path
) -> list[dict]:

    with file_path.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# PYTORCH DATASET

class RequirementDataset(
    torch.utils.data.Dataset
):

    def __init__(
        self,
        records: list[dict],
        tokenizer
    ):

        texts = []
        labels = []

        for item in records:

            text = item.get(
                "text"
            )

            label = item.get(
                "label"
            )

            if not text:
                continue

            if label not in LABEL_TO_ID:
                continue

            texts.append(
                text
            )

            labels.append(
                LABEL_TO_ID[
                    label
                ]
            )


        self.encodings = tokenizer(
            texts,
            padding="max_length",
            truncation=True,
            max_length=128,
        )

        self.labels = labels


    def __len__(self):

        return len(
            self.labels
        )


    def __getitem__(
        self,
        index
    ):

        item = {
            key: torch.tensor(
                values[index]
            )
            for key, values
            in self.encodings.items()
        }

        item["labels"] = torch.tensor(
            self.labels[index],
            dtype=torch.long
        )

        return item


# CALCULATE CLASS WEIGHTS

def calculate_class_weights(
    records: list[dict]
) -> torch.Tensor:

    valid_labels = [
        item.get("label")
        for item in records
        if item.get("label")
        in LABEL_TO_ID
    ]

    counts = Counter(
        valid_labels
    )

    total_samples = len(
        valid_labels
    )

    number_of_classes = len(
        NFR_LABELS
    )

    weights = []


    print(
        "\nTraining class distribution:"
    )

    for label in NFR_LABELS:

        count = counts.get(
            label,
            0
        )

        print(
            f"{label}: {count}"
        )

        if count == 0:

            weight = 0.0

        else:

            weight = (
                total_samples
                /
                (
                    number_of_classes
                    *
                    count
                )
            )

        weights.append(
            weight
        )


    print(
        "\nCalculated class weights:"
    )

    for label, weight in zip(
        NFR_LABELS,
        weights
    ):

        print(
            f"{label}: "
            f"{weight:.4f}"
        )


    return torch.tensor(
        weights,
        dtype=torch.float
    )


# METRICS

def compute_metrics(
    eval_prediction
):

    logits, labels = (
        eval_prediction
    )

    predictions = np.argmax(
        logits,
        axis=-1
    )


    accuracy = accuracy_score(
        labels,
        predictions
    )


    weighted_precision, weighted_recall, weighted_f1, _ = (
        precision_recall_fscore_support(
            labels,
            predictions,
            average="weighted",
            zero_division=0,
        )
    )


    macro_precision, macro_recall, macro_f1, _ = (
        precision_recall_fscore_support(
            labels,
            predictions,
            average="macro",
            zero_division=0,
        )
    )


    return {
        "accuracy":
            accuracy,

        "weighted_precision":
            weighted_precision,

        "weighted_recall":
            weighted_recall,

        "weighted_f1":
            weighted_f1,

        "macro_precision":
            macro_precision,

        "macro_recall":
            macro_recall,

        "macro_f1":
            macro_f1,
    }


# WEIGHTED TRAINER

class WeightedTrainer(
    Trainer
):

    def __init__(
        self,
        *args,
        class_weights=None,
        **kwargs
    ):

        super().__init__(
            *args,
            **kwargs
        )

        self.class_weights = (
            class_weights
        )


    def compute_loss(
        self,
        model,
        inputs,
        return_outputs=False,
        num_items_in_batch=None,
    ):

        labels = inputs.get(
            "labels"
        )

        outputs = model(
            **inputs
        )

        logits = (
            outputs.logits
        )


        weights = (
            self.class_weights
            .to(
                logits.device
            )
        )


        loss_function = (
            torch.nn.CrossEntropyLoss(
                weight=weights
            )
        )


        loss = loss_function(
            logits,
            labels
        )


        if return_outputs:

            return (
                loss,
                outputs
            )

        return loss


# TRAIN MODEL

def train_model(
    model_key: str = "roberta"
):

    if model_key not in MODELS:

        raise ValueError(
            f"Unknown model: "
            f"{model_key}"
        )


    model_name = (
        MODELS[
            model_key
        ]
    )


    print(
        "\n================================"
    )

    print(
        f"TRAINING BALANCED + AUGMENTED "
        f"NFR MODEL: {model_key}"
    )

    print(
        f"Base model: "
        f"{model_name}"
    )

    print(
        "================================"
    )


    # LOAD ORIGINAL TRAINING DATA
    original_train_records = load_json(
        DATA_DIR
        / "nfr_category_train.json"
    )


    # LOAD AUGMENTATION DATA

    augmentation_records = load_json(
        DATA_DIR
        / "nfr_category_augmentation.json"
    )


    # COMBINE TRAINING DATA

    train_records = (
        original_train_records
        + augmentation_records
    )


    # LOAD VALIDATION DATA
    #
    # Validation is intentionally NOT augmented.

    validation_records = load_json(
        DATA_DIR
        / "nfr_category_validation.json"
    )


    print(
        f"\nOriginal training records: "
        f"{len(original_train_records)}"
    )

    print(
        f"Augmentation records: "
        f"{len(augmentation_records)}"
    )

    print(
        f"Combined training records: "
        f"{len(train_records)}"
    )

    print(
        f"Validation records: "
        f"{len(validation_records)}"
    )


    # CALCULATE CLASS WEIGHTS
    #
    # We calculate these using the combined training set.

    class_weights = (
        calculate_class_weights(
            train_records
        )
    )


    # TOKENIZER

    tokenizer = (
        AutoTokenizer
        .from_pretrained(
            model_name
        )
    )


    # CREATE PYTORCH DATASETS

    train_dataset = (
        RequirementDataset(
            train_records,
            tokenizer
        )
    )

    validation_dataset = (
        RequirementDataset(
            validation_records,
            tokenizer
        )
    )


    print(
        f"\nTraining records used: "
        f"{len(train_dataset)}"
    )

    print(
        f"Validation records used: "
        f"{len(validation_dataset)}"
    )

    print(
        f"Number of classes: "
        f"{len(NFR_LABELS)}"
    )


    print(
        "\nLabel mapping:"
    )

    for label, label_id in (
        LABEL_TO_ID.items()
    ):

        print(
            f"{label_id}: "
            f"{label}"
        )


    # MODEL

    model = (
        AutoModelForSequenceClassification
        .from_pretrained(
            model_name,

            num_labels=
                len(NFR_LABELS),

            id2label=
                ID_TO_LABEL,

            label2id=
                LABEL_TO_ID,
        )
    )


    # OUTPUT DIRECTORY
    #
    # Keeps this model separate from:
    #
    # roberta/final
    # roberta_balanced/final

    output_dir = (
        MODEL_OUTPUT_DIR
        / "nfr_category"
        / f"{model_key}_balanced_augmented"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    # TRAINING ARGUMENTS

    training_args = (
        TrainingArguments(

            output_dir=
                str(
                    output_dir
                ),

            num_train_epochs=
                TRAINING_CONFIG[
                    "num_train_epochs"
                ],

            learning_rate=
                TRAINING_CONFIG[
                    "learning_rate"
                ],

            per_device_train_batch_size=
                TRAINING_CONFIG[
                    "batch_size"
                ],

            per_device_eval_batch_size=
                TRAINING_CONFIG[
                    "batch_size"
                ],

            weight_decay=
                0.01,

            eval_strategy=
                "epoch",

            save_strategy=
                "epoch",

            load_best_model_at_end=
                True,

            # Macro F1 is used because
            # the NFR classes are imbalanced.
            metric_for_best_model=
                "macro_f1",

            greater_is_better=
                True,

            logging_steps=
                20,

            report_to=
                "none",
        )
    )


    # TRAINER

    trainer = (
        WeightedTrainer(

            model=model,

            args=training_args,

            train_dataset=
                train_dataset,

            eval_dataset=
                validation_dataset,

            compute_metrics=
                compute_metrics,

            class_weights=
                class_weights,
        )
    )


    # TRAIN

    start_time = (
        time.time()
    )

    trainer.train()

    training_time = (
        time.time()
        -
        start_time
    )


    # VALIDATION

    metrics = (
        trainer.evaluate()
    )


    print(
        "\n================================"
    )

    print(
        "BALANCED + AUGMENTED "
        "NFR VALIDATION RESULTS"
    )

    print(
        "================================"
    )


    print(
        f"Accuracy: "
        f"{metrics.get('eval_accuracy')}"
    )

    print(
        f"Weighted Precision: "
        f"{metrics.get('eval_weighted_precision')}"
    )

    print(
        f"Weighted Recall: "
        f"{metrics.get('eval_weighted_recall')}"
    )

    print(
        f"Weighted F1: "
        f"{metrics.get('eval_weighted_f1')}"
    )

    print(
        f"Macro Precision: "
        f"{metrics.get('eval_macro_precision')}"
    )

    print(
        f"Macro Recall: "
        f"{metrics.get('eval_macro_recall')}"
    )

    print(
        f"Macro F1: "
        f"{metrics.get('eval_macro_f1')}"
    )

    print(
        f"Training time: "
        f"{training_time:.2f} seconds"
    )


    # SAVE FINAL AUGMENTED MODEL

    final_model_dir = (
        output_dir
        / "final"
    )


    trainer.save_model(
        final_model_dir
    )

    tokenizer.save_pretrained(
        final_model_dir
    )


    print(
        "\nBalanced + augmented "
        "model saved to:"
    )

    print(
        final_model_dir
    )


# MAIN

if __name__ == "__main__":

    train_model(
        model_key="roberta"
    )