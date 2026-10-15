"""
DesignTrace AI - Project-Independent Dataset Split
=================================================

Creates project-independent datasets for NLP
concept extraction experiments.

Inputs:
    datasets/nlp/train.json
    datasets/nlp/validation.json
    datasets/nlp/test.json
    datasets/nlp/independent_test.json

Outputs:
    datasets/nlp/project_split/train.json
    datasets/nlp/project_split/validation.json
    datasets/nlp/project_split/test.json
    datasets/nlp/project_split/split_report.json

Important:
    Entire projects are assigned to one split.
    Original datasets are never overwritten.
    Conflicting annotations stop the process.
"""

import json
import random
from collections import Counter, defaultdict
from pathlib import Path


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "datasets" / "nlp"

OUTPUT_DIR = DATA_DIR / "project_split"

INPUT_FILES = [
    "train.json",
    "validation.json",
    "test.json",
    "independent_test.json",
]

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15

SEED = 42

REQUIRED_FIELDS = {
    "requirement_id",
    "project_id",
    "text",
    "annotations",
}


# --------------------------------------------------
# 2. Load datasets
# --------------------------------------------------

def load_all_datasets():

    all_requirements = []

    for filename in INPUT_FILES:

        path = DATA_DIR / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {path}"
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(
                f"{filename} must contain a JSON list."
            )

        for index, example in enumerate(data):

            if not isinstance(example, dict):
                raise ValueError(
                    f"{filename}, item {index}: "
                    "expected a JSON object."
                )

            missing = REQUIRED_FIELDS - example.keys()

            if missing:
                raise ValueError(
                    f"{filename}, item {index}: "
                    f"missing fields {sorted(missing)}"
                )

            if not isinstance(
                example["annotations"], list
            ):
                raise ValueError(
                    f"{filename}, item {index}: "
                    "annotations must be a list."
                )

            for field in (
                "requirement_id",
                "project_id",
                "text",
            ):
                if (
                    not isinstance(example[field], str)
                    or not example[field].strip()
                ):
                    raise ValueError(
                        f"{filename}, item {index}: "
                        f"invalid {field}"
                    )

            all_requirements.append(example)

        print(
            f"{filename}: {len(data)} requirements"
        )

    return all_requirements


# --------------------------------------------------
# 3. Normalize and validate annotations
# --------------------------------------------------

def normalize_text(text):
    return " ".join(text.casefold().split())


def annotation_signature(example):

    text = example["text"]
    signatures = []

    for annotation in example["annotations"]:

        if not isinstance(annotation, dict):
            raise ValueError(
                "Annotation must be a JSON object."
            )

        for field in (
            "start",
            "end",
            "text",
            "label",
        ):
            if field not in annotation:
                raise ValueError(
                    f"Missing annotation field: {field}"
                )

        start = annotation["start"]
        end = annotation["end"]

        if (
            type(start) is not int
            or type(end) is not int
            or start < 0
            or end > len(text)
            or start >= end
        ):
            raise ValueError(
                "Invalid annotation offsets in "
                f"{example['requirement_id']}"
            )

        if text[start:end] != annotation["text"]:
            raise ValueError(
                "Annotation text mismatch in "
                f"{example['requirement_id']}"
            )

        if annotation["label"] not in {
            "ENTITY",
            "ATTRIBUTE",
            "ACTION",
        }:
            raise ValueError(
                "Unsupported annotation label in "
                f"{example['requirement_id']}"
            )

        signatures.append(
            (
                start,
                end,
                annotation["label"],
            )
        )

    signatures.sort()

    for previous, current in zip(
        signatures,
        signatures[1:],
    ):
        if current[0] < previous[1]:
            raise ValueError(
                "Overlapping annotations in "
                f"{example['requirement_id']}"
            )

    return tuple(signatures)


# --------------------------------------------------
# 4. Remove duplicates and detect conflicts
# --------------------------------------------------

def deduplicate_requirements(requirements):

    unique = {}

    duplicates_removed = 0
    conflicts = []

    for example in requirements:

        text_key = normalize_text(example["text"])
        signature = annotation_signature(example)

        if text_key not in unique:
            unique[text_key] = example
            continue

        existing = unique[text_key]

        existing_signature = annotation_signature(
            existing
        )

        if (
            signature != existing_signature
            or example["text"] != existing["text"]
        ):
            conflicts.append({
                "text": example["text"],
                "first_requirement_id":
                    existing["requirement_id"],
                "second_requirement_id":
                    example["requirement_id"],
                "first_project":
                    existing["project_id"],
                "second_project":
                    example["project_id"],
            })
            continue

        duplicates_removed += 1

    if conflicts:

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        conflict_path = (
            OUTPUT_DIR / "annotation_conflicts.json"
        )

        with conflict_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                conflicts,
                file,
                indent=2,
                ensure_ascii=False,
            )

        raise ValueError(
            f"Found {len(conflicts)} duplicate-text "
            "annotation conflicts. "
            f"Review {conflict_path} before splitting."
        )

    return list(unique.values()), duplicates_removed


# --------------------------------------------------
# 5. Group by project
# --------------------------------------------------

def group_by_project(requirements):

    projects = defaultdict(list)

    for example in requirements:
        projects[example["project_id"]].append(
            example
        )

    return dict(projects)


# --------------------------------------------------
# 6. Split complete projects
# --------------------------------------------------

