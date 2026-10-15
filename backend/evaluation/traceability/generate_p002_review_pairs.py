# Generates all requirement-artifact pairs for P002
# for independent human review.

# Important:
# This script does NOT call SBERT or Gemini.
# It only creates the reviewer file.


import json
from pathlib import Path


REQUIREMENTS = [
    {
        "requirement_id": "REQ-101",
        "statement":
            "Students shall be able to submit assignments online.",
        "requirement_type": "FR",
        "asr": False,
    },
    {
        "requirement_id": "REQ-102",
        "statement":
            "Only authorized users shall access student grades.",
        "requirement_type": "NFR",
        "asr": True,
    },
    {
        "requirement_id": "REQ-103",
        "statement":
            "Students shall receive notifications when grades are published.",
        "requirement_type": "FR",
        "asr": False,
    },
]


def load_artifacts():

    path = Path(
        "datasets/traceability/"
        "mock_design_artifacts_p002.json"
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    artifacts = []

    for artifact in data["architecture"]:
        artifacts.append(
            {
                **artifact,
                "artifact_type":
                    "architecture",
            }
        )

    for artifact in data["database"]:
        artifacts.append(
            {
                **artifact,
                "artifact_type":
                    "database",
            }
        )

    for artifact in data["api"]:
        artifacts.append(
            {
                **artifact,
                "artifact_type":
                    "api",
            }
        )

    for artifact in data["components"]:
        artifacts.append(
            {
                **artifact,
                "artifact_type":
                    "component",
            }
        )

    return (
        data,
        artifacts,
    )


def main():

    project_data, artifacts = (
        load_artifacts()
    )

    review_items = []

    pair_number = 1

    for requirement in REQUIREMENTS:

        for artifact in artifacts:

            review_items.append(
                {
                    "pair_id":
                        f"P002-PAIR-{pair_number:03d}",

                    "requirement_id":
                        requirement["requirement_id"],

                    "requirement_statement":
                        requirement["statement"],

                    "requirement_type":
                        requirement["requirement_type"],

                    "asr":
                        requirement["asr"],

                    "artifact_id":
                        artifact["artifact_id"],

                    "artifact_type":
                        artifact["artifact_type"],

                    "artifact_name":
                        artifact["name"],

                    "artifact_description":
                        artifact["description"],

                    "human_validated":
                        None,

                    "reviewer_comment":
                        "",
                }
            )

            pair_number += 1

    output = {
        "project_id":
            project_data["project_id"],

        "domain":
            project_data["domain"],

        "purpose":
            "Independent human-reviewed gold traceability labels",

        "instructions": (
            "For each requirement-artifact pair, set "
            "human_validated to true only when the artifact "
            "has a concrete and meaningful design role in "
            "implementing, enabling, supporting, protecting, "
            "storing necessary data for, or realizing the "
            "requirement. Do not mark a link true merely "
            "because it belongs to the same general workflow "
            "or contains similar terminology."
        ),

        "total_requirements":
            len(REQUIREMENTS),

        "total_artifacts":
            len(artifacts),

        "total_pairs":
            len(review_items),

        "review_items":
            review_items,
    }

    output_path = Path(
        "datasets/traceability/"
        "reviewer_validation_p002_42_pairs.json"
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        "P002 HUMAN REVIEW FILE CREATED"
    )

    print(
        "Requirements:",
        len(REQUIREMENTS),
    )

    print(
        "Artifacts:",
        len(artifacts),
    )

    print(
        "Pairs:",
        len(review_items),
    )

    print(
        "Output:",
        output_path,
    )


if __name__ == "__main__":
    main()