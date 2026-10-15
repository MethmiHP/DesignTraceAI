"""
FastAPI Dependencies for Architecture Decision Agent.

Provides dependency injection for ArchitectureDesignService and supports
switching between:

- StubLLMProvider / GeminiLLMProvider
- KeywordClassifier
- SemanticQualityClassifier
- Fine-tuned RoBERTa classifier

The service is cached and reused after first initialization.
"""

from __future__ import annotations

from functools import lru_cache
import logging

from fastapi import HTTPException, status

from .config import (
    architecture_config,
    QA_ROBERTA_MODEL_PATH,
    QA_ROBERTA_THRESHOLD,
)

from .service import ArchitectureDesignService

from .llm.provider import (
    GeminiLLMProvider,
    StubLLMProvider,
)

from .retrieval.embedding_provider import (
    SentenceTransformerEmbeddingProvider,
)

from .retrieval.vector_store import (
    InMemoryVectorStore,
)

from .quality_classifier import (
    KeywordClassifier,
    SemanticQualityClassifier,
)

from .supervised_quality_classifier import (
    SupervisedTransformerQualityClassifier,
)


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_architecture_service() -> ArchitectureDesignService:
    """
    Factory dependency providing a cached ArchitectureDesignService instance.

    The LLM provider, embedding model, vector store and selected QA classifier
    are initialized once and reused.

    The cache can be cleared during testing using:

        get_architecture_service.cache_clear()

    FastAPI dependency overrides can also be used in tests.
    """

    # ------------------------------------------------------------------
    # 1. Resolve LLM provider
    # ------------------------------------------------------------------

    if architecture_config.use_stub_llm:

        llm_provider = StubLLMProvider()

    elif architecture_config.gemini_api_key:

        try:
            llm_provider = GeminiLLMProvider(
                model_name=architecture_config.llm_model,
                api_key=architecture_config.gemini_api_key,
            )

        except Exception as exc:

            logger.error(
                "Failed to initialize GeminiLLMProvider: %s",
                type(exc).__name__,
            )

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": "LLM_PROVIDER_INIT_FAILED",
                    "message": (
                        "Failed to initialize external LLM provider."
                    ),
                },
            ) from exc

    else:

        logger.warning(
            "GEMINI_API_KEY not configured and "
            "ARCHITECTURE_USE_STUB_LLM is false."
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "MISSING_LLM_API_KEY",
                "message": (
                    "GEMINI_API_KEY is not configured "
                    "and stub mode is disabled."
                ),
            },
        )

    # ------------------------------------------------------------------
    # 2. Resolve embedding provider
    # ------------------------------------------------------------------

    try:

        embedding_provider = (
            SentenceTransformerEmbeddingProvider(
                model_name=architecture_config.embedding_model
            )
        )

    except Exception as exc:

        logger.error(
            "Failed to initialize "
            "SentenceTransformerEmbeddingProvider: %s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "EMBEDDING_PROVIDER_UNAVAILABLE",
                "message": (
                    "Failed to initialize embedding model provider."
                ),
            },
        ) from exc

    # ------------------------------------------------------------------
    # 3. Resolve QA classifier
    # ------------------------------------------------------------------

    classifier_type = (
        architecture_config
        .qa_classifier
        .strip()
        .lower()
    )

    if classifier_type == "keyword":

        classifier = KeywordClassifier()

        logger.info(
            "Architecture QA classifier: KeywordClassifier"
        )

    elif classifier_type == "semantic":

        classifier = SemanticQualityClassifier(
            embedding_provider=embedding_provider,
            threshold=architecture_config.qa_semantic_threshold,
        )

        logger.info(
            "Architecture QA classifier: "
            "SemanticQualityClassifier"
        )

    elif classifier_type == "roberta":

        try:

            classifier = (
                SupervisedTransformerQualityClassifier(
                    model_path=QA_ROBERTA_MODEL_PATH,
                    threshold=QA_ROBERTA_THRESHOLD,
                )
            )

            logger.info(
                "Architecture QA classifier: "
                "SupervisedTransformerQualityClassifier "
                "(fine-tuned RoBERTa)"
            )

        except Exception as exc:

            logger.error(
                "Failed to initialize fine-tuned RoBERTa "
                "QA classifier: %s",
                type(exc).__name__,
            )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "ROBERTA_CLASSIFIER_UNAVAILABLE",
                    "message": (
                        "Failed to initialize the fine-tuned "
                        "RoBERTa QA classifier."
                    ),
                },
            ) from exc

    else:

        logger.error(
            "Unsupported QA classifier configured: %s",
            architecture_config.qa_classifier,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INVALID_QA_CLASSIFIER",
                "message": (
                    "Unsupported ARCHITECTURE_QA_CLASSIFIER: "
                    f"{architecture_config.qa_classifier}. "
                    "Supported values are: "
                    "keyword, semantic, roberta."
                ),
            },
        )

    # ------------------------------------------------------------------
    # 4. Resolve vector store
    # ------------------------------------------------------------------

    vector_store = InMemoryVectorStore()

    # ------------------------------------------------------------------
    # 5. Build Architecture Design Service
    # ------------------------------------------------------------------

    return ArchitectureDesignService(
        classifier=classifier,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        llm_provider=llm_provider,
    )