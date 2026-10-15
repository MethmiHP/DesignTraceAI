# Expands SBERT-generated traceability candidates using
# deterministic software-design rules.

# This layer helps recover meaningful design relationships
# that semantic similarity alone may miss.

# The rules are domain-independent and focus on:
# 1. Security / access-control relationships
# 2. Protected-resource relationships

import re

from modules.traceability.schemas import (
    TraceabilityRequirement,
    CandidateTraceLink,
    NormalizedArtifact,
)


class CandidateExpander:

    def expand_candidates(
        self,
        requirement: TraceabilityRequirement,
        current_candidates: list[CandidateTraceLink],
        artifacts: list[NormalizedArtifact],
    ) -> list[CandidateTraceLink]:
        """
        Adds rule-supported candidate links that may have
        low SBERT similarity.

        Existing SBERT candidates are always preserved.
        """

        expanded = list(
            current_candidates
        )

        existing_pairs = {
            (
                candidate.requirement_id,
                candidate.artifact_id,
            )
            for candidate in expanded
        }

        requirement_text = (
            requirement.statement
            .lower()
        )


        # SECURITY / ACCESS-CONTROL REQUIREMENT DETECTION

        security_requirement_terms = {
            "secure",
            "security",
            "protect",
            "protected",
            "protection",
            "privacy",
            "confidential",
            "confidentiality",
            "authenticate",
            "authenticated",
            "authentication",
            "authorize",
            "authorized",
            "authorization",
            "unauthorized",
            "access",
            "access control",
            "permission",
            "permissions",
            "role",
            "roles",
            "credential",
            "credentials",
        }

        is_security_requirement = any(
            term in requirement_text
            for term in security_requirement_terms
        )


        # SECURITY-RELATED ARTIFACT TERMS
        security_artifact_terms = {
            "security",
            "secure",
            "authentication",
            "authenticate",
            "authenticated",
            "authorization",
            "authorize",
            "authorized",
            "access control",
            "access",
            "permission",
            "permissions",
            "role",
            "roles",
            "credential",
            "credentials",
            "login",
            "audit",
            "audit log",
            "audit record",
            "encryption",
            "encrypt",
            "privacy",
            "protection",
            "protect",
        }


        # EXPAND SECURITY CANDIDATES

        if is_security_requirement:

            for artifact in artifacts:

                artifact_text = (
                    artifact.normalized_text
                    .lower()
                )

                if any(
                    term in artifact_text
                    for term in security_artifact_terms
                ):

                    self._add_candidate(
                        requirement=requirement,
                        artifact=artifact,
                        expanded=expanded,
                        existing_pairs=existing_pairs,
                    )


        # PROTECTED RESOURCE EXPANSION

        if is_security_requirement:

            resource_terms = (
                self._extract_resource_terms(
                    requirement_text
                )
            )

            for artifact in artifacts:

                artifact_text = (
                    artifact.normalized_text
                    .lower()
                )

                if any(
                    resource_term
                    in artifact_text
                    for resource_term
                    in resource_terms
                ):

                    self._add_candidate(
                        requirement=requirement,
                        artifact=artifact,
                        expanded=expanded,
                        existing_pairs=existing_pairs,
                    )


        # SORT FOR CONSISTENT OUTPUT

        expanded.sort(
            key=lambda candidate: (
                candidate.requirement_id,
                -candidate.semantic_similarity,
                candidate.artifact_id,
            )
        )

        return expanded


    # ADD RULE-BASED CANDIDATE

    def _add_candidate(
        self,
        requirement: TraceabilityRequirement,
        artifact: NormalizedArtifact,
        expanded: list[CandidateTraceLink],
        existing_pairs: set,
    ):
        """
        Adds a candidate only if it does not already exist.

        Rule-added candidates use semantic_similarity=0.0
        because we do not fabricate a cosine similarity score.
        """

        pair = (
            requirement.requirement_id,
            artifact.artifact_id,
        )

        if pair in existing_pairs:
            return

        expanded.append(
            CandidateTraceLink(
                requirement_id=
                    requirement.requirement_id,

                artifact_id=
                    artifact.artifact_id,

                artifact_type=
                    artifact.artifact_type,

                semantic_similarity=
                    0.0,
            )
        )

        existing_pairs.add(
            pair
        )


    # EXTRACT PROTECTED RESOURCE TERMS

    def _extract_resource_terms(
        self,
        requirement_text: str,
    ) -> set[str]:
        """
        Extracts meaningful domain/resource words from a
        security or access-control requirement.

        Example:

        "Only authorized users shall access student grades."

        produces useful resource terms such as:

        student
        grades
        grade

        These terms help include artifacts representing the
        protected resource itself.
        """

        words = re.findall(
            r"[a-zA-Z]+",
            requirement_text.lower(),
        )

        stop_words = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "be",
            "by",
            "for",
            "from",
            "has",
            "have",
            "in",
            "is",
            "it",
            "of",
            "on",
            "only",
            "or",
            "shall",
            "should",
            "that",
            "the",
            "their",
            "to",
            "using",
            "user",
            "users",
            "with",

            # Security words themselves are not resource names.
            "secure",
            "security",
            "protect",
            "protected",
            "protection",
            "privacy",
            "confidential",
            "confidentiality",
            "authenticate",
            "authenticated",
            "authentication",
            "authorize",
            "authorized",
            "authorization",
            "unauthorized",
            "access",
            "control",
            "permission",
            "permissions",
            "role",
            "roles",
            "credential",
            "credentials",
        }

        resource_terms = set()

        for word in words:

            if (
                word in stop_words
                or len(word) < 4
            ):
                continue

            resource_terms.add(
                word
            )

            # Simple plural handling:
            # grades -> grade
            # students -> student
            if (
                word.endswith("s")
                and len(word) > 4
            ):

                resource_terms.add(
                    word[:-1]
                )

        return resource_terms