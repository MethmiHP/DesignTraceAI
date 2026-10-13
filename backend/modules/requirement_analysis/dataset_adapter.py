# Converts Requirement Analysis datasets from their original source formats
# into a common DesignTraceAI representation. It maps PROMISE_exp labels,
# standardizes human-gold annotations, prepares PURE project documents,
# and provides consistent records for training and evaluation.

from collections import Counter
from typing import Any

from .dataset_loader import (
    load_promise_dataset,
    load_promise_exp_dataset,
    load_human_gold_dataset,
    load_pure_documents,
    normalize_boolean,
    normalize_requirement_type,
)

PROMISE_EXP_LABEL_MAP = {
    "F": {
        "requirement_type": "FR",
        "quality_attribute": None
    },

    "A": {
        "requirement_type": "NFR",
        "quality_attribute": "Availability"
    },

    "L": {
        "requirement_type": "NFR",
        "quality_attribute": "Legal"
    },

    "LF": {
        "requirement_type": "NFR",
        "quality_attribute": "Look and Feel"
    },

    "MN": {
        "requirement_type": "NFR",
        "quality_attribute": "Maintainability"
    },

    "O": {
        "requirement_type": "NFR",
        "quality_attribute": "Operational"
    },

    "PE": {
        "requirement_type": "NFR",
        "quality_attribute": "Performance"
    },

    "SC": {
        "requirement_type": "NFR",
        "quality_attribute": "Scalability"
    },

    "SE": {
        "requirement_type": "NFR",
        "quality_attribute": "Security"
    },

    "US": {
        "requirement_type": "NFR",
        "quality_attribute": "Usability"
    },

    "FT": {
        "requirement_type": "NFR",
        "quality_attribute": "Fault Tolerance"
    },

    "PO": {
        "requirement_type": "NFR",
        "quality_attribute": "Portability"
    }
}


# COMMON EVALUATION FORMAT

