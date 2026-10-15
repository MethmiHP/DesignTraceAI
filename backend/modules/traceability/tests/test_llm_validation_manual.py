# Manual test for Gemini-based traceability validation
# using one requirement and its candidate design artifacts.

import json

from numpy import matrix

from modules.traceability import coverage_service
from modules.traceability import link_filter
from modules.traceability.schemas import (
    TraceabilityRequest,
)

from modules.traceability.normalizer import (
    normalize_artifacts,
)

from modules.traceability.similarity_service import (
    TraceabilitySimilarityService,
)

from modules.traceability.candidate_selector import (
    rank_candidates,
)

from modules.traceability.traceability_validator import (
    TraceabilityValidator,
)

from modules.traceability.link_filter import (
    TraceLinkFilter,
)

from modules.traceability.matrix_builder import (
    TraceabilityMatrixBuilder,
)

from modules.traceability.coverage_service import (
    TraceabilityCoverageService,
)

def main():

    with open(
        "datasets/traceability/mock_design_artifacts.json",
        "r",
        encoding="utf-8",
    ) as file:
        mock_artifacts = json.load(file)

    request_data = {
        "project_id": "P001",

        "requirements": [
            {
                "requirement_id": "REQ-001",
                "statement":
                    "Patients shall be able to book appointments.",
                "requirement_type": "FR",
                "asr": False,
            }
        ],

        "architecture":
            mock_artifacts["architecture"],

        "database":
            mock_artifacts["database"],

        "api":
            mock_artifacts["api"],

        "components":
            mock_artifacts["components"],
    }

    request = TraceabilityRequest(
        **request_data
    )

    artifacts = normalize_artifacts(
        request
    )

    similarity_service = (
        TraceabilitySimilarityService(
            similarity_threshold=0.40

        )
    )

    candidates = (
        similarity_service.generate_candidate_links(
            request=request,
            artifacts=artifacts,
        )
    )

    ranked_candidates = (
        rank_candidates(
            candidates
        )
    )

    print("\nSBERT candidates:")

    for candidate in ranked_candidates:

        print(
            candidate.requirement_id,
            "->",
            candidate.artifact_id,
            candidate.artifact_type,
            candidate.semantic_similarity,
        )

    validator = TraceabilityValidator()

    requirement = request.requirements[0]

    validated_links = (
        validator.validate_requirement_candidates(
            requirement=requirement,
            candidates=ranked_candidates,
            artifacts=artifacts,
        )
    )

    link_filter = TraceLinkFilter(
    minimum_confidence=0.70
    )

    filtered_links = (
    link_filter.filter_links(
        links=validated_links,
        artifacts=artifacts,
        )
    )


    matrix_builder = TraceabilityMatrixBuilder()

    matrix = matrix_builder.build_matrix(
        requirements=request.requirements,
        links=filtered_links,
   )

    coverage_service = TraceabilityCoverageService()

    coverage_summary = (
        coverage_service.calculate_coverage(
            matrix
        )
    )

    print("\nCoverage summary:")

    print(
        "Total requirements:",
        coverage_summary.total_requirements,
    )

    print(
        "Fully covered:",
        coverage_summary.fully_covered,
    )

    print(
        "Partially covered:",
        coverage_summary.partially_covered,
    )

    print(
        "Uncovered:",
        coverage_summary.uncovered,
    )

    print(
        "Coverage percentage:",
        coverage_summary.coverage_percentage,
    )

    print("\nTraceability matrix:")

    for row in matrix:
        print(
            "\nRequirement:",
            row.requirement_id,
        )

        print(
            "Architecture:",
            row.architecture_links,
        )

        print(
            "Database:",
            row.database_links,
        )

        print(
            "API:",
            row.api_links,
        )

        print(
             "Components:",
            row.component_links,
        )

        print(
            "Coverage:",
            row.coverage_status,
        )

    print("\nFiltered final trace links:")

    for link in filtered_links:
        print(
            link.requirement_id,
            "->",
            link.artifact_id,
            link.artifact_type,
            "confidence=",
            link.confidence,
        )

    print("\nGemini validation results:")

    for link in validated_links:

        print(
            "\nRequirement:",
            link.requirement_id,
        )

        print(
            "Artifact:",
            link.artifact_id,
        )

        print(
            "Type:",
            link.artifact_type,
        )

        print(
            "SBERT similarity:",
            link.semantic_similarity,
        )

        print(
            "Valid:",
            link.link_valid,
        )

        print(
            "Confidence:",
            link.confidence,
        )

        print(
            "Rationale:",
            link.rationale,
        )


if __name__ == "__main__":
    main()