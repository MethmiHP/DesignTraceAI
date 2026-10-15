# Main orchestration service for the Traceability Module.

# Production pipeline:

# Requirements + Design Artifacts
# -> Normalize artifacts
# -> SBERT semantic similarity
# -> Candidate ranking
# -> Candidate expansion
# -> Gemini contextual validation
# -> Deterministic filtering
# -> Traceability matrix
# -> Coverage summary
# -> Validation
# -> Save JSON result
# -> TraceabilityResponse


import json
from pathlib import Path

from modules.traceability.schemas import (
    TraceabilityRequest,
    TraceabilityResponse,
    TraceabilityValidationResult,
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

from modules.traceability.candidate_expander import (
    CandidateExpander,
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


class TraceabilityService:
    
    # Coordinates the complete requirement-to-design
    # traceability workflow.
    

    def __init__(
        self,
        similarity_threshold: float = 0.40,
        minimum_confidence: float = 0.70,
    ):
        
        # Uses the frozen configuration established
        # during traceability evaluation.
        

        # SBERT + cosine similarity retrieval
        self.similarity_service = (
            TraceabilitySimilarityService(
                similarity_threshold=similarity_threshold
            )
        )

        # Rule-based candidate expansion
        self.candidate_expander = (
            CandidateExpander()
        )

        # Gemini contextual validation
        self.validator = (
            TraceabilityValidator()
        )

        # Deterministic filtering
        self.link_filter = (
            TraceLinkFilter(
                minimum_confidence=minimum_confidence
            )
        )

        # Matrix generation
        self.matrix_builder = (
            TraceabilityMatrixBuilder()
        )

        # Coverage calculation
        self.coverage_service = (
            TraceabilityCoverageService()
        )


    # MAIN TRACEABILITY PIPELINE

    def analyze(
        self,
        request: TraceabilityRequest,
    ) -> TraceabilityResponse:
        
        # Runs the complete traceability analysis pipeline.

        # STEP 1 - INPUT VALIDATION

        input_issues = self._validate_input(
            request
        )

        # INVALID INPUT RESPONSE

        if input_issues:

            empty_matrix = (
                self.matrix_builder.build_matrix(
                    requirements=request.requirements,
                    links=[],
                )
            )

            empty_coverage = (
                self.coverage_service.calculate_coverage(
                    empty_matrix
                )
            )

            response = TraceabilityResponse(
                project_id=request.project_id,

                trace_links=[],

                traceability_matrix=empty_matrix,

                coverage_summary=empty_coverage,

                evaluation=None,

                validation=TraceabilityValidationResult(
                    valid=False,
                    issues=input_issues,
                ),
            )

            # Save even invalid results for debugging/history.
            self._save_result(
                response
            )

            return response


        # STEP 2 - NORMALIZE DESIGN ARTIFACTS

        artifacts = normalize_artifacts(
            request
        )


        # STEP 3 - SBERT SEMANTIC RETRIEVAL

        candidates = (
            self.similarity_service
            .generate_candidate_links(
                request=request,
                artifacts=artifacts,
            )
        )


        # STEP 4 - RANK SBERT CANDIDATES

        candidates = rank_candidates(
            candidates
        )

        # STEP 5 - PROCESS EACH REQUIREMENT
        validated_links = []

        for requirement in request.requirements:


            # 5A - GET SBERT CANDIDATES FOR THIS REQUIREMENT

            requirement_candidates = [
                candidate
                for candidate in candidates
                if (
                    candidate.requirement_id
                    == requirement.requirement_id
                )
            ]


            # 5B - EXPAND CANDIDATES

            expanded_candidates = (
                self.candidate_expander
                .expand_candidates(
                    requirement=requirement,

                    current_candidates=
                        requirement_candidates,

                    artifacts=artifacts,
                )
            )


            # 5C - GEMINI CONTEXTUAL VALIDATION

            requirement_links = (
                self.validator
                .validate_requirement_candidates(
                    requirement=requirement,

                    candidates=
                        expanded_candidates,

                    artifacts=artifacts,
                )
            )

            validated_links.extend(
                requirement_links
            )


        # STEP 6 - DETERMINISTIC LINK FILTERING

        final_links = (
            self.link_filter.filter_links(
                links=validated_links,
                artifacts=artifacts,
            )
        )


        # STEP 7 - BUILD TRACEABILITY MATRIX

        traceability_matrix = (
            self.matrix_builder.build_matrix(
                requirements=request.requirements,
                links=final_links,
            )
        )


        # STEP 8 - CALCULATE COVERAGE

        coverage_summary = (
            self.coverage_service
            .calculate_coverage(
                traceability_matrix
            )
        )


        # STEP 9 - VALIDATE FINAL OUTPUT

        output_issues = (
            self._validate_output(
                request=request,
                artifacts=artifacts,
                final_links=final_links,
                matrix=traceability_matrix,
            )
        )

        validation_result = (
            TraceabilityValidationResult(
                valid=(
                    len(output_issues) == 0
                ),
                issues=output_issues,
            )
        )


        # STEP 10 - CREATE RESPONSE

        response = TraceabilityResponse(
            project_id=request.project_id,

            trace_links=final_links,

            traceability_matrix=
                traceability_matrix,

            coverage_summary=
                coverage_summary,

            # Evaluation metrics require human-reviewed
            # gold labels, so they are not calculated
            # during normal application execution.
            evaluation=None,

            validation=
                validation_result,
        )


        # STEP 11 - SAVE RESULT LOCALLY

        self._save_result(
            response
        )


        # STEP 12 - RETURN RESPONSE
        return response


    # INPUT VALIDATION

    def _validate_input(
        self,
        request: TraceabilityRequest,
    ) -> list[str]:
        """
        Checks whether the request contains enough
        information for traceability analysis.
        """

        issues = []


        # PROJECT ID

        if not request.project_id.strip():

            issues.append(
                "Project ID is required."
            )


        # REQUIREMENTS
        if not request.requirements:

            issues.append(
                "At least one requirement is required."
            )


        # DESIGN ARTIFACTS

        total_artifacts = (
            len(
                request.architecture.elements
            )
            + len(
                request.database.entities
            )
            + len(
                request.api.operations
            )
            + len(
                request.components
            )
        )

        if total_artifacts == 0:

            issues.append(
                "At least one design artifact is required."
            )


        # DUPLICATE REQUIREMENT IDS

        requirement_ids = [
            requirement.requirement_id
            for requirement
            in request.requirements
        ]

        if (
            len(requirement_ids)
            != len(set(requirement_ids))
        ):

            issues.append(
                "Duplicate requirement IDs were found."
            )


        # DUPLICATE ARTIFACT IDS

        artifact_ids = []

        artifact_ids.extend(
            artifact.artifact_id
            for artifact
            in request.architecture.elements
        )

        artifact_ids.extend(
            artifact.artifact_id
            for artifact
            in request.database.entities
        )

        artifact_ids.extend(
            artifact.artifact_id
            for artifact
            in request.api.operations
        )

        artifact_ids.extend(
            artifact.artifact_id
            for artifact
            in request.components
        )

        if (
            len(artifact_ids)
            != len(set(artifact_ids))
        ):

            issues.append(
                "Duplicate artifact IDs were found."
            )

        return issues


    # OUTPUT VALIDATION

    def _validate_output(
        self,
        request,
        artifacts,
        final_links,
        matrix,
    ) -> list[str]:
        """
        Checks consistency of the generated
        traceability result.
        """

        issues = []

        valid_requirement_ids = {
            requirement.requirement_id
            for requirement
            in request.requirements
        }

        valid_artifact_ids = {
            artifact.artifact_id
            for artifact
            in artifacts
        }


        # VALIDATE TRACE LINKS
        for link in final_links:

            if (
                link.requirement_id
                not in valid_requirement_ids
            ):

                issues.append(
                    "Trace link contains unknown "
                    f"requirement ID: "
                    f"{link.requirement_id}"
                )

            if (
                link.artifact_id
                not in valid_artifact_ids
            ):

                issues.append(
                    "Trace link contains unknown "
                    f"artifact ID: "
                    f"{link.artifact_id}"
                )


        # MATRIX ROW COUNT

        if (
            len(matrix)
            != len(request.requirements)
        ):

            issues.append(
                "Traceability matrix does not contain "
                "exactly one row per requirement."
            )


        # MATRIX REQUIREMENT IDS
        matrix_requirement_ids = {
            row.requirement_id
            for row in matrix
        }

        if (
            matrix_requirement_ids
            != valid_requirement_ids
        ):

            issues.append(
                "Traceability matrix requirement IDs "
                "do not match the input requirements."
            )

        return issues

    # SAVE RESULT TO JSON

    def _save_result(
        self,
        response: TraceabilityResponse,
    ) -> None:
       
        # Saves the generated traceability response as JSON.

        # This provides temporary local persistence until
        # database storage is connected.
        

        # FIND BACKEND ROOT

        backend_root = (
            Path(__file__)
            .resolve()
            .parents[2]
        )

        # OUTPUT DIRECTORY
        output_directory = (
            backend_root
            / "outputs"
            / "traceability"
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        # SAFE PROJECT ID FOR FILE NAME
        safe_project_id = (
            response.project_id
            .strip()
            .replace("/", "_")
            .replace("\\", "_")
        )

        if not safe_project_id:
            safe_project_id = "unknown_project"


        # FILE PATH

        file_path = (
            output_directory
            / (
                f"{safe_project_id}"
                "_traceability_result.json"
            )
        )

        # WRITE JSON

        with open(
            file_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                response.model_dump(),
                file,
                indent=4,
                ensure_ascii=False,
            )

        print(
            f"Traceability result saved to: "
            f"{file_path}"
        )


# SHARED SERVICE INSTANCE

_traceability_service = None


def get_traceability_service():
    
    # Returns one shared TraceabilityService instance.

    # This avoids rebuilding the SBERT-related services
    # for every API request.
    

    global _traceability_service

    if _traceability_service is None:

        _traceability_service = (
            TraceabilityService()
        )

    return _traceability_service