def create_common_record(
    *,
    source: str,
    project_id: str | None,
    statement: str,
    gold_requirement_type: str | None = None,
    gold_quality_attribute: str | None = None,
    gold_asr: bool | None = None,
    gold_ambiguous: bool | None = None,
    gold_incomplete: bool | None = None,
    gold_conflicting: bool | None = None,
    gold_potentially_missing: bool | None = None,
    original_label: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:

    return {
        "source": source,

        "project_id": project_id,

        "statement": statement,

        "gold_requirement_type":
            gold_requirement_type,

        "gold_quality_attribute":
            gold_quality_attribute,

        "gold_asr":
            gold_asr,

        "gold_ambiguous":
            gold_ambiguous,

        "gold_incomplete":
            gold_incomplete,

        "gold_conflicting":
            gold_conflicting,

        "gold_potentially_missing":
            gold_potentially_missing,

        "original_label":
            original_label,

        "metadata":
            metadata or {}
    }



# PROMISE_EXP

def inspect_promise_exp_labels() -> dict[str, int]:
    """
    Inspect all PROMISE_exp labels.

    IMPORTANT:
    We do this BEFORE creating a mapping because labels such as
    PE, LF, SE, US, etc. must not be guessed.
    """

    records = load_promise_exp_dataset()

    labels = [
        record.get("_class_")
        for record in records
        if record.get("_class_")
    ]

    return dict(
        Counter(labels)
    )


def adapt_promise_exp() -> list[dict[str, Any]]:
    """
    Convert PROMISE_exp records into the common evaluation format.

    PROMISE_exp fields:
        ProjectID
        RequirementText
        _class_

    Label mapping:
        F  -> Functional
        A  -> Availability
        L  -> Legal
        LF -> Look and Feel
        MN -> Maintainability
        O  -> Operational
        PE -> Performance
        SC -> Scalability
        SE -> Security
        US -> Usability
        FT -> Fault Tolerance
        PO -> Portability
    """

    source_records = load_promise_exp_dataset()

    adapted = []

    for record in source_records:

        statement = (
            record.get("RequirementText")
            or ""
        ).strip()

        if not statement:
            continue

        original_label = (
            record.get("_class_")
            or ""
        ).strip().upper()

        mapping = PROMISE_EXP_LABEL_MAP.get(
            original_label
        )

        if mapping is None:
            continue

        adapted.append(
            create_common_record(

                source="PROMISE_EXP",

                project_id=str(
                    record.get(
                        "ProjectID",
                        ""
                    )
                ),

                statement=statement,

                gold_requirement_type=mapping[
                    "requirement_type"
                ],

                gold_quality_attribute=mapping[
                    "quality_attribute"
                ],

                gold_asr=None,
                gold_ambiguous=None,
                gold_incomplete=None,
                gold_conflicting=None,
                gold_potentially_missing=None,

                original_label=original_label,

                metadata={
                    "source_file":
                        record.get(
                            "_source_file"
                        )
                }
            )
        )

    return adapted


# HUMAN GOLD / CANDIDATE DATASET

def adapt_human_gold(
    reviewed_only: bool = True
) -> list[dict[str, Any]]:
    """
    Convert your human annotation CSV into the
    common evaluation format.

    reviewed_only=True means rows marked as unreviewed
    will NOT be treated as final evaluation gold.
    """

    source_records = (
        load_human_gold_dataset()
    )

    adapted = []

    for record in source_records:

        final_status = str(
            record.get(
                "final_gold",
                ""
            )
        ).strip().lower()

        if reviewed_only:

            if final_status in {
                "",
                "unreviewed",
                "pending"
            }:
                continue

        statement = (
            record.get("statement")
            or ""
        ).strip()

        if not statement:
            continue

        requirement_type = (
            normalize_requirement_type(
                record.get(
                    "requirement_type"
                )
            )
        )

        quality_attribute = (
            record.get(
                "quality_attribute"
            )
            or None
        )

        if quality_attribute:

            quality_attribute = (
                quality_attribute.strip()
            )

            if not quality_attribute:
                quality_attribute = None

        adapted.append(
            create_common_record(

                source="HUMAN_GOLD",

                project_id=record.get(
                    "project_id"
                ),

                statement=statement,

                gold_requirement_type=
                    requirement_type,

                gold_quality_attribute=
                    quality_attribute,

                gold_asr=
                    normalize_boolean(
                        record.get("asr")
                    ),

                gold_ambiguous=
                    normalize_boolean(
                        record.get(
                            "ambiguous"
                        )
                    ),

                gold_incomplete=
                    normalize_boolean(
                        record.get(
                            "incomplete"
                        )
                    ),

                gold_conflicting=
                    normalize_boolean(
                        record.get(
                            "conflicting"
                        )
                    ),

                gold_potentially_missing=
                    normalize_boolean(
                        record.get(
                            "potentially_missing"
                        )
                    ),

                metadata={
                    "requirement_id":
                        record.get(
                            "requirement_id"
                        ),

                    "reviewer_1":
                        record.get(
                            "reviewer_1"
                        ),

                    "reviewer_2":
                        record.get(
                            "reviewer_2"
                        ),

                    "final_gold":
                        record.get(
                            "final_gold"
                        ),

                    "source_file":
                        record.get(
                            "_source_file"
                        )
                }
            )
        )

    return adapted



# PURE

def adapt_pure_documents() -> list[dict[str, Any]]:
    """
    PURE documents are mainly realistic project-level
    requirement sources.

    They do not automatically become gold-labelled
    evaluation examples.
    """

    documents = (
        load_pure_documents()
    )

    adapted = []

    for index, document in enumerate(
        documents,
        start=1
    ):

        content = document.get(
            "content"
        )

        if not isinstance(
            content,
            str
        ):
            continue

        if not content.strip():
            continue

        adapted.append(
            {
                "source": "PURE",

                "project_id":
                    f"PURE-{index:03d}",

                "document_id":
                    document.get(
                        "document_id"
                    ),

                "content":
                    content,

                "metadata": {
                    "source_archive":
                        document.get(
                            "source_archive"
                        ),

                    "file_type":
                        document.get(
                            "file_type"
                        )
                }
            }
        )

    return adapted



# SUMMARY

def get_adapter_summary() -> dict[str, Any]:

    promise_exp = adapt_promise_exp()

    human_all = adapt_human_gold(
        reviewed_only=False
    )

    human_reviewed = adapt_human_gold(
        reviewed_only=True
    )

    pure = adapt_pure_documents()

    return {

        "promise_exp_records":
            len(promise_exp),

        "human_candidate_records":
            len(human_all),

        "human_final_gold_records":
            len(human_reviewed),

        "pure_documents":
            len(pure),

        "promise_exp_label_distribution":
            inspect_promise_exp_labels()
    }



# MANUAL TEST

if __name__ == "__main__":

    print(
        "\n================================"
    )

    print(
        "DATASET ADAPTER SUMMARY"
    )

    print(
        "================================"
    )

    summary = (
        get_adapter_summary()
    )

    for key, value in summary.items():

        print(
            f"{key}: {value}"
        )

    print(
        "\nPROMISE EXP SAMPLE"
    )

    promise_exp = (
        adapt_promise_exp()
    )

    for record in promise_exp[:3]:

        print(
            record
        )

    print(
        "\nHUMAN GOLD SAMPLE"
    )

    human = adapt_human_gold(
        reviewed_only=False
    )

    for record in human[:3]:

        print(
            record
        )