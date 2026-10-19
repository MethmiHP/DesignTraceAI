# Runs the FINAL held-out Requirement Analysis evaluation.
#
# IMPORTANT:
# - Reads only final_heldout_gold.csv
# - Does not modify the earlier Version 1 evaluation files
# - Processes requirements project by project
# - Saves resumable prediction results
# - Uses the complete Requirement Analysis pipeline

import asyncio
import csv
from pathlib import Path
from collections import defaultdict

from modules.requirement_analysis.schemas import (
    RequirementAnalysisRequest,
    ProjectContext,
)

from modules.requirement_analysis.service import (
    RequirementAnalysisService,
)


# FILE PATHS

GOLD_FILE = Path(
    "evaluation/requirement_analysis/"
    "final_heldout_gold.csv"
)

OUTPUT_FILE = Path(
    "evaluation/requirement_analysis/"
    "final_heldout_predictions.csv"
)


# BOOLEAN HELPER

def to_bool(value):

    if isinstance(value, bool):
        return value

    if value is None:
        return False

    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
    }


# LOAD FINAL HELD-OUT GOLD DATA

def load_gold_records():

    if not GOLD_FILE.exists():

        raise FileNotFoundError(
            f"Gold file not found: {GOLD_FILE}"
        )

    records = []

    with GOLD_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            requirement_id = (
                row.get(
                    "requirement_id",
                    ""
                )
                .strip()
            )

            if not requirement_id:
                continue

            records.append({

                "project_id":
                    row.get(
                        "project_id",
                        ""
                    ).strip(),

                "requirement_id":
                    requirement_id,

                "statement":
                    row.get(
                        "statement",
                        ""
                    ).strip(),

                "gold_requirement_type":
                    row.get(
                        "gold_requirement_type",
                        ""
                    ).strip(),

                "gold_quality_attribute":
                    row.get(
                        "gold_quality_attribute",
                        ""
                    ).strip(),

                "gold_asr":
                    to_bool(
                        row.get(
                            "gold_asr"
                        )
                    ),

                "gold_ambiguous":
                    to_bool(
                        row.get(
                            "gold_ambiguous"
                        )
                    ),

                "gold_incomplete":
                    to_bool(
                        row.get(
                            "gold_incomplete"
                        )
                    ),

                "gold_conflicting":
                    to_bool(
                        row.get(
                            "gold_conflicting"
                        )
                    ),

                "gold_potentially_missing":
                    to_bool(
                        row.get(
                            "gold_potentially_missing"
                        )
                    ),
            })

    return records


# LOAD EXISTING RESULTS

def load_existing_results():

    if not OUTPUT_FILE.exists():
        return {}

    existing = {}

    with OUTPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            key = (
                row.get(
                    "project_id"
                ),
                row.get(
                    "requirement_id"
                ),
            )

            existing[
                key
            ] = row

    return existing


# SAVE RESULTS

def save_results(
    results
):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "project_id",
        "requirement_id",
        "statement",

        "gold_requirement_type",
        "gold_quality_attribute",
        "gold_asr",
        "gold_ambiguous",
        "gold_incomplete",
        "gold_conflicting",
        "gold_potentially_missing",

        "pred_requirement_type",
        "pred_quality_attribute",
        "pred_asr",
        "pred_ambiguous",
        "pred_incomplete",
        "pred_conflicting",
        "pred_potentially_missing",
        "pred_confidence",

        "status",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            results
        )


# GROUP BY PROJECT

def group_by_project(
    records
):

    grouped = defaultdict(
        list
    )

    for record in records:

        grouped[
            record[
                "project_id"
            ]
        ].append(
            record
        )

    return grouped


# BUILD PROJECT DESCRIPTION

def build_project_description(
    records
):

    lines = []

    for record in records:

        lines.append(
            f"{record['requirement_id']}: "
            f"{record['statement']}"
        )

    return "\n".join(
        lines
    )


# TEXT NORMALIZATION
def normalize_text(
    text
):

    if text is None:
        return ""

    return (
        str(text)
        .strip()
        .lower()
        .replace(".", "")
    )


