# Builds the structured prompt used by Gemini for requirement extraction
# and contextual requirement-quality analysis.
#
# Gemini responsibilities:
# - Extract atomic requirements
# - Normalize requirement statements
# - Detect ASRs
# - Detect contextual quality issues
#
# RoBERTa responsibilities:
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
        ensure_ascii=False
    )

    rules_json = json.dumps(
        rule_findings or {},
        ensure_ascii=False
    )

    return f"""
You are a software requirements engineering assistant.

Analyse the supplied project description and return structured JSON only.

PROJECT CONTEXT:
{context_json}

PROJECT DESCRIPTION:
{raw_description}

DETERMINISTIC RULE FINDINGS:
{rules_json}

TASK 1 - EXTRACT ATOMIC REQUIREMENTS

Extract every explicit software requirement from the complete project
description.

Each independently implementable or independently testable obligation
must be returned as a separate requirement object.

Important atomic-decomposition rules:

- One independent obligation = one requirement object.
- Split compound requirements when one statement contains multiple
  independent actions, capabilities, constraints, or quality goals.
- Conjunctions such as "and", "or", commas, and lists may indicate
  multiple requirements when the individual parts can be implemented
  or tested separately.
- Do not split wording when all parts are necessary to describe one
  inseparable operation.
- Do not invent requirements that are not supported by the source text.
- Do not treat introductory project context as an explicit requirement
  unless it contains a clear system obligation.
- Analyse the entire project description before returning results.

Examples:

Input:
"Patients shall be able to book, reschedule, or cancel appointments."

Return three requirements:
1. Patients shall be able to book appointments.
2. Patients shall be able to reschedule appointments.
3. Patients shall be able to cancel appointments.

Input:
"Doctors shall be able to view appointment schedules and update their
available time slots."

Return two requirements:
1. Doctors shall be able to view appointment schedules.
2. Doctors shall be able to update their available time slots.

Input:
"The system shall encrypt sensitive data during transmission."

Return one requirement only.

Input:
"The system shall support 500 concurrent users."

Return one requirement only.

Do not convert introductory project context, actor lists, or domain descriptions
into requirements unless they explicitly state a system obligation.

Example:

Input:
"A hospital appointment management system is required for patients,
doctors, and administrators."

Do not create a requirement from this sentence alone.

Also split a statement when it contains independent quality concerns.

Example:

Input:
"The user interface should be easy to use on both desktop and mobile devices."

Return:
1. The user interface shall be easy to use.
2. The system shall support use on desktop and mobile devices.

TASK 2 - NORMALIZE EACH REQUIREMENT

For every extracted requirement:

- Preserve the original meaning.
- Rewrite it as a clear software requirement.
- Do not add functionality, constraints, actors, or numerical values
  that are not present in the source.
- Keep the normalized statement atomic.

Preferred wording:

"The system shall ..."

or

"[Actor] shall be able to ..."

TASK 3 - ARCHITECTURALLY SIGNIFICANT REQUIREMENTS

For each requirement determine whether it is architecturally significant.

Set asr = true when the requirement has important architectural impact,
for example:

- security
- privacy
- performance
- scalability
- availability
- reliability
- integration
- persistence
- deployment
- major data-management decisions
- technology constraints

Otherwise set asr = false.

TASK 4 - REQUIREMENT QUALITY ANALYSIS

For every requirement analyse:

ambiguous:
true only when wording is vague, subjective, unclear, or open to
multiple interpretations.

incomplete:
true only when important information needed to understand or implement
the requirement is genuinely missing.

conflicting:
true only when the requirement contradicts another supplied requirement
or project statement.

potentially_missing:
true only when the supplied context strongly indicates that an important
related requirement is absent.

TASK 5 - ISSUE DETAILS

If a quality issue exists, add an issue_details entry containing:

- issue_type
- evidence
- rationale
- recommendation

Allowed issue types:

- ambiguity
- incompleteness
- conflict
- potentially_missing

If there are no issues, return an empty issue_details array.

IMPORTANT

- Do not generate requirement IDs.
- Do not return Markdown.
- Return JSON only.
- Do not add unsupported information.
- Every explicit requirement must appear exactly once.
- Do not merge independent obligations.
- Do not create requirements from general background/context statements.

FR/NFR classification and NFR quality-attribute classification are
performed later by trained RoBERTa models.

The fields requirement_type and quality_attribute are retained only for
response-schema compatibility and are replaced by backend classifier
results.

Return this structure:

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
"""