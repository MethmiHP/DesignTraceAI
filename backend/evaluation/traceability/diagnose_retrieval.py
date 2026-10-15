# Diagnoses SBERT requirement-to-artifact retrieval.
# This script compares every requirement with every design artifact
# and prints all cosine similarity scores.

# Gemini is NOT called.


import json

from modules.traceability.schemas import (
    TraceabilityRequest,
)

from modules.traceability.normalizer import (
    normalize_artifacts,
    normalize_requirement_text,
)

from modules.traceability.embedding_service import (
    get_traceability_embedding_service,
)


def load_mock_project():

    with open(
        "datasets/traceability/mock_design_artifacts.json",
        "r",
        encoding="utf-8",
    ) as file:

        artifact_data = json.load(file)

    request_data = {

        "project_id": "P001",

        "requirements": [

            {
                "requirement_id": "REQ-001",
                "statement":
                    "Patients shall be able to book appointments.",
                "requirement_type": "FR",
                "asr": False,
            },

            {
                "requirement_id": "REQ-002",
                "statement":
                    "Patient information shall be secure.",
                "requirement_type": "NFR",
                "asr": True,
            },

            {
                "requirement_id": "REQ-003",
                "statement":
                    "Patients shall receive appointment reminders.",
                "requirement_type": "FR",
                "asr": False,
            },
        ],

        "architecture":
            artifact_data["architecture"],

        "database":
            artifact_data["database"],

        "api":
            artifact_data["api"],

        "components":
            artifact_data["components"],
    }

    return TraceabilityRequest(
        **request_data
    )


def load_gold_labels():

    with open(
        "datasets/traceability/"
        "reviewer_validation_all_39_pairs.json",
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    gold = {}

    for item in data["review_items"]:

        key = (
            item["requirement_id"],
            item["artifact_id"],
        )

        gold[key] = bool(
            item["human_validated"]
        )

    return gold


def main():

    print(
        "SBERT RETRIEVAL DIAGNOSTIC"
    )

    request = load_mock_project()

    gold_labels = load_gold_labels()

    artifacts = normalize_artifacts(
        request
    )

    embedding_service = (
        get_traceability_embedding_service()
    )

    artifact_texts = [
        artifact.normalized_text
        for artifact in artifacts
    ]

    artifact_embeddings = (
        embedding_service.encode_texts(
            artifact_texts
        )
    )

    for requirement in request.requirements:

        print(
            "\n"
            "=================================================="
        )

        print(
            requirement.requirement_id,
            "-",
            requirement.statement,
        )

        print(
            "=================================================="
        )

        requirement_text = (
            normalize_requirement_text(
                requirement_id=
                    requirement.requirement_id,

                statement=
                    requirement.statement,

                requirement_type=
                    requirement.requirement_type,

                asr=
                    requirement.asr,
            )
        )

        requirement_embedding = (
            embedding_service.encode_text(
                requirement_text
            )
        )

        results = []

        for artifact, artifact_embedding in zip(
            artifacts,
            artifact_embeddings,
        ):

            similarity = float(
                requirement_embedding
                @ artifact_embedding
            )

            gold_value = gold_labels.get(
                (
                    requirement.requirement_id,
                    artifact.artifact_id,
                ),
                False,
            )

            results.append(
                (
                    similarity,
                    artifact,
                    gold_value,
                )
            )

        results.sort(
            key=lambda item:
                item[0],
            reverse=True,
        )

        for (
            similarity,
            artifact,
            gold_value,
        ) in results:

            marker = (
                "GOLD=TRUE"
                if gold_value
                else "GOLD=FALSE"
            )

            threshold_marker = (
                "PASS"
                if similarity >= 0.40
                else "FAIL"
            )

            print(
                requirement.requirement_id,
                "->",
                artifact.artifact_id,
                artifact.artifact_type,
                "similarity=",
                round(
                    similarity,
                    4,
                ),
                marker,
                "threshold_0.40=",
                threshold_marker,
            )


if __name__ == "__main__":
    main()