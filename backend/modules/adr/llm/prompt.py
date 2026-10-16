"""
Prompt construction for AI-assisted ADR generation.

The prompt instructs the LLM to produce an explainable ADR draft
strictly grounded in evidence received from upstream DesignTrace AI
modules.
"""

import json

from modules.adr.evidence_aggregator import ADREvidencePackage


def build_adr_generation_prompt(
    evidence: ADREvidencePackage,
) -> str:
    """
    Build a grounded prompt for ADR generation.
    """

    evidence_json = json.dumps(
        evidence.model_dump(mode="json"),
        indent=2,
    )

    return f"""
You are the Architecture Decision Records module in DesignTrace AI.

Your task is to create a clear and explainable Architecture Decision
Record using only the supplied design-decision evidence.

SOURCE EVIDENCE:
{evidence_json}

Rules:
- Do not invent requirements, components, risks, alternatives, or evidence.
- Preserve the meaning of the selected decision.
- Use only information supported by the supplied evidence.
- Explain why the selected option was preferred.
- Preserve the alternatives that were actually considered.
- Preserve reasons for rejecting alternatives.
- Clearly express benefits, risks, consequences, and trade-offs.
- Do not create requirement IDs or design-element IDs.
- Do not create an ADR ID.
- Do not change the project ID or source decision ID.
- Keep the output concise and suitable for a software architecture record.
- Return structured JSON only.

Return these fields:
- title
- context
- decision
- rationale
- alternatives
- rejected_alternative_reasons
- decision_criteria
- benefits
- risks
- consequences
- trade_offs
"""