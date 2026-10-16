"""
Create group-aware train / validation / test splits for the
ADR significance dataset.

Important:
All records belonging to the same:
    source_module + scenario_family + label
group remain in the same split.

Dataset:
    600 records
    120 groups
    5 records per group

Target split:
    Train      70% = 84 groups = 420 records
    Validation 15% = 18 groups = 90 records
    Test       15% = 18 groups = 90 records

The split is deterministic and stratified as closely as possible
by source module and class label.
"""

import csv
import random
from collections import Counter, defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = (
    BASE_DIR
    / "processed"
    / "adr_significance_final.csv"
)

SPLIT_DIR = (
    BASE_DIR
    / "splits"
)

TRAIN_PATH = (
    SPLIT_DIR
    / "train.csv"
)

VALIDATION_PATH = (
    SPLIT_DIR
    / "validation.csv"
)

TEST_PATH = (
    SPLIT_DIR
    / "test.csv"
)


RANDOM_SEED = 42


SOURCE_MODULES = [
    "architecture_decision",
    "database_design",
    "api_component_design",
    "quality_evaluation",
]


def load_rows():
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def group_rows(rows):
    groups = defaultdict(list)

    for row in rows:
        key = (
            row["source_module"],
            row["scenario_family"],
            row["label"],
        )

        groups[key].append(
            row
        )

    return groups


def split_groups(groups):
    """
    Each source-module / label combination has 15 groups:

        4 modules
        x 2 labels
        x 15 groups
        = 120 groups

    For each combination:
        train      = 11 groups
        validation = 2 groups
        test       = 2 groups

    This gives:
        train = 88 groups

    That would be too large.

    Therefore we distribute the 120 groups using:
        84 train
        18 validation
        18 test

    while preserving source/class balance as closely as possible.
    """

    random.seed(
        RANDOM_SEED
    )

    buckets = defaultdict(list)

    for key in groups:
        source_module, _, label = key

        buckets[
            (
                source_module,
                label,
            )
        ].append(
            key
        )

    for bucket_keys in buckets.values():
        random.shuffle(
            bucket_keys
        )

    train_groups = []
    validation_groups = []
    test_groups = []

    # There are 8 source/label buckets.
    #
    # Six buckets:
    #   11 train, 2 validation, 2 test
    #
    # Two buckets:
    #   9 train, 3 validation, 3 test
    #
    # Totals:
    #   Train = 6*11 + 2*9 = 84
    #   Val   = 6*2  + 2*3 = 18
    #   Test  = 6*2  + 2*3 = 18
    #
    # Rotate which buckets receive the 9/3/3 allocation
    # so the process remains explicit and reproducible.

    special_buckets = {
        (
            "architecture_decision",
            "0",
        ),
        (
            "quality_evaluation",
            "1",
        ),
    }

    for bucket_key in sorted(
        buckets.keys()
    ):
        bucket_groups = buckets[
            bucket_key
        ]

        if len(bucket_groups) != 15:
            raise ValueError(
                f"Expected 15 groups in bucket "
                f"{bucket_key}, found "
                f"{len(bucket_groups)}."
            )

        if bucket_key in special_buckets:
            train_count = 9
            validation_count = 3
            test_count = 3
        else:
            train_count = 11
            validation_count = 2
            test_count = 2

        train_groups.extend(
            bucket_groups[
                :train_count
            ]
        )

        validation_groups.extend(
            bucket_groups[
                train_count:
                train_count
                + validation_count
            ]
        )

        test_groups.extend(
            bucket_groups[
                train_count
                + validation_count:
                train_count
                + validation_count
                + test_count
            ]
        )

    return (
        train_groups,
        validation_groups,
        test_groups,
    )


def flatten_groups(
    groups,
    selected_keys,
):
    rows = []

    for key in selected_keys:
        rows.extend(
            groups[key]
        )

    return rows


