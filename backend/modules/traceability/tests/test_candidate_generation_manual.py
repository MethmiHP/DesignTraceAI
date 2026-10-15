# Manual test for traceability candidate generation using
# mock requirements and mock design artifacts.

import json

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

def main():

    with open(
        "datasets/traceability/mock_design_artifacts.json",
        "r",
        encoding="utf-8"
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
                "asr": False
            },
            {
                "requirement_id": "REQ-002",
                "statement":
                    "Patient information shall be secure.",
                "requirement_type": "NFR",
                "asr": True
            },
            {
                "requirement_id": "REQ-003",
                "statement":
                    "Patients shall receive appointment reminders.",
                "requirement_type": "FR",
                "asr": False
            }
        ],

        "architecture":
            mock_artifacts["architecture"],

        "database":
            mock_artifacts["database"],

        "api":
            mock_artifacts["api"],

        "components":
            mock_artifacts["components"]
    }


    request = TraceabilityRequest(
        **request_data
    )


    artifacts = normalize_artifacts(
        request
    )


    print(
        f"Normalized artifacts: "
        f"{len(artifacts)}"
    )


    similarity_service = (
        TraceabilitySimilarityService(
            similarity_threshold=0.40
        )
    )


    candidates = (
        similarity_service
        .generate_candidate_links(
            request=request,
            artifacts=artifacts
        )
    )

    selected_candidates = (
        rank_candidates(
            candidates
        )
    )

    print(
        f"Selected candidate links: "
        f"{len(selected_candidates)}"
    )

    for candidate in selected_candidates:

        print(
            candidate.requirement_id,
            "->",
            candidate.artifact_id,
            candidate.artifact_type,
            candidate.semantic_similarity
        )

    print(
        f"Candidate links: "
        f"{len(candidates)}"
    )


    for candidate in candidates:

        print(
            candidate.requirement_id,
            "->",
            candidate.artifact_id,
            candidate.artifact_type,
            candidate.semantic_similarity
        )


if __name__ == "__main__":

    main()