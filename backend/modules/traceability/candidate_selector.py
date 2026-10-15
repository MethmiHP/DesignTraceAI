# Ranks SBERT candidate links for each requirement
# without removing potentially valid candidates.

from collections import defaultdict

from modules.traceability.schemas import (
    CandidateTraceLink,
)


def rank_candidates(
    candidates: list[CandidateTraceLink],
) -> list[CandidateTraceLink]:

    # Groups candidates by requirement and ranks
    # all candidates by semantic similarity.

    grouped = defaultdict(list)

    for candidate in candidates:
        grouped[
            candidate.requirement_id
        ].append(candidate)

    ranked_candidates = []

    for requirement_id, links in grouped.items():

        ranked_links = sorted(
            links,
            key=lambda link:
                link.semantic_similarity,
            reverse=True
        )

        ranked_candidates.extend(
            ranked_links
        )

    ranked_candidates.sort(
        key=lambda link: (
            link.requirement_id,
            -link.semantic_similarity
        )
    )

    return ranked_candidates