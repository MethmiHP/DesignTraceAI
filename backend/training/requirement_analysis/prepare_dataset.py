# Prepares the PROMISE_exp dataset for:
# 1. FR/NFR classification
# 2. NFR quality-attribute classification
#
# It adapts the raw records, filters valid labels,
# creates train/validation/test splits,
# and saves the prepared datasets as JSON files.

from pathlib import Path
import json
from collections import Counter

from sklearn.model_selection import train_test_split

from modules.requirement_analysis.dataset_adapter import (
    adapt_promise_exp
)

from training.requirement_analysis.model_config import (
    TRAINING_CONFIG
)



# OUTPUT PATH

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    BASE_DIR
    / "training"
    / "requirement_analysis"
    / "prepared_data"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)



# PREPARE FR / NFR DATASET

def prepare_fr_nfr_dataset():
    """
    Create train, validation and test splits
    for FR / NFR classification.
    """

    records = adapt_promise_exp()

    dataset = []

    for record in records:

        statement = record.get(
            "statement"
        )

        label = record.get(
            "gold_requirement_type"
        )

        if not statement:
            continue

        if label not in {
            "FR",
            "NFR"
        }:
            continue

        dataset.append({
            "text": statement,
            "label": label
        })

    print(
        f"Total FR/NFR records: {len(dataset)}"
    )

    labels = [
        item["label"]
        for item in dataset
    ]


    # FIRST SPLIT
    # 70% train
    # 30% temporary

    train_data, temp_data = train_test_split(

        dataset,

        test_size=(
            TRAINING_CONFIG["test_size"]
            +
            TRAINING_CONFIG["validation_size"]
        ),

        random_state=
            TRAINING_CONFIG[
                "random_state"
            ],

        stratify=labels
    )


    # SECOND SPLIT
    # 15% validation
    # 15% test

    temp_labels = [
        item["label"]
        for item in temp_data
    ]

    validation_ratio = (
        TRAINING_CONFIG[
            "validation_size"
        ]
        /
        (
            TRAINING_CONFIG[
                "validation_size"
            ]
            +
            TRAINING_CONFIG[
                "test_size"
            ]
        )
    )

    validation_data, test_data = (
        train_test_split(

            temp_data,

            test_size=(
                1 - validation_ratio
            ),

            random_state=
                TRAINING_CONFIG[
                    "random_state"
                ],

            stratify=temp_labels
        )
    )

    return (
        train_data,
        validation_data,
        test_data
    )


# PREPARE NFR QUALITY ATTRIBUTE DATASET

def prepare_nfr_category_dataset():
    """
    Create train, validation and test splits
    for NFR quality-attribute classification.
    """

    records = adapt_promise_exp()

    dataset = []

    for record in records:

        requirement_type = record.get(
            "gold_requirement_type"
        )

        quality_attribute = record.get(
            "gold_quality_attribute"
        )

        statement = record.get(
            "statement"
        )

        # Only NFR requirements are needed
        if requirement_type != "NFR":
            continue

        if not statement:
            continue

        if not quality_attribute:
            continue

        dataset.append({
            "text": statement,
            "label": quality_attribute
        })

    print(
        f"\nTotal NFR category records: "
        f"{len(dataset)}"
    )

    labels = [
        item["label"]
        for item in dataset
    ]


    # FIRST SPLIT
    # 70% train
    # 30% temporary


    train_data, temp_data = train_test_split(

        dataset,

        test_size=(
            TRAINING_CONFIG["test_size"]
            +
            TRAINING_CONFIG["validation_size"]
        ),

        random_state=
            TRAINING_CONFIG[
                "random_state"
            ],

        stratify=labels
    )


    # SECOND SPLIT
    # 15% validation
    # 15% test

    temp_labels = [
        item["label"]
        for item in temp_data
    ]

    validation_ratio = (
        TRAINING_CONFIG[
            "validation_size"
        ]
        /
        (
            TRAINING_CONFIG[
                "validation_size"
            ]
            +
            TRAINING_CONFIG[
                "test_size"
            ]
        )
    )

    validation_data, test_data = (
        train_test_split(

            temp_data,

            test_size=(
                1 - validation_ratio
            ),

            random_state=
                TRAINING_CONFIG[
                    "random_state"
                ],

            stratify=temp_labels
        )
    )

    return (
        train_data,
        validation_data,
        test_data
    )



# SAVE JSON

def save_json(
    file_path: Path,
    data: list[dict]
):
    """
    Save dataset records as JSON.
    """

    with file_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )



# FR / NFR LABEL COUNTS

def print_label_counts(
    name: str,
    data: list[dict]
):
    """
    Print FR and NFR counts.
    """

    fr_count = sum(
        1
        for item in data
        if item["label"] == "FR"
    )

    nfr_count = sum(
        1
        for item in data
        if item["label"] == "NFR"
    )

    print(
        f"\n{name}"
    )

    print(
        f"Total: {len(data)}"
    )

    print(
        f"FR: {fr_count}"
    )

    print(
        f"NFR: {nfr_count}"
    )



# NFR CATEGORY COUNTS

def print_category_counts(
    name: str,
    data: list[dict]
):
    """
    Print counts for each NFR quality attribute.
    """

    counts = Counter(
        item["label"]
        for item in data
    )

    print(
        f"\n{name}"
    )

    print(
        f"Total: {len(data)}"
    )

    for category, count in sorted(
        counts.items()
    ):

        print(
            f"{category}: {count}"
        )



# MAIN

if __name__ == "__main__":

    
    # FR / NFR DATASET

    print(
        "\n================================"
    )

    print(
        "PREPARING FR / NFR DATASET"
    )

    print(
        "================================"
    )

    (
        train_data,
        validation_data,
        test_data
    ) = prepare_fr_nfr_dataset()

    save_json(
        OUTPUT_DIR
        / "fr_nfr_train.json",
        train_data
    )

    save_json(
        OUTPUT_DIR
        / "fr_nfr_validation.json",
        validation_data
    )

    save_json(
        OUTPUT_DIR
        / "fr_nfr_test.json",
        test_data
    )

    print_label_counts(
        "TRAIN SET",
        train_data
    )

    print_label_counts(
        "VALIDATION SET",
        validation_data
    )

    print_label_counts(
        "TEST SET",
        test_data
    )


    # NFR CATEGORY DATASET

    print(
        "\n================================"
    )

    print(
        "PREPARING NFR CATEGORY DATASET"
    )

    print(
        "================================"
    )

    (
        nfr_train,
        nfr_validation,
        nfr_test
    ) = prepare_nfr_category_dataset()

    save_json(
        OUTPUT_DIR
        / "nfr_category_train.json",
        nfr_train
    )

    save_json(
        OUTPUT_DIR
        / "nfr_category_validation.json",
        nfr_validation
    )

    save_json(
        OUTPUT_DIR
        / "nfr_category_test.json",
        nfr_test
    )

    print_category_counts(
        "NFR CATEGORY TRAIN SET",
        nfr_train
    )

    print_category_counts(
        "NFR CATEGORY VALIDATION SET",
        nfr_validation
    )

    print_category_counts(
        "NFR CATEGORY TEST SET",
        nfr_test
    )

 
    # FINISHED

    print(
        "\n================================"
    )

    print(
        "DATASET PREPARATION COMPLETE"
    )

    print(
        "================================"
    )

    print(
        "\nFiles saved to:"
    )

    print(
        OUTPUT_DIR
    )