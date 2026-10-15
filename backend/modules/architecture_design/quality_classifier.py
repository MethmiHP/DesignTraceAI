"""
Quality Attribute Classifier – Milestone 1.

Design:
  - BaseClassifier  : abstract contract.  Swap this for a transformer later
                      without touching service.py, quality_profile.py, or schemas.py.
  - KeywordClassifier: deterministic, keyword-count-based implementation.

Confidence formula (per attribute):
    hits   = number of distinct keywords that appear in the statement
    total  = size of that attribute's keyword set
    raw    = hits / total
    score  = min(raw * CONFIDENCE_SCALE, MAX_CONFIDENCE)

CONFIDENCE_SCALE amplifies sparse matches so that a single strong keyword
produces a useful score rather than 1/10 = 0.10.
MAX_CONFIDENCE caps the score below 1.0 to leave room for a future model.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, FrozenSet, List, Optional

from .schemas import QualityAttribute, QualityHit

if TYPE_CHECKING:
    from .retrieval.embedding_provider import BaseEmbeddingProvider

# ---------------------------------------------------------------------------
# Tuning knobs
# ---------------------------------------------------------------------------

CONFIDENCE_SCALE  = 3.0   # amplifier so 1 keyword hit ≠ a tiny score
MAX_CONFIDENCE    = 0.97  # ceiling – a transformer can exceed this later


# ---------------------------------------------------------------------------
# Keyword registry
# ---------------------------------------------------------------------------

_KEYWORD_MAP: Dict[QualityAttribute, FrozenSet[str]] = {
    QualityAttribute.SECURITY: frozenset({
        "unauthorized", "encrypted", "authentication", "protected",
        "privacy", "secure", "security", "credential", "permission",
        "confidential",
    }),
    QualityAttribute.SCALABILITY: frozenset({
        "concurrent", "scale", "scalable", "load", "traffic",
        "distributed", "capacity", "elastic", "peak demand", "high volume",
    }),
    QualityAttribute.PERFORMANCE: frozenset({
        "response time", "latency", "throughput", "fast", "speed",
        "milliseconds", "efficient", "performance", "acceptable response",
        "processing time",
    }),
    QualityAttribute.RELIABILITY: frozenset({
        "operational", "remain operational", "fail", "fails", "failure",
        "fault", "recover", "resilient", "redundant", "reliable",
        "reliability", "recovery",
    }),
    QualityAttribute.MAINTAINABILITY: frozenset({
        "maintainable", "maintainability", "modular", "readable",
        "refactor", "testable", "documented", "decouple", "extensible",
        "clean code",
    }),
    QualityAttribute.AVAILABILITY: frozenset({
        "available", "availability", "downtime", "24/7", "always on",
        "uptime", "replication", "failover", "high availability",
        "continuous",
    }),
}


# ---------------------------------------------------------------------------
# Abstract base – the plug-in point for future classifiers
# ---------------------------------------------------------------------------

class BaseClassifier(ABC):
    """
    All classifiers must implement classify().
    The rest of the module depends only on this interface.
    """

    @abstractmethod
    def classify(self, statement: str) -> List[QualityHit]:
        """
        Return a list of quality-attribute hits for the given requirement
        statement.  An empty list means no attribute matched.
        Results should be ordered by descending confidence.
        """


# ---------------------------------------------------------------------------
# Deterministic keyword-based classifier
# ---------------------------------------------------------------------------

class KeywordClassifier(BaseClassifier):
    """
    Deterministic baseline classifier for Quality Attribute identification.

    NOTE: The `confidence` field represents a heuristic keyword match score
    based on keyword presence and tuning amplifiers, NOT a calibrated probabilistic
    confidence. Future semantic classifiers (e.g. transformers) will serve as
    comparative benchmarks against this baseline.

    Matching is case-insensitive and whitespace-normalised.
    Only attributes with at least one keyword hit are included in the result.
    """

    def classify(self, statement: str) -> List[QualityHit]:
        normalised = statement.lower()
        hits: List[QualityHit] = []

        for attr, keywords in _KEYWORD_MAP.items():
            matched = self._count_matches(normalised, keywords)
            if matched == 0:
                continue

            raw_score  = matched / len(keywords)
            confidence = min(raw_score * CONFIDENCE_SCALE, MAX_CONFIDENCE)
            confidence = round(confidence, 4)

            hits.append(QualityHit(name=attr, confidence=confidence))

        # Sort by descending confidence
        hits.sort(key=lambda h: h.confidence, reverse=True)
        return hits

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _count_matches(text: str, keywords: FrozenSet[str]) -> int:
        """Count how many distinct keywords from the set appear in the text."""
        count = 0
        for kw in keywords:
            # Use word-boundary-aware search for single-word keywords;
            # plain substring search for multi-word phrases.
            if " " in kw:
                if kw in text:
                    count += 1
            else:
                # \b-delimited to avoid partial matches (e.g. "fail" inside "failover")
                pattern = rf"\b{re.escape(kw)}\b"
                if re.search(pattern, text):
                    count += 1
        return count


# ---------------------------------------------------------------------------
# Semantic embedding-based classifier
# ---------------------------------------------------------------------------

def _normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


def _dot_product(u: List[float], v: List[float]) -> float:
    return sum(a * b for a, b in zip(u, v))


class SemanticQualityClassifier(BaseClassifier):
    """
    Semantic multi-label classifier using dense sentence embeddings.

    Computes cosine similarity between an incoming requirement statement
    and curated prototype representations (definitions, descriptions, positive examples,
    and architectural indicators) for each of the six supported quality attributes.

    NOTE: The `confidence` field in `QualityHit` represents a semantic cosine
    similarity score, NOT a calibrated statistical probability.
    """

    def __init__(
        self,
        embedding_provider: BaseEmbeddingProvider | None = None,
        threshold: float = 0.50,
        knowledge_path: Path | str | None = None,
    ) -> None:
        if embedding_provider is None:
            from .retrieval.embedding_provider import SentenceTransformerEmbeddingProvider
            self._embedding_provider: BaseEmbeddingProvider = SentenceTransformerEmbeddingProvider()
        else:
            self._embedding_provider = embedding_provider

        self._threshold = threshold

        if knowledge_path is None:
            knowledge_path = Path(__file__).resolve().parent / "knowledge" / "quality_attributes.json"
        self._knowledge_path = Path(knowledge_path)

        self._prototypes: Dict[QualityAttribute, List[List[float]]] = {}
        self._load_and_embed_prototypes()

    def _load_and_embed_prototypes(self) -> None:
        if not self._knowledge_path.exists():
            raise FileNotFoundError(f"Semantic QA knowledge base not found at: {self._knowledge_path}")

        data = json.loads(self._knowledge_path.read_text(encoding="utf-8"))

        for item in data.get("attributes", []):
            qa_name = item.get("name")
            try:
                qa_enum = QualityAttribute(qa_name)
            except ValueError:
                # Unsupported QA label ignored
                continue

            texts: List[str] = []
            if "definition" in item and item["definition"]:
                texts.append(item["definition"])
            for desc in item.get("representative_descriptions", []):
                texts.append(desc)
            for ex in item.get("positive_examples", []):
                texts.append(ex)
            if item.get("architectural_indicators"):
                texts.append(f"Architectural indicators: {', '.join(item['architectural_indicators'])}")

            if not texts:
                continue

            raw_embeddings = self._embedding_provider.embed(texts)
            norm_embeddings = [_normalize(vec) for vec in raw_embeddings]
            self._prototypes[qa_enum] = norm_embeddings

    def classify(self, statement: str) -> List[QualityHit]:
        if not statement.strip() or not self._prototypes:
            return []

        raw_query_vec = self._embedding_provider.embed([statement])[0]
        query_vec = _normalize(raw_query_vec)

        hits: List[QualityHit] = []
        for qa_enum, proto_vecs in self._prototypes.items():
            max_sim = max((_dot_product(query_vec, pv) for pv in proto_vecs), default=0.0)
            score = round(min(max(max_sim, 0.0), 1.0), 4)

            if score >= self._threshold:
                hits.append(QualityHit(name=qa_enum, confidence=score))

        hits.sort(key=lambda h: h.confidence, reverse=True)
        return hits
