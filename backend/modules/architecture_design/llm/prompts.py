"""
LLM Prompts – Milestone 4.

Builds the prompt that enforces the strict rule: the LLM must explain the
deterministic Rank 1 architecture, citing evidence, and not invent its own scores.
"""

from __future__ import annotations

from typing import List

from ..schemas import (
    ASRBatch,
    ArchitectureEvaluation,
    QualityProfile,
    RetrievedEvidence,
)


def build_recommendation_prompt(
    batch: ASRBatch,
    profile: QualityProfile,
    evaluations: List[ArchitectureEvaluation],
    evidence: List[RetrievedEvidence],
) -> str:
    """
    Construct the final grounding prompt for the LLM.
    
    Args:
        batch: Original user requirements.
        profile: The derived quality profile counts.
        evaluations: Deterministically scored and ranked architectures.
        evidence: The top RAG-retrieved knowledge items.
        
    Returns:
        A strictly formatted text prompt ready for the LLM.
    """
    
    # 1. Format Requirements
    reqs_text = "\n".join(f"- [{asr.requirement_id}] {asr.statement}" for asr in batch.asrs)
    
    # 2. Format Profile
    profile_counts = profile.model_dump()
    active_qas = [f"- {qa}: {count}" for qa, count in profile_counts.items() if count > 0]
    profile_text = "\n".join(active_qas) if active_qas else "No specific quality attributes detected."
    
    # 3. Format Evaluations (Ranks)
    # They should already be sorted by rank, but let's ensure it.
    sorted_evals = sorted(evaluations, key=lambda e: e.rank)
    evals_text_parts = []
    for ev in sorted_evals:
        chunk = (
            f"{ev.rank}. {ev.style.value} (Score: {ev.normalized_score:.1f})\n"
            f"   Strengths: {', '.join(ev.strengths)}\n"
            f"   Weaknesses: {', '.join(ev.weaknesses)}"
        )
        evals_text_parts.append(chunk)
    evals_text = "\n\n".join(evals_text_parts)
    
    # 4. Format Evidence
    if not evidence:
        evidence_text = "(No supporting evidence found. Rely entirely on the Evaluations section above.)"
    else:
        evidence_parts = []
        for ev in evidence:
            part = (
                f"[{ev.knowledge_id}] {ev.title}\n"
                f"Styles: {', '.join(ev.architecture_styles)}\n"
                f"QAs: {', '.join(ev.quality_attributes)}\n"
                f"Content: {ev.content}"
            )
            evidence_parts.append(part)
        evidence_text = "\n\n---\n".join(evidence_parts)

    # Note: Using precise, imperative language to limit hallucinations
    # and override LLM pre-training bias.
    
    # 5. Add Tie-Handling context if needed
    rank_1_evals = [e for e in sorted_evals if e.rank == 1]
    is_tied = len(rank_1_evals) > 1
    tie_instructions = ""
    if is_tied:
        tie_instructions = (
            f"\nATTENTION! MULTIPLE ARCHITECTURES TIED FOR RANK 1: {', '.join(e.style.value for e in rank_1_evals)}\n"
            "CRITICAL TIE-BREAKING RULES:\n"
            "a. You MUST populate the `tied_candidates` array with these names.\n"
            "b. If multiple architectures share Rank 1, do not pretend one won numerically. Their scores are identical.\n"
            "c. You may recommend one ONLY when the supplied requirements or retrieved evidence provide a meaningful distinguishing factor.\n"
            "d. If you successfully resolve the tie using project constraints, set `tie_resolved=true` and provide a `tie_resolution_reason`.\n"
            "e. If the evidence is insufficient to cleanly resolve the tie, set `review_required=true`, `tie_resolved=false` and explain the unresolved tie.\n"
        )
    
    prompt = f"""You are an expert Software Architecture Decision Assistant.
Your task is to explain and document the architecture selection for the project.

CRITICAL RULES:
1. The architecture styles have ALREADY been evaluated and scored using a strict deterministic algorithm.
2. DO NOT change the scores, ranks, or invent new scores.
3. The selected architecture MUST be the one ranked #1 in the Evaluations section below.
4. If (and only if) the Retrieved Evidence provides a severe, overriding conflict against the Rank 1 architecture, you may set "review_required" to true in your JSON response. Even then, you must still document the Rank 1 architecture as the selected one.
5. Base your rationale heavily on the provided "Retrieved Evidence". Cite the exact IDs (e.g. KB-012).
6. Explain why the strongest alternatives (e.g. Rank 2, Rank 3) were NOT selected.
{tie_instructions}
--- PROJECT REQUIREMENTS (ASRs) ---
{reqs_text}

--- QUALITY PROFILE SENSITIVITY ---
{profile_text}

--- DETERMINISTIC ARCHITECTURE EVALUATIONS ---
{evals_text}

--- RETRIEVED ARCHITECTURE KNOWLEDGE (EVIDENCE) ---
{evidence_text}

--- INSTRUCTIONS ---
Using ONLY the information provided above, generate your final structured recommendation.
Return the output as valid JSON matching the exact schema requested.
"""
    return prompt