# FIND MATCHING PREDICTION
def find_matching_prediction(
    gold_record,
    predictions,
):

    gold_text = normalize_text(
        gold_record[
            "statement"
        ]
    )

    for prediction in predictions:

        original_text = normalize_text(
            prediction.original_text
        )

        normalized_statement = normalize_text(
            prediction.normalized_statement
        )

        if (
            gold_text
            == original_text

            or gold_text
            == normalized_statement

            or gold_text
            in original_text

            or original_text
            in gold_text
        ):

            return prediction

    return None


# ORDER RESULTS

def build_ordered_results(
    records,
    results_by_key,
):

    ordered_results = []

    for gold_record in records:

        key = (
            gold_record[
                "project_id"
            ],
            gold_record[
                "requirement_id"
            ],
        )

        if key in results_by_key:

            ordered_results.append(
                results_by_key[
                    key
                ]
            )

    return ordered_results


# MAIN

async def main():

    print(
        "\n======================================="
    )

    print(
        "FINAL HELD-OUT REQUIREMENT EVALUATION"
    )

    print(
        "======================================="
    )


    # LOAD GOLD DATA

    records = (
        load_gold_records()
    )

    print(
        f"Total held-out requirements: "
        f"{len(records)}"
    )


    # GROUP BY PROJECT

    grouped = (
        group_by_project(
            records
        )
    )

    print(
        f"Projects: "
        f"{len(grouped)}"
    )

    print(
        f"Project IDs: "
        f"{list(grouped.keys())}"
    )


    # LOAD PREVIOUS PROGRESS

    existing_results = (
        load_existing_results()
    )

    results_by_key = dict(
        existing_results
    )

    print(
        f"Previously saved rows: "
        f"{len(existing_results)}"
    )


    # LOAD REQUIREMENT ANALYSIS SERVICE

    print(
        "\nLoading Requirement Analysis service..."
    )

    service = (
        RequirementAnalysisService()
    )

    print(
        "Requirement Analysis service loaded."
    )


    # PROCESS PROJECTS

    quota_exhausted = False

    for project_index, (
        project_id,
        project_records,
    ) in enumerate(
        grouped.items(),
        start=1,
    ):

        print(
            "\n======================================="
        )

        print(
            f"PROJECT "
            f"[{project_index}/{len(grouped)}] "
            f"{project_id}"
        )

        print(
            "======================================="
        )


        # CHECK WHETHER PROJECT ALREADY COMPLETED

        project_complete = True

        for record in project_records:

            key = (
                record[
                    "project_id"
                ],
                record[
                    "requirement_id"
                ],
            )

            existing = (
                existing_results.get(
                    key
                )
            )

            if (
                existing is None

                or existing.get(
                    "status"
                )
                not in {
                    "OK",
                    "NO_MATCH",
                }
            ):

                project_complete = False

                break


        if project_complete:

            print(
                "Already completed. "
                "Skipping project."
            )

            continue


        # BUILD PROJECT INPUT

        project_description = (
            build_project_description(
                project_records
            )
        )

        print(
            "\nInput requirements:"
        )

        print(
            project_description
        )


        # CREATE REQUEST

        request = (
            RequirementAnalysisRequest(

                project_id=
                    project_id,

                raw_description=
                    project_description,

                project_context=
                    ProjectContext(),
            )
        )


        # RUN COMPLETE PIPELINE

        try:

            response = await service.analyze(
                request
            )

            predictions = (
                response.requirements
            )

            print(
                f"\nExtracted requirements: "
                f"{len(predictions)}"
            )


            # MATCH GOLD ROWS

            for gold_record in (
                project_records
            ):

                key = (
                    gold_record[
                        "project_id"
                    ],
                    gold_record[
                        "requirement_id"
                    ],
                )


                matched = (
                    find_matching_prediction(
                        gold_record,
                        predictions,
                    )
                )


                # NO MATCH

                if matched is None:

                    print(
                        f"NO MATCH: "
                        f"{gold_record['requirement_id']}"
                    )

                    prediction_row = {

                        "pred_requirement_type":
                            "",

                        "pred_quality_attribute":
                            "",

                        "pred_asr":
                            "",

                        "pred_ambiguous":
                            "",

                        "pred_incomplete":
                            "",

                        "pred_conflicting":
                            "",

                        "pred_potentially_missing":
                            "",

                        "pred_confidence":
                            "",

                        "status":
                            "NO_MATCH",
                    }


                # MATCH FOUND

                else:

                    print(
                        f"MATCHED: "
                        f"{gold_record['requirement_id']} "
                        f"-> "
                        f"{matched.requirement_id}"
                    )

                    prediction_row = {

                        "pred_requirement_type":
                            matched.requirement_type,

                        "pred_quality_attribute":
                            (
                                matched
                                .quality_attribute
                                or ""
                            ),

                        "pred_asr":
                            matched.asr,

                        "pred_ambiguous":
                            (
                                matched
                                .quality_issues
                                .ambiguous
                            ),

                        "pred_incomplete":
                            (
                                matched
                                .quality_issues
                                .incomplete
                            ),

                        "pred_conflicting":
                            (
                                matched
                                .quality_issues
                                .conflicting
                            ),

                        "pred_potentially_missing":
                            (
                                matched
                                .quality_issues
                                .potentially_missing
                            ),

                        "pred_confidence":
                            matched.confidence,

                        "status":
                            "OK",
                    }


                results_by_key[
                    key
                ] = {

                    **gold_record,
                    **prediction_row,
                }


        # ERROR HANDLING

        except Exception as exc:

            error_text = str(
                exc
            )

            print(
                "\nPROJECT ERROR:"
            )

            print(
                error_text
            )


            if (
                "429"
                in error_text

                or "RESOURCE_EXHAUSTED"
                in error_text
            ):

                print(
                    "\nGemini quota exhausted."
                )

                print(
                    "Stopping safely. "
                    "Run the same command later "
                    "to continue."
                )

                quota_exhausted = True


            for gold_record in (
                project_records
            ):

                key = (
                    gold_record[
                        "project_id"
                    ],
                    gold_record[
                        "requirement_id"
                    ],
                )

                results_by_key[
                    key
                ] = {

                    **gold_record,

                    "pred_requirement_type":
                        "",

                    "pred_quality_attribute":
                        "",

                    "pred_asr":
                        "",

                    "pred_ambiguous":
                        "",

                    "pred_incomplete":
                        "",

                    "pred_conflicting":
                        "",

                    "pred_potentially_missing":
                        "",

                    "pred_confidence":
                        "",

                    "status":
                        f"ERROR: {error_text}",
                }


        # SAVE AFTER EACH PROJECT

        ordered_results = (
            build_ordered_results(
                records,
                results_by_key,
            )
        )

        save_results(
            ordered_results
        )

        print(
            "\nProject progress saved."
        )


        if quota_exhausted:

            break


    # FINAL SAVE
    final_results = (
        build_ordered_results(
            records,
            results_by_key,
        )
    )

    save_results(
        final_results
    )


    # SUMMARY

    successful = sum(
        1
        for row in final_results
        if row.get(
            "status"
        ) == "OK"
    )

    no_match = sum(
        1
        for row in final_results
        if row.get(
            "status"
        ) == "NO_MATCH"
    )

    errors = sum(
        1
        for row in final_results
        if str(
            row.get(
                "status",
                ""
            )
        ).startswith(
            "ERROR:"
        )
    )


    print(
        "\n======================================="
    )

    print(
        "FINAL HELD-OUT EVALUATION STATUS"
    )

    print(
        "======================================="
    )

    print(
        f"Successful matches: "
        f"{successful}"
    )

    print(
        f"No matches: "
        f"{no_match}"
    )

    print(
        f"Errors: "
        f"{errors}"
    )

    print(
        f"Total gold requirements: "
        f"{len(records)}"
    )


    if records:

        print(
            f"Match coverage: "
            f"{(successful / len(records)) * 100:.1f}%"
        )


    if quota_exhausted:

        print(
            "\nStatus: PAUSED - "
            "GEMINI QUOTA EXHAUSTED"
        )

    else:

        print(
            "\nStatus: FINISHED"
        )


    print(
        "\nSaved to:"
    )

    print(
        OUTPUT_FILE
    )


# ENTRY POINT
if __name__ == "__main__":

    asyncio.run(
        main()
    )