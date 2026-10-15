# Evaluates the frozen Traceability Module on unseen P002.

# P002 domain:
# E-Learning / Course Management System

# Important:
# Do not tune thresholds, candidate rules, or Gemini prompts
# using this project before recording the evaluation result.

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

from modules.traceability.candidate_expander import (
    CandidateExpander,
)

from modules.traceability.traceability_validator import (
    TraceabilityValidator,
)

from modules.traceability.link_filter import (
    TraceLinkFilter,
)


# LOAD P002 PROJECT
def load_p002_project():
    """
    Loads the unseen P002 E-Learning project
    and converts the JSON structure into the
    TraceabilityRequest schema format.
    """

    with open(
        "datasets/traceability/"
        "mock_design_artifacts_p002.json",
        "r",
        encoding="utf-8",
    ) as file:
        artifacts = json.load(file)



    # PREPARE ARCHITECTURE ARTIFACTS

    architecture_elements = []

    for item in artifacts["architecture"]:

        architecture_elements.append(
            {
                "artifact_id":
                    item["artifact_id"],

                "type":
                    "service",

                "name":
                    item["name"],

                "description":
                    item["description"],
            }
        )



    # PREPARE DATABASE ARTIFACTS

    database_entities = []

    for item in artifacts["database"]:

        database_entities.append(
            {
                "artifact_id":
                    item["artifact_id"],

                "name":
                    item["name"],

                "description":
                    item["description"],
            }
        )


    # PREPARE API ARTIFACTS

    api_operations = []

    for item in artifacts["api"]:

        api_name = item["name"].strip()

        # Example:
        # "POST /assignments/{id}/submit"
        # becomes:
        # method = "POST"
        # path = "/assignments/{id}/submit"

        parts = api_name.split(
            " ",
            1,
        )

        method = parts[0]

        path = (
            parts[1]
            if len(parts) > 1
            else "/"
        )

        api_operations.append(
            {
                "artifact_id":
                    item["artifact_id"],

                "method":
                    method,

                "path":
                    path,

                "description":
                    item["description"],
            }
        )


    # PREPARE COMPONENT ARTIFACTS

    components = []

    for item in artifacts["components"]:

        components.append(
            {
                "artifact_id":
                    item["artifact_id"],

                "name":
                    item["name"],

                "description":
                    item["description"],
            }
        )


    # BUILD REQUEST

    request_data = {
        "project_id":
            "P002",

        "requirements": [
            {
                "requirement_id":
                    "REQ-101",

                "statement":
                    "Students shall be able to submit assignments online.",

                "requirement_type":
                    "FR",

                "asr":
                    False,
            },

            {
                "requirement_id":
                    "REQ-102",

                "statement":
                    "Only authorized users shall access student grades.",

                "requirement_type":
                    "NFR",

                "asr":
                    True,
            },

            {
                "requirement_id":
                    "REQ-103",

                "statement":
                    "Students shall receive notifications when grades are published.",

                "requirement_type":
                    "FR",

                "asr":
                    False,
            },
        ],

        "architecture": {
            "elements":
                architecture_elements,
        },

        "database": {
            "entities":
                database_entities,
        },

        "api": {
            "operations":
                api_operations,
        },

        "components":
            components,
    }

    return TraceabilityRequest(
        **request_data
    )


# LOAD P002 HUMAN GOLD LABELS

