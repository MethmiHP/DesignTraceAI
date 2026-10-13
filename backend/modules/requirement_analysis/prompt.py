# IMPORTANT:
# - Do not create requirement IDs.
# - IDs are assigned by deterministic backend logic.
# - Do not return Markdown.
# - Do not wrap JSON inside ``` blocks.
# """

# Builds the structured LLM prompt used to analyze raw software
# project descriptions.
#
# Gemini responsibilities:
# - Extract ALL explicit atomic requirements
# - Normalize requirement statements
# - Detect Architecturally Significant Requirements (ASRs)
# - Detect requirement quality issues
#
# RoBERTa responsibilities are handled later in service.py:
# - FR/NFR classification
# - NFR quality-attribute classification
# - Classification confidence

import json


QUALITY_ATTRIBUTES = [
    "Security",
    "Performance",
    "Scalability",
    "Availability",
    "Reliability",
    "Usability",
    "Maintainability",
    "Interoperability",
    "Portability",
    "Privacy",
    "Auditability",
]


def build_requirement_analysis_prompt(
    raw_description: str,
    project_context: dict,
    rule_findings: dict | None = None
) -> str:

    context_json = json.dumps(
        project_context,
        indent=2
    )

    rules_json = json.dumps(
        rule_findings or {},
        indent=2
    )

    return f"""
You are a software requirements engineering assistant.

Your main responsibility is to extract and analyse ALL software
requirements contained in the supplied raw project description.

PROJECT CONTEXT:
{context_json}

RAW PROJECT DESCRIPTION:
{raw_description}

DETERMINISTIC RULE FINDINGS:
{rules_json}


============================================================
TASK 1 - EXTRACT ALL EXPLICIT REQUIREMENTS
============================================================

Extract EVERY explicit software requirement present in the raw
description.

IMPORTANT EXTRACTION RULES:

- Do NOT stop after the first requirement.
- Read the ENTIRE raw description before producing the result.
- Every independent requirement must appear as a separate object.
- Preserve requirements appearing later in the description.
- Do not omit non-functional requirements such as:
  security, performance, availability, scalability, usability,
  reliability, privacy, maintainability, portability, or integration.
- If the input contains 3 independent requirements, return 3
  requirement objects.
- If the input contains 5 independent requirements, return 5
  requirement objects.
- Do not merge unrelated requirements into one requirement.
- Split compound statements when they contain multiple independent
  obligations.
- Do not invent requirements that are not supported by the input.
- A sentence may contain more than one atomic requirement.
- Multiple sentences may belong to different atomic requirements.

Example:

Input:

"Patients should be able to book appointments online.
The system shall encrypt patient information.
The system should respond within 2 seconds."

Correct extraction:

1. Patients should be able to book appointments online.
2. The system shall encrypt patient information.
3. The system should respond within 2 seconds.

Do NOT return only the first requirement.


============================================================
TASK 2 - NORMALIZE EACH REQUIREMENT
============================================================

For every extracted requirement:

- Keep the meaning of the original statement.
- Rewrite it into clear software requirement language.
- Do not introduce additional functionality.

Preferred forms include:

"The system shall ..."

or

"[Actor] shall be able to ..."

Examples:

Original:
"Patients should be able to book appointments online."

Normalized:
"Patients shall be able to book appointments online."

Original:
"It should load quickly."

Normalized:
"The system shall respond within the stated performance constraint."

Do not invent numerical values that are not present in the input.


============================================================
TASK 3 - ARCHITECTURALLY SIGNIFICANT REQUIREMENTS
============================================================

For every extracted requirement determine whether it is an
Architecturally Significant Requirement (ASR).

ASR is a Boolean value:

true
or
false

ASR is NOT a third requirement type.

A requirement may be architecturally significant when it has major
implications for areas such as:

- security
- privacy
- performance
- scalability
- availability
- reliability
- integration
- persistence
- deployment
- external systems
- architectural structure
- technology constraints
- major data-management decisions

Examples:

"The system shall encrypt all patient records."
May be ASR = true because it affects security architecture.

"The system shall respond within 2 seconds."
May be ASR = true because it may affect performance architecture.

"Patients shall be able to edit their profile."
Usually ASR = false unless the project context indicates otherwise.


============================================================
TASK 4 - REQUIREMENT QUALITY ANALYSIS
============================================================

For every extracted requirement analyse these four quality issues:

1. ambiguous
2. incomplete
3. conflicting
4. potentially_missing

Each value must be either true or false.


AMBIGUOUS
---------

Mark ambiguous = true when the requirement contains unclear,
subjective, vague, or multiple possible interpretations.

Examples of vague terms:

- fast
- user-friendly
- efficient
- adequate
- appropriate
- quickly
- secure enough
- easy to use
- sufficient


INCOMPLETE
----------

Mark incomplete = true only when important information required to
understand or implement the stated requirement is genuinely missing.

Do NOT automatically mark a simple but valid requirement as
incomplete.

For example:

"Patients shall be able to book appointments online."

is a valid functional requirement and should NOT automatically be
marked incomplete merely because it does not describe every booking
workflow detail.


CONFLICTING
-----------

Mark conflicting = true only when the requirement clearly contradicts
another requirement or information present in the supplied description.

Do not claim a conflict unless there is evidence in the provided
project description.


POTENTIALLY MISSING
-------------------

Mark potentially_missing = true only when the supplied project context
or surrounding requirements strongly indicate that an important
related requirement may be absent.

Use this carefully.

Do not invent missing requirements.


============================================================
TASK 5 - ISSUE DETAILS
============================================================

If one or more quality issues are detected, provide issue details.

Each issue detail should contain:

- issue_type
- evidence
- rationale
- recommendation

Allowed issue_type values should normally be:

- ambiguity
- incompleteness
- conflict
- potentially_missing

The evidence should quote or identify the relevant wording from the
requirement.

The rationale should explain why it is an issue.

The recommendation should explain how the requirement could be
improved.

If no quality issue exists, return an empty issue_details array.


============================================================
CLASSIFICATION NOTE
============================================================

The final FR/NFR classification and final NFR quality attribute are
performed by trained RoBERTa classifiers in the backend.

Therefore:

- Do not rely on yourself as the final FR/NFR classifier.
- Do not calculate classification confidence.
- The backend will override any classification-related information.

You may infer requirement meaning when performing ASR and quality
analysis, but your primary responsibility is extraction and quality
analysis.


============================================================
OUTPUT RULES
============================================================

Return JSON only.

Do NOT return Markdown.

Do NOT wrap the result inside ``` blocks.

Do NOT provide explanations outside the JSON.

Do NOT create requirement IDs.

Requirement IDs are assigned later by deterministic backend logic.

Every extracted atomic requirement must be represented exactly once.


Expected JSON structure:

{{
  "requirements": [
    {{
      "original_text": "...",
      "normalized_statement": "...",
      "requirement_type": "FR",
      "quality_attribute": "Security",
      "asr": false,
      "quality_issues": {{
        "ambiguous": false,
        "incomplete": false,
        "conflicting": false,
        "potentially_missing": false
      }},
      "issue_details": []
    }}
  ]
}}


============================================================
FINAL CHECK BEFORE RESPONDING
============================================================

Before returning the JSON:

1. Re-read the full RAW PROJECT DESCRIPTION.
2. Count the independent explicit requirements.
3. Verify that every explicit requirement has a corresponding object.
4. Verify that no requirement was accidentally omitted.
5. Verify that unrelated requirements were not merged.
6. Verify that compound requirements were split when appropriate.
7. Verify that no unsupported requirement was invented.
8. Return the complete requirements array.
"""