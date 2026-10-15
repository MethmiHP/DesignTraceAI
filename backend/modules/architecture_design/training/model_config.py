"""
Configuration for Milestone 7.1B supervised transformer fine-tuning.

All models solve the same six-label multi-label Quality Attribute
classification problem using the exact same train/validation/test splits.
"""

from __future__ import annotations


MODEL_REGISTRY = {
    "distilbert": {
        "hf_name": "distilbert-base-uncased",
        "display_name": "DistilBERT",
    },
    "bert": {
        "hf_name": "bert-base-uncased",
        "display_name": "BERT-base",
    },
    "roberta": {
        "hf_name": "roberta-base",
        "display_name": "RoBERTa-base",
    },
}


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

RANDOM_SEED = 42


# ---------------------------------------------------------------------------
# Training configuration
# ---------------------------------------------------------------------------

NUM_EPOCHS = 4

BATCH_SIZE = 8

LEARNING_RATE = 2e-5

WEIGHT_DECAY = 0.01

MAX_LENGTH = 128


# Initial decision threshold.
#
# IMPORTANT:
# This is deliberately fixed at 0.50 during Milestone 7.1B.
# Threshold calibration belongs to Milestone 7.2 and must use only the
# validation set, never the test set.
DECISION_THRESHOLD = 0.50