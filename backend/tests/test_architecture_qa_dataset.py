from __future__ import annotations

import json
from pathlib import Path

from modules.architecture_design.training.dataset_utils import (
    LABEL_LIST,
    labels_to_multihot,
    normalize_statement,
    validate_dataset,
)


DATASET_DIR = (
    Path(__file__).resolve().parent.parent
    / "datasets"
    / "architecture_qa"
)


def load_json(name: str):
    with (
        DATASET_DIR / name
    ).open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def test_dataset_loads():
    records = load_json(
        "qa_dataset.json"
    )

    # Temporary M7.1A construction-stage check.
    # Increase this to >=900 after dataset expansion.
    assert len(records) >= 900


def test_six_label_constraint():
    records = load_json(
        "qa_dataset.json"
    )

    allowed = set(LABEL_LIST)

    for record in records:
        assert set(
            record["labels"]
        ).issubset(allowed)


def test_multihot_encoding():
    vector = labels_to_multihot(
        [
            "Security",
            "Performance",
        ]
    )

    assert vector == [
        1,
        0,
        1,
        0,
        0,
        0,
    ]


def test_no_duplicate_statements():
    records = load_json(
        "qa_dataset.json"
    )

    normalized = [
        normalize_statement(
            record["statement"]
        )
        for record in records
    ]

    assert len(normalized) == len(
        set(normalized)
    )


def test_no_cross_split_overlap():
    train = load_json(
        "train.json"
    )

    validation = load_json(
        "validation.json"
    )

    test = load_json(
        "test.json"
    )

    train_texts = {
        normalize_statement(
            r["statement"]
        )
        for r in train
    }

    validation_texts = {
        normalize_statement(
            r["statement"]
        )
        for r in validation
    }

    test_texts = {
        normalize_statement(
            r["statement"]
        )
        for r in test
    }

    assert train_texts.isdisjoint(
        validation_texts
    )

    assert train_texts.isdisjoint(
        test_texts
    )

    assert validation_texts.isdisjoint(
        test_texts
    )


def test_all_qas_in_each_split():

    for filename in (
        "train.json",
        "validation.json",
        "test.json",
    ):
        records = load_json(filename)

        labels_found = set()

        for record in records:
            labels_found.update(
                record["labels"]
            )

        assert labels_found == set(
            LABEL_LIST
        )


def test_split_proportions():
    full = load_json(
        "qa_dataset.json"
    )

    train = load_json(
        "train.json"
    )

    validation = load_json(
        "validation.json"
    )

    test = load_json(
        "test.json"
    )

    total = len(full)

    train_ratio = len(train) / total
    val_ratio = len(validation) / total
    test_ratio = len(test) / total

    assert abs(
        train_ratio - 0.70
    ) <= 0.05

    assert abs(
        val_ratio - 0.15
    ) <= 0.05

    assert abs(
        test_ratio - 0.15
    ) <= 0.05


def test_multi_label_examples_exist():
    records = load_json(
        "qa_dataset.json"
    )

    multi_label = [
        r
        for r in records
        if len(r["labels"]) > 1
    ]

    assert len(multi_label) >= 50


def test_every_record_has_label():
    records = load_json(
        "qa_dataset.json"
    )

    for record in records:
        assert len(
            record["labels"]
        ) >= 1


def test_dataset_structure():
    records = load_json(
        "qa_dataset.json"
    )

    validate_dataset(records)

    required = {
        "example_id",
        "statement",
        "labels",
        "source_type",
        "domain",
    }

    for record in records:
        assert required.issubset(
            record.keys()
        )