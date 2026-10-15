"""
Runtime Configuration – Milestone 7.2.

Centralizes architecture-specific configuration options from environment
variables and loads them from the backend .env file.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


# ---------------------------------------------------------
# Load environment variables from backend/.env
# ---------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[2]

ENV_PATH = BACKEND_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


# ---------------------------------------------------------
# Fine-tuned RoBERTa model configuration
# ---------------------------------------------------------

QA_ROBERTA_MODEL_PATH = (
    BACKEND_DIR
    / "datasets"
    / "roberta"
    / "best_model"
)

QA_ROBERTA_THRESHOLD = 0.50


# ---------------------------------------------------------
# Architecture runtime configuration
# ---------------------------------------------------------

class ArchitectureConfig(BaseModel):

    # LLM configuration
    llm_model: str = os.getenv(
        "ARCHITECTURE_LLM_MODEL",
        "gemini-3.5-flash-lite",
    )

    gemini_api_key: str | None = os.getenv(
        "GEMINI_API_KEY"
    )

    use_stub_llm: bool = os.getenv(
        "ARCHITECTURE_USE_STUB_LLM",
        "false",
    ).lower() in (
        "true",
        "1",
        "yes",
    )

    # RAG / embedding configuration
    embedding_model: str = os.getenv(
        "ARCHITECTURE_EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    retrieval_top_k: int = int(
        os.getenv(
            "ARCHITECTURE_RETRIEVAL_TOP_K",
            "5",
        )
    )

    # Quality Attribute classifier configuration
    qa_classifier: str = os.getenv(
        "ARCHITECTURE_QA_CLASSIFIER",
        "roberta",
    )

    qa_semantic_threshold: float = float(
        os.getenv(
            "ARCHITECTURE_QA_SEMANTIC_THRESHOLD",
            "0.50",
        )
    )


# Singleton configuration instance
architecture_config = ArchitectureConfig()