def load_gold_labels():
    """
    Loads the 42 human-reviewed P002 pairs.
    """

    with open(
        "datasets/traceability/"
        "reviewer_validation_p002_42_pairs.json",
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    gold_labels = {}

    for item in data["review_items"]:

        if item["human_validated"] is None:
            raise ValueError(
                f"Unreviewed pair found: "
                f"{item['pair_id']}"
            )

        key = (
            item["requirement_id"],
            item["artifact_id"],
        )

        gold_labels[key] = bool(
            item["human_validated"]
        )

    return gold_labels



# RUN FROZEN TRACEABILITY PIPELINE

def run_traceability_pipeline(
    request: TraceabilityRequest,
):
    """
    Frozen pipeline:

    Requirement
    -> SBERT retrieval
    -> Candidate ranking
    -> Deterministic candidate expansion
    -> Gemini validation
    -> Deterministic filtering

    Frozen values:
    similarity threshold = 0.40
    minimum confidence = 0.70
    """


    # NORMALIZE ARTIFACTS

    artifacts = normalize_artifacts(
        request
    )



    # FROZEN SBERT RETRIEVAL
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

    candidates = rank_candidates(
        candidates
    )


    # FROZEN CANDIDATE EXPANSION

    candidate_expander = (
        CandidateExpander()
    )


    # FROZEN GEMINI VALIDATOR
    validator = (
        TraceabilityValidator()
    )

    validated_links = []


    # PROCESS EACH REQUIREMENT

    for requirement in request.requirements:

        print(
            "\n"
            "=================================================="
        )

        print(
            "PROCESSING:",
            requirement.requirement_id
        )

        print(
            "Requirement:",
            requirement.statement
        )

        print(
            "=================================================="
        )

        # ORIGINAL SBERT CANDIDATES
        requirement_candidates = [
            candidate
            for candidate in candidates
            if (
                candidate.requirement_id
                == requirement.requirement_id
            )
        ]

        print(
            f"\nOriginal SBERT candidates "
            f"({len(requirement_candidates)}):"
        )

        if not requirement_candidates:

            print(
                "No SBERT candidates found."
            )

        else:

            for candidate in requirement_candidates:

                print(
                    candidate.requirement_id,
                    "->",
                    candidate.artifact_id,
                    candidate.artifact_type,
                    "similarity=",
                    candidate.semantic_similarity,
                )


        # CANDIDATE EXPANSION
        expanded_candidates = (
            candidate_expander.expand_candidates(
                requirement=requirement,
                current_candidates=
                    requirement_candidates,
                artifacts=artifacts,
            )
        )

        print(
            f"\nCandidates after expansion "
            f"({len(expanded_candidates)}):"
        )

        for candidate in expanded_candidates:

            source = (
                "SBERT"
                if candidate.semantic_similarity > 0.0
                else "RULE"
            )

            print(
                candidate.requirement_id,
                "->",
                candidate.artifact_id,
                candidate.artifact_type,
                "similarity=",
                candidate.semantic_similarity,
                "source=",
                source,
            )


        # GEMINI VALIDATION
        print(
            f"\nValidating "
            f"{requirement.requirement_id}"
            f" with "
            f"{len(expanded_candidates)} "
            f"candidate(s)..."
        )

        requirement_links = (
            validator.validate_requirement_candidates(
                requirement=requirement,
                candidates=expanded_candidates,
                artifacts=artifacts,
            )
        )


        # PRINT GEMINI DECISIONS
        print(
            f"\nGemini decisions for "
            f"{requirement.requirement_id}:"
        )

        if not requirement_links:

            print(
                "No Gemini validation results."
            )

        else:

            for link in requirement_links:

                print(
                    link.requirement_id,
                    "->",
                    link.artifact_id,
                    link.artifact_type,
                    "similarity=",
                    link.semantic_similarity,
                    "valid=",
                    link.link_valid,
                    "confidence=",
                    link.confidence,
                )

                print(
                    "Rationale:",
                    link.rationale,
                )

                print()

        validated_links.extend(
            requirement_links
        )


    # FROZEN DETERMINISTIC FILTERING
    link_filter = (
        TraceLinkFilter(
            minimum_confidence=0.70
        )
    )

    filtered_links = (
        link_filter.filter_links(
            links=validated_links,
            artifacts=artifacts,
        )
    )

    return filtered_links


# CALCULATE METRICS
def calculate_metrics(
    gold_labels: dict,
    predicted_links,
):
    """
    Calculates TP, FP, FN, TN,
    Precision, Recall and F1-score.
    """

    predicted_positive = {
        (
            link.requirement_id,
            link.artifact_id,
        )
        for link in predicted_links
    }

    tp = 0
    fp = 0
    fn = 0
    tn = 0

    false_negative_pairs = []
    false_positive_pairs = []

    for pair, gold_value in gold_labels.items():

        predicted_value = (
            pair in predicted_positive
        )

        if (
            gold_value
            and predicted_value
        ):
            tp += 1

        elif (
            not gold_value
            and predicted_value
        ):
            fp += 1

            false_positive_pairs.append(
                pair
            )

        elif (
            gold_value
            and not predicted_value
        ):
            fn += 1

            false_negative_pairs.append(
                pair
            )

        else:
            tn += 1

    precision = (
        tp / (tp + fp)
        if (
            tp + fp
        ) > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (
            tp + fn
        ) > 0
        else 0.0
    )

    f1 = (
        2
        * precision
        * recall
        / (
            precision
            + recall
        )
        if (
            precision
            + recall
        ) > 0
        else 0.0
    )

    return {
        "true_positives":
            tp,

        "false_positives":
            fp,

        "false_negatives":
            fn,

        "true_negatives":
            tn,

        "precision":
            round(
                precision,
                4,
            ),

        "recall":
            round(
                recall,
                4,
            ),

        "f1_score":
            round(
                f1,
                4,
            ),

        "false_negative_pairs":
            false_negative_pairs,

        "false_positive_pairs":
            false_positive_pairs,
    }

# Main function to run the evaluation

def main():

    print(
        "TRACEABILITY UNSEEN EVALUATION - P002"
    )

    print(
        "Domain: E-Learning / Course Management System"
    )

    print(
        "Pipeline configuration: FROZEN"
    )


    # LOAD DATA

    request = (
        load_p002_project()
    )

    gold_labels = (
        load_gold_labels()
    )

    print(
        "Gold reviewed pairs:",
        len(gold_labels),
    )

    gold_positive_count = sum(
        1
        for value in gold_labels.values()
        if value
    )

    gold_negative_count = sum(
        1
        for value in gold_labels.values()
        if not value
    )

    print(
        "Gold valid links:",
        gold_positive_count,
    )

    print(
        "Gold invalid links:",
        gold_negative_count,
    )


    # RUN FROZEN PIPELINE

    predicted_links = (
        run_traceability_pipeline(
            request
        )
    )


    # FINAL PREDICTED LINKS

    print(
        "\n"
        "=================================================="
    )

    print(
        "FINAL PREDICTED VALID LINKS"
    )

    print(
        "=================================================="
    )

    if not predicted_links:

        print(
            "No final valid links."
        )

    else:

        for link in predicted_links:

            print(
                link.requirement_id,
                "->",
                link.artifact_id,
                link.artifact_type,
                "confidence=",
                link.confidence,
            )


    # METRICS

    metrics = (
        calculate_metrics(
            gold_labels,
            predicted_links,
        )
    )


    # FALSE NEGATIVES

    print(
        "\n"
        "=================================================="
    )

    print(
        "FALSE NEGATIVES"
    )

    print(
        "=================================================="
    )

    if (
        metrics[
            "false_negative_pairs"
        ]
    ):

        for (
            requirement_id,
            artifact_id,
        ) in metrics[
            "false_negative_pairs"
        ]:

            print(
                requirement_id,
                "->",
                artifact_id,
            )

    else:

        print(
            "No false negatives."
        )


    # FALSE POSITIVES
    print(
        "\n"
        "=================================================="
    )

    print(
        "FALSE POSITIVES"
    )

    print(
        "=================================================="
    )

    if (
        metrics[
            "false_positive_pairs"
        ]
    ):

        for (
            requirement_id,
            artifact_id,
        ) in metrics[
            "false_positive_pairs"
        ]:

            print(
                requirement_id,
                "->",
                artifact_id,
            )

    else:

        print(
            "No false positives."
        )


    # FINAL RESULTS

    print(
        "\n"
        "=================================================="
    )

    print(
        "P002 UNSEEN EVALUATION RESULTS"
    )

    print(
        "=================================================="
    )

    print(
        "True Positives:",
        metrics["true_positives"],
    )

    print(
        "False Positives:",
        metrics["false_positives"],
    )

    print(
        "False Negatives:",
        metrics["false_negatives"],
    )

    print(
        "True Negatives:",
        metrics["true_negatives"],
    )

    print(
        "Precision:",
        metrics["precision"],
    )

    print(
        "Recall:",
        metrics["recall"],
    )

    print(
        "F1-score:",
        metrics["f1_score"],
    )


if __name__ == "__main__":
    main()