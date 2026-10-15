"""
Architecture Scorer – Milestone 2.

Loads the static knowledge base (architecture_styles.json) once at import time
and exposes a single function:  score(profile) -> list[ArchitectureEvaluation]

Scoring is fully deterministic and explainable:

  Step 1 – Weight per quality attribute
      total_active = sum of non-zero counts in QualityProfile
      weight[attr] = count[attr] / total_active       (0 when count = 0)
      Edge case: if total_active == 0, uniform weight 1/6 is used.

  Step 2 – Raw score per architecture style
      raw = Σ( weight[attr] × support_score[attr] )
      per_attribute_contribution = weight[attr] × support_score[attr]

  Step 3 – Normalize to 0–100
      max_possible = Σ( weight[attr] × 5 )   # 5 = best support score
      normalized   = round( raw / max_possible × 100, 2 )

  Step 4 – Rank
      Sort by normalized_score descending; assign rank 1, 2, 3, 4, 5.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ..schemas import (
    ArchitectureEvaluation,
    ArchitectureStyle,
    QualityAttribute,
    QualityContributions,
    QualityProfile,
)

# ---------------------------------------------------------------------------
# Load the knowledge base once at module import time
# ---------------------------------------------------------------------------

_KB_PATH = Path(__file__).parent / "architecture_styles.json"

def _load_kb() -> List[Dict[str, Any]]:
    with open(_KB_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["styles"]

_STYLES: List[Dict[str, Any]] = _load_kb()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score(profile: QualityProfile) -> List[ArchitectureEvaluation]:
    """
    Score all architecture styles against the given quality profile.

    Args:
        profile: Project-level QualityProfile (counts per attribute).

    Returns:
        List of ArchitectureEvaluation objects, sorted by rank (best first).
    """
    weights = _derive_weights(profile)
    max_possible = sum(w * 5 for w in weights.values())

    # Step 1: collect raw scores in plain dicts (no Pydantic yet)
    raw_results = []

    for style_data in _STYLES:
        kb_scores = style_data["quality_scores"]

        contributions: Dict[str, float] = {}
        raw_score = 0.0

        for attr in QualityAttribute:
            w       = weights[attr.value]
            support = float(kb_scores.get(attr.value, 0))
            contrib = round(w * support, 4)
            contributions[attr.value] = contrib
            raw_score += contrib

        raw_score = round(raw_score, 4)
        normalized = round((raw_score / max_possible) * 100, 2) if max_possible > 0 else 0.0

        raw_results.append({
            "style_data":     style_data,
            "contributions":  contributions,
            "raw_score":      raw_score,
            "normalized":     normalized,
        })

    # Step 2: sort by normalized score descending so rank is known before construction
    raw_results.sort(key=lambda r: r["normalized"], reverse=True)

    # Step 3: group by normalized score to handle ties properly
    grouped_by_score: Dict[float, List[Dict[str, Any]]] = {}
    for r in raw_results:
        grouped_by_score.setdefault(r["normalized"], []).append(r)

    # Sort the unique scores descending
    sorted_scores = sorted(grouped_by_score.keys(), reverse=True)

    # Step 4: construct Pydantic objects with shared rank for ties
    evaluations: List[ArchitectureEvaluation] = []
    current_rank = 1
    
    for score_val in sorted_scores:
        group = grouped_by_score[score_val]
        # Calculate tie conditions for the group
        is_tied = len(group) > 1
        group_style_names = [r["style_data"]["name"] for r in group]
        
        for r in group:
            sd   = r["style_data"]
            cont = r["contributions"]
            style_name = sd["name"]
            
            # If tied, tied_with should include everyone in the group Except itself
            tied_with = [s for s in group_style_names if s != style_name] if is_tied else []

            evaluations.append(
                ArchitectureEvaluation(
                    style            = ArchitectureStyle(style_name),
                    raw_score        = r["raw_score"],
                    normalized_score = r["normalized"],
                    rank             = current_rank,
                    is_tied          = is_tied,
                    tied_with        = tied_with,
                    quality_contributions = QualityContributions(
                        Security        = cont[QualityAttribute.SECURITY.value],
                        Scalability     = cont[QualityAttribute.SCALABILITY.value],
                        Performance     = cont[QualityAttribute.PERFORMANCE.value],
                        Reliability     = cont[QualityAttribute.RELIABILITY.value],
                        Maintainability = cont[QualityAttribute.MAINTAINABILITY.value],
                        Availability    = cont[QualityAttribute.AVAILABILITY.value],
                    ),
                    strengths  = sd.get("strengths",  []),
                    weaknesses = sd.get("weaknesses", []),
                    tradeoffs  = sd.get("tradeoffs",  []),
                )
            )
        # Advance rank by the number of items in this tie block (e.g. 1, 1, 3, 4, 5)
        # Alternatively, we could do dense ranking (1, 1, 2, 3, 4).
        # We'll use dense ranking (current_rank += 1) for cleaner UI presentation.
        current_rank += 1

    return evaluations



# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _derive_weights(profile: QualityProfile) -> Dict[str, float]:
    """
    Convert raw ASR counts into normalised quality weights.

    Returns a dict keyed by attribute name (string) with float values in [0, 1]
    that sum to 1.0.  Attributes with count = 0 receive weight 0.
    """
    counts: Dict[str, int] = profile.model_dump()
    total_active: int = sum(counts.values())

    if total_active == 0:
        # Degenerate case: use uniform weights
        uniform = round(1.0 / len(QualityAttribute), 6)
        return {attr.value: uniform for attr in QualityAttribute}

    return {
        attr.value: round(counts[attr.value] / total_active, 6)
        for attr in QualityAttribute
    }