def save_split(
    path,
    rows,
):
    if not rows:
        raise ValueError(
            f"No rows available for {path.name}."
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(
                rows[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(rows)


def group_key(row):
    return (
        row["source_module"],
        row["scenario_family"],
        row["label"],
    )


def validate_no_leakage(
    train_rows,
    validation_rows,
    test_rows,
):
    train_groups = {
        group_key(row)
        for row in train_rows
    }

    validation_groups = {
        group_key(row)
        for row in validation_rows
    }

    test_groups = {
        group_key(row)
        for row in test_rows
    }

    train_val_overlap = (
        train_groups
        & validation_groups
    )

    train_test_overlap = (
        train_groups
        & test_groups
    )

    validation_test_overlap = (
        validation_groups
        & test_groups
    )

    return (
        train_val_overlap,
        train_test_overlap,
        validation_test_overlap,
    )


def print_split_summary(
    name,
    rows,
):
    labels = Counter(
        row["label"]
        for row in rows
    )

    sources = Counter(
        row["source_module"]
        for row in rows
    )

    domains = Counter(
        row["domain"]
        for row in rows
    )

    groups = {
        group_key(row)
        for row in rows
    }

    print()
    print(name)
    print("-" * len(name))

    print(
        f"Records: {len(rows)}"
    )

    print(
        f"Groups: {len(groups)}"
    )

    print(
        f"Significant: "
        f"{labels.get('1', 0)}"
    )

    print(
        f"Not significant: "
        f"{labels.get('0', 0)}"
    )

    print("Source modules:")

    for source in SOURCE_MODULES:
        print(
            f"  {source}: "
            f"{sources.get(source, 0)}"
        )

    print("Domains:")

    for domain, count in sorted(
        domains.items()
    ):
        print(
            f"  {domain}: {count}"
        )


def main():
    rows = load_rows()

    groups = group_rows(
        rows
    )

    print()
    print("ADR Significance Group-Aware Split")
    print("==================================")

    print(
        f"Dataset records: {len(rows)}"
    )

    print(
        f"Scenario groups: {len(groups)}"
    )

    # Verify every group contains the expected five domains.
    invalid_group_sizes = {
        key: len(group_rows_list)
        for key, group_rows_list
        in groups.items()
        if len(group_rows_list) != 5
    }

    if invalid_group_sizes:
        raise ValueError(
            "Some scenario groups do not "
            "contain exactly five records: "
            f"{invalid_group_sizes}"
        )

    (
        train_group_keys,
        validation_group_keys,
        test_group_keys,
    ) = split_groups(
        groups
    )

    train_rows = flatten_groups(
        groups,
        train_group_keys,
    )

    validation_rows = flatten_groups(
        groups,
        validation_group_keys,
    )

    test_rows = flatten_groups(
        groups,
        test_group_keys,
    )

    (
        train_val_overlap,
        train_test_overlap,
        validation_test_overlap,
    ) = validate_no_leakage(
        train_rows,
        validation_rows,
        test_rows,
    )

    print_split_summary(
        "TRAIN",
        train_rows,
    )

    print_split_summary(
        "VALIDATION",
        validation_rows,
    )

    print_split_summary(
        "TEST",
        test_rows,
    )

    print()
    print("Leakage checks")
    print("--------------")

    print(
        "Train / validation group overlap: "
        f"{len(train_val_overlap)}"
    )

    print(
        "Train / test group overlap: "
        f"{len(train_test_overlap)}"
    )

    print(
        "Validation / test group overlap: "
        f"{len(validation_test_overlap)}"
    )

    total_records = (
        len(train_rows)
        + len(validation_rows)
        + len(test_rows)
    )

    total_groups = (
        len(train_group_keys)
        + len(validation_group_keys)
        + len(test_group_keys)
    )

    passed = (
        len(rows) == 600
        and
        len(groups) == 120
        and
        len(train_rows) == 420
        and
        len(validation_rows) == 90
        and
        len(test_rows) == 90
        and
        len(train_group_keys) == 84
        and
        len(validation_group_keys) == 18
        and
        len(test_group_keys) == 18
        and
        total_records == 600
        and
        total_groups == 120
        and
        not train_val_overlap
        and
        not train_test_overlap
        and
        not validation_test_overlap
    )

    print()
    print(
        f"Total split records: "
        f"{total_records}"
    )

    print(
        f"Total split groups: "
        f"{total_groups}"
    )

    print()

    if not passed:
        print(
            "GROUP-AWARE SPLIT VALIDATION: FAILED"
        )
        return

    save_split(
        TRAIN_PATH,
        train_rows,
    )

    save_split(
        VALIDATION_PATH,
        validation_rows,
    )

    save_split(
        TEST_PATH,
        test_rows,
    )

    print(
        "GROUP-AWARE SPLIT VALIDATION: PASSED"
    )

    print()
    print("Created:")
    print(
        f"  {TRAIN_PATH}"
    )
    print(
        f"  {VALIDATION_PATH}"
    )
    print(
        f"  {TEST_PATH}"
    )


if __name__ == "__main__":
    main()