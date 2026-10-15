"""
LLM Prompts for M5 – High-Level Architecture Design Generation.

The architecture style is selected from the identified ASRs, while the
high-level design is generated using all architecture-relevant project
requirements supplied by the Requirement Analysis Module / Coordinator.
"""

from __future__ import annotations

from typing import List

from ..schemas import (
    ArchitectureProjectInput,
    ArchitectureRecommendation,
    QualityProfile,
    RetrievedEvidence,
)


def build_design_prompt(
    project: ArchitectureProjectInput,
    profile: QualityProfile,
    recommendation: ArchitectureRecommendation,
    evidence: List[RetrievedEvidence],
) -> str:
    """Construct the grounded prompt for complete high-level architecture design."""

    requirements_text = "\n".join(
        (
            f"- [{requirement.requirement_id}] "
            f"({requirement.requirement_type.value}) "
            f"{requirement.statement}"
        )
        for requirement in project.requirements
    )

    valid_requirement_ids = [
        requirement.requirement_id
        for requirement in project.requirements
    ]

    asrs_text = "\n".join(
        f"- [{asr.requirement_id}] {asr.statement}"
        for asr in project.asrs
    )

    profile_counts = profile.model_dump()
    active_qas = [
        f"- {qa}: {count}"
        for qa, count in profile_counts.items()
        if count > 0
    ]
    profile_text = (
        "\n".join(active_qas)
        if active_qas
        else "No specific quality attributes detected."
    )

    if not evidence:
        evidence_text = "(No supporting evidence found.)"
    else:
        evidence_parts = []

        for ev in evidence:
            if ev.knowledge_id in recommendation.evidence_ids:
                evidence_parts.append(
                    f"[{ev.knowledge_id}] {ev.title}\n"
                    f"Content: {ev.content}"
                )

        evidence_text = (
            "\n\n---\n".join(evidence_parts)
            if evidence_parts
            else "(No cited evidence available.)"
        )

    prompt = f"""
You are an expert Software Architecture Designer.

Your task is to generate a COMPLETE HIGH-LEVEL LOGICAL ARCHITECTURE for the
project while preserving the architecture style that was already selected by
the Architecture Decision pipeline.

The architecture recommendation was derived from the identified ASRs.
The business/domain structure of the high-level design must now be derived from
ALL supplied architecture-relevant project requirements.

CRITICAL RULES:

1. The selected architecture style is **{recommendation.selected_style}**.
   Do NOT change this architecture style.

2. Use ALL PROJECT REQUIREMENTS to identify the major business capabilities,
   logical services/modules, important data stores, external-facing components,
   and other high-level domain components required by the system.

3. Generate ONLY high-level components. Do not invent implementation-level
   technologies, specific product versions, libraries, frameworks, or
   infrastructure products unless explicitly present in supplied requirements.

4. Every generated component MUST use one grounding type:

   - `requirement_derived`: use for a business/domain component supported by
     one or more supplied PROJECT REQUIREMENTS. It MUST contain one or more
     valid `related_requirements` IDs.

   - `architecture_structural`: use for generic components needed to realize
     the selected architecture style or its quality attributes, such as an API
     Gateway, Load Balancer, Message Broker, Service Discovery, or Monitoring
     component. A direct functional requirement link is optional.

5. NEVER invent domain-specific business capabilities that are not supported by
   the supplied PROJECT REQUIREMENTS.

6. `related_requirements` may contain ONLY IDs from the valid requirement list.

7. Use the ASRs and active quality attributes to shape architecture-level
   mechanisms for security, scalability, performance, reliability,
   maintainability, and availability.

8. Provide logical connections (`source` -> `target`) between generated
   components. Every endpoint must reference a generated component.

9. Keep the architecture high-level and understandable. The goal is an
   architecture diagram, not an implementation deployment plan.

--- ALL PROJECT REQUIREMENTS ---
{requirements_text}

--- IDENTIFIED ARCHITECTURALLY SIGNIFICANT REQUIREMENTS (ASRs) ---
{asrs_text}

VALID REQUIREMENT IDs YOU MAY USE:
{', '.join(valid_requirement_ids)}

--- ACTIVE QUALITY ATTRIBUTES ---
{profile_text}

--- SELECTED ARCHITECTURE RECOMMENDATION ---
Style: {recommendation.selected_style}

Rationale:
{recommendation.rationale}

Trade-offs:
{', '.join(recommendation.tradeoffs)}

--- CITED ARCHITECTURE KNOWLEDGE (RAG EVIDENCE) ---
{evidence_text}

--- OUTPUT INSTRUCTIONS ---
Generate the structured high-level architecture design.
Return valid JSON matching the exact requested schema.
"""

    return prompt.strip()
