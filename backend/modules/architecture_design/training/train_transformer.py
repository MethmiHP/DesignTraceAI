"""
Milestone 7.1B
==============

Fine-tune transformer encoders for multi-label software Quality Attribute
classification.

Supported models:

- DistilBERT
- BERT-base
- RoBERTa-base

Task:
    ASR statement
        ->
    transformer encoder
        ->
    6 independent logits
        ->
    sigmoid
        ->
    Security / Scalability / Performance /
    Reliability / Maintainability / Availability

The same frozen train/validation/test splits are used for every model.

Model selection:
    Best checkpoint is selected using VALIDATION Micro-F1.

Final test metrics:
    Test data is evaluated only after the best validation checkpoint
    has been selected.

The initial classification threshold is fixed at 0.50.
Threshold calibration is intentionally deferred to Milestone 7.2.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from sklearn.metrics import (
    precision_recall_fscore_support,
)

from torch.utils.data import (
    DataLoader,
    Dataset,
)

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from modules.architecture_design.training.dataset_utils import (
    LABEL_LIST,
    labels_to_multihot,
)

from modules.architecture_design.training.model_config import (
    BATCH_SIZE,
    DECISION_THRESHOLD,
    LEARNING_RATE,
    MAX_LENGTH,
    MODEL_REGISTRY,
    NUM_EPOCHS,
    RANDOM_SEED,
    WEIGHT_DECAY,
)


# ============================================================================
# Paths
# ============================================================================

BACKEND_DIR = (
    Path(__file__)
    .resolve()
    .parents[3]
)

DATASET_DIR = (
    BACKEND_DIR
    / "datasets"
    / "architecture_qa"
)

OUTPUT_ROOT = (
    BACKEND_DIR
    / "outputs"
    / "architecture_models"
)


# ============================================================================
# Reproducibility
# ============================================================================

def set_seed(seed: int) -> None:
    random.seed(seed)

    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ============================================================================
# Device
# ============================================================================

def resolve_device() -> torch.device:

    if torch.cuda.is_available():
        return torch.device("cuda")

    if (
        hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return torch.device("mps")

    return torch.device("cpu")


# ============================================================================
# Dataset
# ============================================================================

def load_json(path: Path) -> list[dict[str, Any]]:

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


class ArchitectureQADataset(Dataset):

    def __init__(
        self,
        records: list[dict[str, Any]],
        tokenizer,
        max_length: int,
    ) -> None:

        self.records = records

        self.tokenizer = tokenizer

        self.max_length = max_length


    def __len__(self) -> int:

        return len(self.records)


    def __getitem__(
        self,
        index: int,
    ) -> dict[str, torch.Tensor]:

        record = self.records[index]

        encoded = self.tokenizer(
            record["statement"],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )

        item = {
            key: value.squeeze(0)
            for key, value
            in encoded.items()
        }

        label_vector = labels_to_multihot(
            record["labels"]
        )

        item["labels"] = torch.tensor(
            label_vector,
            dtype=torch.float32,
        )

        return item


# ============================================================================
# Metrics
# ============================================================================

def calculate_metrics(
    probabilities: np.ndarray,
    gold_labels: np.ndarray,
    threshold: float,
) -> dict[str, Any]:

    predictions = (
        probabilities >= threshold
    ).astype(int)

    micro_precision, micro_recall, micro_f1, _ = (
        precision_recall_fscore_support(
            gold_labels,
            predictions,
            average="micro",
            zero_division=0,
        )
    )

    macro_precision, macro_recall, macro_f1, _ = (
        precision_recall_fscore_support(
            gold_labels,
            predictions,
            average="macro",
            zero_division=0,
        )
    )

    per_label = {}

    for index, label in enumerate(LABEL_LIST):

        p, r, f1, support = (
            precision_recall_fscore_support(
                gold_labels[:, index],
                predictions[:, index],
                average="binary",
                zero_division=0,
            )
        )

        per_label[label] = {
            "precision": round(
                float(p),
                4,
            ),
            "recall": round(
                float(r),
                4,
            ),
            "f1": round(
                float(f1),
                4,
            ),
            "support": int(
                gold_labels[
                    :,
                    index,
                ].sum()
            ),
        }

    return {
        "threshold": threshold,

        "micro_precision": round(
            float(micro_precision),
            4,
        ),

        "micro_recall": round(
            float(micro_recall),
            4,
        ),

        "micro_f1": round(
            float(micro_f1),
            4,
        ),

        "macro_precision": round(
            float(macro_precision),
            4,
        ),

        "macro_recall": round(
            float(macro_recall),
            4,
        ),

        "macro_f1": round(
            float(macro_f1),
            4,
        ),

        "per_label": per_label,
    }


# ============================================================================
# Evaluation
# ============================================================================

@torch.no_grad()
def evaluate(
    model,
    loader: DataLoader,
    device: torch.device,
    threshold: float,
) -> tuple[float, dict[str, Any], np.ndarray, np.ndarray]:

    model.eval()

    total_loss = 0.0

    all_probabilities = []

    all_labels = []

    for batch in loader:

        batch = {
            key: value.to(device)
            for key, value
            in batch.items()
        }

        outputs = model(
            **batch
        )

        loss = outputs.loss

        total_loss += loss.item()

        probabilities = torch.sigmoid(
            outputs.logits
        )

        all_probabilities.append(
            probabilities
            .detach()
            .cpu()
            .numpy()
        )

        all_labels.append(
            batch["labels"]
            .detach()
            .cpu()
            .numpy()
        )

    probabilities = np.concatenate(
        all_probabilities,
        axis=0,
    )

    gold_labels = np.concatenate(
        all_labels,
        axis=0,
    )

    metrics = calculate_metrics(
        probabilities=probabilities,
        gold_labels=gold_labels,
        threshold=threshold,
    )

    average_loss = (
        total_loss
        / max(
            len(loader),
            1,
        )
    )

    return (
        average_loss,
        metrics,
        probabilities,
        gold_labels,
    )


# ============================================================================
# Prediction log
# ============================================================================

def build_prediction_log(
    records: list[dict[str, Any]],
    probabilities: np.ndarray,
    threshold: float,
) -> list[dict[str, Any]]:

    logs = []

    for record, probs in zip(
        records,
        probabilities,
    ):

        predicted_labels = [
            LABEL_LIST[i]
            for i, probability
            in enumerate(probs)
            if probability >= threshold
        ]

        logs.append(
            {
                "example_id":
                    record["example_id"],

                "statement":
                    record["statement"],

                "gold_labels":
                    record["labels"],

                "predicted_labels":
                    predicted_labels,

                "probabilities": {
                    LABEL_LIST[i]:
                        round(
                            float(probability),
                            4,
                        )

                    for i, probability
                    in enumerate(probs)
                },
            }
        )

    return logs


# ============================================================================
# Training
# ============================================================================

def train_model(
    model_key: str,
) -> None:

    if model_key not in MODEL_REGISTRY:

        raise ValueError(
            f"Unsupported model: {model_key}"
        )

    set_seed(
        RANDOM_SEED
    )

    model_info = MODEL_REGISTRY[
        model_key
    ]

    hf_name = model_info[
        "hf_name"
    ]

    display_name = model_info[
        "display_name"
    ]

    device = resolve_device()

    print()
    print("=" * 70)
    print(
        "Architecture QA Transformer Fine-Tuning"
    )
    print("=" * 70)

    print(
        f"Model:      {display_name}"
    )

    print(
        f"HF model:   {hf_name}"
    )

    print(
        f"Device:     {device}"
    )

    print(
        f"Labels:     {len(LABEL_LIST)}"
    )

    print(
        f"Threshold:  {DECISION_THRESHOLD}"
    )

    print("=" * 70)

    # ------------------------------------------------------------------
    # Load frozen splits
    # ------------------------------------------------------------------

    train_records = load_json(
        DATASET_DIR / "train.json"
    )

    validation_records = load_json(
        DATASET_DIR / "validation.json"
    )

    test_records = load_json(
        DATASET_DIR / "test.json"
    )

    print(
        f"Train:      {len(train_records)}"
    )

    print(
        f"Validation: {len(validation_records)}"
    )

    print(
        f"Test:       {len(test_records)}"
    )

    print()

    # ------------------------------------------------------------------
    # Tokenizer
    # ------------------------------------------------------------------

    print(
        "Loading tokenizer..."
    )

    tokenizer = (
        AutoTokenizer
        .from_pretrained(
            hf_name
        )
    )

    # ------------------------------------------------------------------
    # Datasets
    # ------------------------------------------------------------------

    train_dataset = (
        ArchitectureQADataset(
            train_records,
            tokenizer,
            MAX_LENGTH,
        )
    )

    validation_dataset = (
        ArchitectureQADataset(
            validation_records,
            tokenizer,
            MAX_LENGTH,
        )
    )

    test_dataset = (
        ArchitectureQADataset(
            test_records,
            tokenizer,
            MAX_LENGTH,
        )
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    # ------------------------------------------------------------------
    # Model
    # ------------------------------------------------------------------

    print(
        "Loading transformer model..."
    )

    id2label = {
        index: label
        for index, label
        in enumerate(LABEL_LIST)
    }

    label2id = {
        label: index
        for index, label
        in enumerate(LABEL_LIST)
    }

    model = (
        AutoModelForSequenceClassification
        .from_pretrained(
            hf_name,

            num_labels=len(
                LABEL_LIST
            ),

            id2label=id2label,

            label2id=label2id,

            problem_type=(
                "multi_label_classification"
            ),
        )
    )

    model.to(
        device
    )

    # ------------------------------------------------------------------
    # Optimizer
    # ------------------------------------------------------------------

    optimizer = torch.optim.AdamW(
        model.parameters(),

        lr=LEARNING_RATE,

        weight_decay=WEIGHT_DECAY,
    )

    # ------------------------------------------------------------------
    # Output directory
    # ------------------------------------------------------------------

    model_output_dir = (
        OUTPUT_ROOT
        / model_key
    )

    model_output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    best_model_dir = (
        model_output_dir
        / "best_model"
    )

    # ------------------------------------------------------------------
    # Training loop
    # ------------------------------------------------------------------

    best_validation_f1 = -1.0

    best_epoch = 0

    history = []

    total_start = time.perf_counter()

    for epoch in range(
        1,
        NUM_EPOCHS + 1,
    ):

        epoch_start = (
            time.perf_counter()
        )

        model.train()

        total_train_loss = 0.0

        for batch in train_loader:

            batch = {
                key: value.to(device)
                for key, value
                in batch.items()
            }

            optimizer.zero_grad()

            outputs = model(
                **batch
            )

            loss = outputs.loss

            loss.backward()

            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                max_norm=1.0,
            )

            optimizer.step()

            total_train_loss += (
                loss.item()
            )

        average_train_loss = (
            total_train_loss
            / max(
                len(train_loader),
                1,
            )
        )

        (
            validation_loss,
            validation_metrics,
            _,
            _,
        ) = evaluate(
            model=model,
            loader=validation_loader,
            device=device,
            threshold=DECISION_THRESHOLD,
        )

        epoch_seconds = (
            time.perf_counter()
            - epoch_start
        )

        history_item = {
            "epoch": epoch,

            "train_loss": round(
                average_train_loss,
                6,
            ),

            "validation_loss": round(
                validation_loss,
                6,
            ),

            "validation_micro_f1":
                validation_metrics[
                    "micro_f1"
                ],

            "validation_macro_f1":
                validation_metrics[
                    "macro_f1"
                ],

            "epoch_seconds": round(
                epoch_seconds,
                2,
            ),
        }

        history.append(
            history_item
        )

        print(
            f"Epoch {epoch}/{NUM_EPOCHS}"
        )

        print(
            f"  Train loss:       "
            f"{average_train_loss:.4f}"
        )

        print(
            f"  Validation loss:  "
            f"{validation_loss:.4f}"
        )

        print(
            f"  Validation Micro-F1: "
            f"{validation_metrics['micro_f1']:.4f}"
        )

        print(
            f"  Validation Macro-F1: "
            f"{validation_metrics['macro_f1']:.4f}"
        )

        print(
            f"  Time: {epoch_seconds:.2f}s"
        )

        # --------------------------------------------------------------
        # Best checkpoint based ONLY on validation set
        # --------------------------------------------------------------

        validation_micro_f1 = (
            validation_metrics[
                "micro_f1"
            ]
        )

        if (
            validation_micro_f1
            > best_validation_f1
        ):

            best_validation_f1 = (
                validation_micro_f1
            )

            best_epoch = epoch

            print(
                "  -> New best validation checkpoint."
            )

            model.save_pretrained(
                best_model_dir
            )

            tokenizer.save_pretrained(
                best_model_dir
            )

        print()

    total_training_seconds = (
        time.perf_counter()
        - total_start
    )

    # ------------------------------------------------------------------
    # Reload best validation checkpoint
    # ------------------------------------------------------------------

    print(
        f"Reloading best checkpoint "
        f"from epoch {best_epoch}..."
    )

    best_model = (
        AutoModelForSequenceClassification
        .from_pretrained(
            best_model_dir
        )
    )

    best_model.to(
        device
    )

    # ------------------------------------------------------------------
    # Final validation metrics
    # ------------------------------------------------------------------

    (
        final_validation_loss,
        final_validation_metrics,
        validation_probabilities,
        _,
    ) = evaluate(
        model=best_model,
        loader=validation_loader,
        device=device,
        threshold=DECISION_THRESHOLD,
    )

    # ------------------------------------------------------------------
    # FINAL TEST EVALUATION
    # ------------------------------------------------------------------

    (
        final_test_loss,
        final_test_metrics,
        test_probabilities,
        _,
    ) = evaluate(
        model=best_model,
        loader=test_loader,
        device=device,
        threshold=DECISION_THRESHOLD,
    )

    # ------------------------------------------------------------------
    # Prediction logs
    # ------------------------------------------------------------------

    validation_predictions = (
        build_prediction_log(
            validation_records,
            validation_probabilities,
            DECISION_THRESHOLD,
        )
    )

    test_predictions = (
        build_prediction_log(
            test_records,
            test_probabilities,
            DECISION_THRESHOLD,
        )
    )

    # ------------------------------------------------------------------
    # Experiment report
    # ------------------------------------------------------------------

    result = {
        "pipeline_version":
            "M7.1B",

        "model_key":
            model_key,

        "display_name":
            display_name,

        "huggingface_model":
            hf_name,

        "task":
            "multi_label_quality_attribute_classification",

        "labels":
            LABEL_LIST,

        "random_seed":
            RANDOM_SEED,

        "training_config": {
            "epochs":
                NUM_EPOCHS,

            "batch_size":
                BATCH_SIZE,

            "learning_rate":
                LEARNING_RATE,

            "weight_decay":
                WEIGHT_DECAY,

            "max_length":
                MAX_LENGTH,

            "decision_threshold":
                DECISION_THRESHOLD,
        },

        "dataset": {
            "train_count":
                len(
                    train_records
                ),

            "validation_count":
                len(
                    validation_records
                ),

            "test_count":
                len(
                    test_records
                ),
        },

        "device":
            str(device),

        "best_epoch":
            best_epoch,

        "best_validation_micro_f1":
            best_validation_f1,

        "training_seconds":
            round(
                total_training_seconds,
                2,
            ),

        "training_history":
            history,

        "validation": {
            "loss":
                round(
                    final_validation_loss,
                    6,
                ),

            "metrics":
                final_validation_metrics,
        },

        "test": {
            "loss":
                round(
                    final_test_loss,
                    6,
                ),

            "metrics":
                final_test_metrics,
        },

        "validation_predictions":
            validation_predictions,

        "test_predictions":
            test_predictions,
    }

    result_path = (
        model_output_dir
        / "evaluation.json"
    )

    with result_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # ------------------------------------------------------------------
    # Terminal summary
    # ------------------------------------------------------------------

    print()
    print("=" * 70)

    print(
        f"{display_name} Fine-Tuning Complete"
    )

    print("=" * 70)

    print(
        f"Best epoch: "
        f"{best_epoch}"
    )

    print()

    print(
        "FINAL TEST METRICS"
    )

    print("-" * 70)

    print(
        f"Micro Precision: "
        f"{final_test_metrics['micro_precision']:.4f}"
    )

    print(
        f"Micro Recall:    "
        f"{final_test_metrics['micro_recall']:.4f}"
    )

    print(
        f"Micro F1:        "
        f"{final_test_metrics['micro_f1']:.4f}"
    )

    print(
        f"Macro F1:        "
        f"{final_test_metrics['macro_f1']:.4f}"
    )

    print()

    print(
        "Per-label F1:"
    )

    for label in LABEL_LIST:

        label_metrics = (
            final_test_metrics[
                "per_label"
            ][label]
        )

        print(
            f"  {label:<18}"
            f"{label_metrics['f1']:.4f}"
        )

    print()

    print(
        f"Saved to: "
        f"{result_path}"
    )

    print("=" * 70)


# ============================================================================
# CLI
# ============================================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Fine-tune transformer models "
            "for Architecture QA classification."
        )
    )

    parser.add_argument(
        "--model",
        required=True,
        choices=list(
            MODEL_REGISTRY.keys()
        ),
        help=(
            "Model to train: "
            "distilbert | bert | roberta"
        ),
    )

    args = parser.parse_args()

    train_model(
        args.model
    )


if __name__ == "__main__":
    main()