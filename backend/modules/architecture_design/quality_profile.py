"""
Quality Profile builder – Milestone 1.

Takes the list of per-ASR classification results and aggregates them into
a project-level QualityProfile.  Every attribute is always present in the
output (count = 0 when no ASR matched it).
"""

from __future__ import annotations

from typing import List

from .schemas import ASRClassification, QualityAttribute, QualityProfile


def build_profile(classifications: List[ASRClassification]) -> QualityProfile:
    """
    Aggregate per-ASR quality-attribute hits into a project-level profile.

    An attribute's count is incremented once per ASR that carries it,
    regardless of how many keywords matched within that ASR.

    Args:
        classifications: list of ASRClassification objects (one per ASR).

    Returns:
        QualityProfile with counts for all six attributes.
    """
    counts: dict[str, int] = {attr.value: 0 for attr in QualityAttribute}

    for asr_class in classifications:
        # De-duplicate: count each attribute at most once per ASR
        seen: set[str] = set()
        for hit in asr_class.quality_attributes:
            attr_name = hit.name.value
            if attr_name not in seen:
                counts[attr_name] += 1
                seen.add(attr_name)

    return QualityProfile(
        Security        = counts[QualityAttribute.SECURITY.value],
        Scalability     = counts[QualityAttribute.SCALABILITY.value],
        Performance     = counts[QualityAttribute.PERFORMANCE.value],
        Reliability     = counts[QualityAttribute.RELIABILITY.value],
        Maintainability = counts[QualityAttribute.MAINTAINABILITY.value],
        Availability    = counts[QualityAttribute.AVAILABILITY.value],
    )
