# Trains multiple transformer models for requirement classification and
# compares their performance on the same test dataset using evaluation
# metrics such as accuracy, precision, recall, F1-score, and inference time.

from pathlib import Path
import json
import time

import numpy as np

from datasets import Dataset

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



# CREATE HUGGING FACE DATASET

def create_dataset(
    records: list[dict]
) -> Dataset:

    texts = []
    labels = []

    for item in records:

        text = item.get("text")
        label = item.get("label")

        if not text:
            continue

        if label not in LABEL_TO_ID:
            continue

        texts.append(text)

        labels.append(
            LABEL_TO_ID[label]
        )

    return Dataset.from_dict({
        "text": texts,
        "label": labels,
    })



# METRICS
def compute_metrics(
    eval_prediction
):

    logits, labels = eval_prediction

    predictions = np.argmax(
        logits,
        axis=-1
    )

    accuracy = accuracy_score(
        labels,
        predictions
    )

    # Weighted metrics
    weighted_precision, weighted_recall, weighted_f1, _ = (
        precision_recall_fscore_support(
            labels,
            predictions,
            average="weighted",
            zero_division=0,
        )
    )

    # Macro metrics
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



# TRAIN MODEL

def train_model(
    model_key: str = "distilbert"
):

    if model_key not in MODELS:

        raise ValueError(
            f"Unknown model: {model_key}"
        )

    model_name = MODELS[
        model_key
    ]

    print(
        "\n================================"
    )

    print(
        f"TRAINING NFR MODEL: {model_key}"
    )

    print(
        f"Base model: {model_name}"
    )

    print(
        "================================"
    )


    # LOAD DATA

    train_records = load_json(
        DATA_DIR
        / "nfr_category_train.json"
    )

    validation_records = load_json(
        DATA_DIR
        / "nfr_category_validation.json"
    )

    train_dataset = create_dataset(
        train_records
    )

    validation_dataset = create_dataset(
        validation_records
    )

    print(
        f"Training records: "
        f"{len(train_dataset)}"
    )

    print(
        f"Validation records: "
        f"{len(validation_dataset)}"
    )

    print(
        f"Number of classes: "
        f"{len(NFR_LABELS)}"
    )

    print(
        "\nLabel mapping:"
    )

    for label, label_id in LABEL_TO_ID.items():

        print(
            f"{label_id}: {label}"
        )


    # TOKENIZER
    tokenizer = (
        AutoTokenizer.from_pretrained(
            model_name
        )
    )

    def tokenize(batch):

        return tokenizer(
            batch["text"],
            padding="max_length",
            truncation=True,
            max_length=128,
        )

    train_dataset = (
        train_dataset.map(
            tokenize,
            batched=True
        )
    )

    validation_dataset = (
        validation_dataset.map(
            tokenize,
            batched=True
        )
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
    output_dir = (
        MODEL_OUTPUT_DIR
        / "nfr_category"
        / model_key
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    # TRAINING ARGUMENTS

    training_args = TrainingArguments(

        output_dir=str(
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

        weight_decay=0.01,

        eval_strategy="epoch",

        save_strategy="epoch",

        load_best_model_at_end=True,

        # Important:
        # use macro F1 because NFR classes
        # are imbalanced
        metric_for_best_model=
            "macro_f1",

        greater_is_better=True,

        logging_steps=20,

        report_to="none",
    )

  
    # TRAINER

    trainer = Trainer(

        model=model,

        args=training_args,

        train_dataset=
            train_dataset,

        eval_dataset=
            validation_dataset,

        compute_metrics=
            compute_metrics,
    )


    # TRAIN

    start_time = time.time()

    trainer.train()

    training_time = (
        time.time()
        -
        start_time
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    metrics = trainer.evaluate()

    print(
        "\n================================"
    )

    print(
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


    # SAVE FINAL MODEL

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
        "\nModel saved to:"
    )

    print(
        final_model_dir
    )


# MAIN

if __name__ == "__main__":

    train_model(
        # model_key="distilbert"
        # model_key="bert"
        model_key="roberta"
    )