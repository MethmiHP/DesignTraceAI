# Validates SBERT-generated candidate traceability links
# using Gemini contextual reasoning.

# All candidate artifacts for one requirement are validated
# together in a single LLM request to reduce API usage.

import json
import re

from modules.traceability.schemas import (
    TraceabilityRequirement,
    CandidateTraceLink,
    NormalizedArtifact,
    TraceLink,
)

from modules.traceability.traceability_llm_client import (
    get_traceability_llm_client,
)


class TraceabilityValidator:

    def __init__(self):
        self.llm_client = (
            get_traceability_llm_client()
        )

    def validate_requirement_candidates(
        self,
        requirement: TraceabilityRequirement,
        candidates: list[CandidateTraceLink],
        artifacts: list[NormalizedArtifact],
    ) -> list[TraceLink]:
        """
        Validates all candidate artifacts for one requirement
        using one Gemini request.
        """

        if not candidates:
            return []

        # ====================================================
        # CREATE ARTIFACT LOOKUP
        # ====================================================

        artifact_lookup = {
            artifact.artifact_id: artifact
            for artifact in artifacts
        }

        # ====================================================
        # BUILD CANDIDATE DATA FOR GEMINI
        # ====================================================

        candidate_data = []

        for candidate in candidates:

            artifact = artifact_lookup.get(
                candidate.artifact_id
            )

            if artifact is None:
                continue

            candidate_data.append(
                {
                    "artifact_id":
                        artifact.artifact_id,

                    "artifact_type":
                        artifact.artifact_type,

                    "name":
                        artifact.name,

                    "description":
                        artifact.description,

                    "semantic_similarity":
                        candidate.semantic_similarity,
                }
            )

        if not candidate_data:
            return []

        # ====================================================
        # BUILD PROMPT
        # ====================================================

        prompt = self._build_prompt(
            requirement=requirement,
            candidate_data=candidate_data,
        )

        # ====================================================
        # CALL GEMINI
        # ====================================================

        response_text = (
            self.llm_client.generate(
                prompt
            )
        )

        # ====================================================
        # PARSE RESPONSE
        # ====================================================

        validation_results = (
            self._parse_json_response(
                response_text
            )
        )

        # ====================================================
        # CREATE TRACE LINKS
        # ====================================================

        candidate_lookup = {
            candidate.artifact_id: candidate
            for candidate in candidates
        }

        trace_links = []

        for result in validation_results:

            artifact_id = result.get(
                "artifact_id"
            )

            candidate = candidate_lookup.get(
                artifact_id
            )

            artifact = artifact_lookup.get(
                artifact_id
            )

            if (
                candidate is None
                or artifact is None
            ):
                continue

            link_valid = bool(
                result.get(
                    "link_valid",
                    False,
                )
            )

            confidence = (
                self._normalize_confidence(
                    result.get(
                        "confidence",
                        0.0,
                    )
                )
            )

            rationale = str(
                result.get(
                    "rationale",
                    "",
                )
            ).strip()

            trace_links.append(
                TraceLink(
                    requirement_id=
                        requirement.requirement_id,

                    artifact_id=
                        artifact.artifact_id,

                    artifact_type=
                        artifact.artifact_type,

                    link_valid=
                        link_valid,

                    semantic_similarity=
                        candidate.semantic_similarity,

                    confidence=
                        confidence,

                    rationale=
                        rationale,
                )
            )

        return trace_links

    def _build_prompt(
        self,
        requirement: TraceabilityRequirement,
        candidate_data: list[dict],
    ) -> str:
        """
        Builds the Gemini prompt for validating candidate
        requirement-to-design traceability links.
        """

        candidates_json = json.dumps(
            candidate_data,
            indent=2,
        )

        return f"""
You are validating requirement-to-design traceability links
for a software engineering system.

Your task is to determine whether each candidate design
artifact has a genuine and meaningful software-design
relationship with the requirement.

IMPORTANT TRACEABILITY DEFINITION:

A candidate artifact should be marked VALID when at least one
of the following is true:

1. The artifact directly implements or realizes the
   requirement.

2. The artifact provides data that is necessary or
   meaningfully used to realize the requirement.

3. The artifact enables, supports, protects, controls, or
   facilitates the requirement through a concrete design role.

4. The artifact represents an architectural, database, API,
   or component-level design element that would reasonably be
   traced to the requirement during software design.

A candidate does NOT need to directly execute the required
functionality in order to be a valid traceability link.

For example:

- A requirement about appointment reminders may validly trace
  to an Appointment database entity because reminder
  generation depends on stored appointment information.

- A security requirement may validly trace to an
  authentication API because authentication controls access
  to protected information.

- A security requirement may validly trace to an AuditLog
  database entity when auditing provides accountability,
  monitoring, or security-related traceability.

However, do NOT mark a candidate valid merely because:

- it contains similar words,
- it belongs to the same general workflow,
- it is only loosely related,
- or it has no concrete role in realizing or supporting the
  requirement.

You must distinguish meaningful design support from simple
topic similarity.

IMPORTANT BOUNDARY RULE:

Do NOT mark a link valid merely because the artifact occurs
earlier in the same business workflow or indirectly causes
related data to exist.

A supporting artifact must have a concrete design role that is
actually used by the implementation of the requirement itself.

Examples:

- Appointment database -> appointment reminder requirement:
  VALID, because reminder generation depends on stored
  appointment details such as date, time, and patient data.

- Appointment creation API -> appointment reminder requirement:
  INVALID, because creating an appointment is a separate
  upstream operation. It does not itself implement, store, or
  deliver the reminder functionality.

- Authentication API -> patient information security:
  VALID, because authentication directly controls access to
  protected information.

- Audit log -> patient information security:
  VALID, because auditing provides concrete accountability and
  monitoring support for the security requirement.
Requirement:

EVENT-TRIGGER RULE:

A design artifact can be a valid traceability link when it
produces, changes, or publishes the event/state that directly
triggers the requirement.

Example:

- GradeManagementComponent -> notification when grades are published:
  VALID, because publishing the grade is the explicit triggering event
  for the notification requirement.

However, a general upstream workflow action is still INVALID if it
does not directly produce the event/state named in the requirement.


IDENTITY VS AUTHORIZATION RULE:

Do NOT assume that storing user identity or profile data automatically
implements authorization.

A database artifact should be considered authorization/security-related
only when its description indicates a concrete role such as:

- credentials
- roles
- permissions
- access-control data
- authorization state
- security policy data
- protected-resource enforcement

Example:

- Student profile/account database -> authorized grade access:
  INVALID when it only stores identity/profile information and does
  not store roles, permissions, credentials, or authorization data.
  
ID: {requirement.requirement_id}
Type: {requirement.requirement_type}
Statement: {requirement.statement}
ASR: {requirement.asr}

Candidate design artifacts:

{candidates_json}

For EACH candidate artifact return:

- artifact_id
- link_valid: true or false
- confidence: number between 0.0 and 1.0
- rationale: short explanation of the concrete design
  relationship, or why no meaningful relationship exists

Return ONLY a valid JSON array.

Example output:

[
  {{
    "artifact_id": "ARCH-001",
    "link_valid": true,
    "confidence": 0.92,
    "rationale": "The appointment service directly implements appointment booking."
  }},
  {{
    "artifact_id": "DB-002",
    "link_valid": true,
    "confidence": 0.88,
    "rationale": "The appointment entity stores the appointment data needed to support reminder generation."
  }},
  {{
    "artifact_id": "COMP-002",
    "link_valid": false,
    "confidence": 0.90,
    "rationale": "The doctor search component has no concrete role in implementing or supporting this requirement."
  }}
]
""".strip()

    def _parse_json_response(
        self,
        response_text: str,
    ) -> list[dict]:
        """
        Parses the Gemini response text as JSON
        and validates the structure.
        """

        cleaned = (
            response_text.strip()
        )

        cleaned = re.sub(
            r"^```(?:json)?",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"```$",
            "",
            cleaned,
        )

        cleaned = (
            cleaned.strip()
        )

        try:
            data = json.loads(
                cleaned
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                "Gemini returned invalid JSON "
                "for traceability validation."
            ) from error

        if not isinstance(
            data,
            list,
        ):

            raise ValueError(
                "Gemini traceability response "
                "must be a JSON array."
            )

        return data

    def _normalize_confidence(
        self,
        confidence,
    ) -> float:
        """
        Normalizes confidence to a float
        between 0.0 and 1.0.
        """

        try:
            value = float(
                confidence
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

        value = max(
            0.0,
            min(
                1.0,
                value,
            )
        )

        return round(
            value,
            4,
        )