def split_projects(projects):

    project_ids = list(projects.keys())

    if len(project_ids) < 3:
        raise ValueError(
            "At least 3 different projects are "
            "required for train/validation/test."
        )

    rng = random.Random(SEED)

    # Randomize tie-breaking while keeping
    # results reproducible.
    rng.shuffle(project_ids)

    # Place larger projects first to improve
    # requirement-count balance.
    project_ids.sort(
        key=lambda pid: len(projects[pid]),
        reverse=True,
    )

    total_requirements = sum(
        len(items)
        for items in projects.values()
    )

    targets = {
        "train": total_requirements * TRAIN_RATIO,
        "validation":
            total_requirements * VALIDATION_RATIO,
        "test": total_requirements * TEST_RATIO,
    }

    splits = {
        "train": [],
        "validation": [],
        "test": [],
    }

    assigned_projects = {
        "train": [],
        "validation": [],
        "test": [],
    }

    counts = {
        "train": 0,
        "validation": 0,
        "test": 0,
    }

    # Assign one project to each split first,
    # ensuring all three are non-empty.
    for split_name, project_id in zip(
        ("train", "validation", "test"),
        project_ids[:3],
    ):
        assigned_projects[split_name].append(
            project_id
        )

        splits[split_name].extend(
            projects[project_id]
        )

        counts[split_name] += len(
            projects[project_id]
        )

    # Assign remaining projects based on
    # the current target deficits.
    for project_id in project_ids[3:]:

        size = len(projects[project_id])

        split_name = max(
            targets,
            key=lambda name: (
                (targets[name] - counts[name])
                / targets[name]
            ),
        )

        assigned_projects[split_name].append(
            project_id
        )

        splits[split_name].extend(
            projects[project_id]
        )

        counts[split_name] += size

    # Shuffle requirements inside each split.
    for split_name in splits:
        rng.shuffle(splits[split_name])

    return splits, assigned_projects


# --------------------------------------------------
# 7. Verify separation
# --------------------------------------------------

def verify_splits(splits):

    project_sets = {}
    text_sets = {}

    for name, requirements in splits.items():

        project_sets[name] = {
            item["project_id"]
            for item in requirements
        }

        text_sets[name] = {
            normalize_text(item["text"])
            for item in requirements
        }

    pairs = [
        ("train", "validation"),
        ("train", "test"),
        ("validation", "test"),
    ]

    for first, second in pairs:

        shared_projects = (
            project_sets[first]
            & project_sets[second]
        )

        shared_texts = (
            text_sets[first]
            & text_sets[second]
        )

        if shared_projects:
            raise ValueError(
                f"Project overlap between "
                f"{first} and {second}: "
                f"{sorted(shared_projects)}"
            )

        if shared_texts:
            raise ValueError(
                f"Duplicate texts between "
                f"{first} and {second}: "
                f"{len(shared_texts)}"
            )

    print(
        "\nProject separation: PASS"
    )

    print(
        "Cross-split duplicate texts: 0"
    )


# --------------------------------------------------
# 8. Save datasets and report
# --------------------------------------------------

def save_results(
    splits,
    assigned_projects,
    original_count,
    duplicates_removed,
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "seed": SEED,
        "original_requirements": original_count,
        "unique_requirements":
            sum(len(items) for items in splits.values()),
        "duplicates_removed": duplicates_removed,
        "target_ratios": {
            "train": TRAIN_RATIO,
            "validation": VALIDATION_RATIO,
            "test": TEST_RATIO,
        },
        "splits": {},
        "project_overlap": False,
        "cross_split_duplicate_texts": 0,
    }

    for name, requirements in splits.items():

        path = OUTPUT_DIR / f"{name}.json"

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                requirements,
                file,
                indent=2,
                ensure_ascii=False,
            )

        label_counts = Counter(
            annotation["label"]
            for example in requirements
            for annotation in example["annotations"]
        )

        report["splits"][name] = {
            "requirements": len(requirements),
            "projects": assigned_projects[name],
            "project_count":
                len(assigned_projects[name]),
            "label_counts": dict(label_counts),
        }

        print(f"\n{name.upper()}")
        print(
            " Requirements:",
            len(requirements),
        )
        print(
            " Projects:",
            len(assigned_projects[name]),
        )
        print(
            " Project IDs:",
            assigned_projects[name],
        )
        print(
            " Label counts:",
            dict(label_counts),
        )

    report_path = (
        OUTPUT_DIR / "split_report.json"
    )

    with report_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        "\nReport saved to:",
        report_path,
    )


# --------------------------------------------------
# 9. Main
# --------------------------------------------------

def main():

    print(
        "DesignTrace AI - Project-Independent Split"
    )
    print("-----------------------------------------")

    requirements = load_all_datasets()

    original_count = len(requirements)

    print(
        "\nTotal input requirements:",
        original_count,
    )

    unique_requirements, removed = (
        deduplicate_requirements(requirements)
    )

    print(
        "Unique requirements:",
        len(unique_requirements),
    )

    print(
        "Exact duplicates removed:",
        removed,
    )

    projects = group_by_project(
        unique_requirements
    )

    print(
        "Total projects:",
        len(projects),
    )

    splits, assigned_projects = split_projects(
        projects
    )

    verify_splits(splits)

    save_results(
        splits,
        assigned_projects,
        original_count,
        removed,
    )

    print(
        "\n-----------------------------------------"
    )
    print(
        "Project-independent splitting completed."
    )


if __name__ == "__main__":
    main()
