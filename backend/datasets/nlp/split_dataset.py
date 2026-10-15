"""Split DesignTrace AI NLP annotations by project to avoid leakage."""

import json
import random
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
INPUT_FILE = DATA_DIR / "synthetic_annotated_requirements_1000.json"

SEED = 42
TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15


def split_dataset() -> None:
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list) or not records:
        raise ValueError("Expected a non-empty JSON list of requirements.")

    projects = defaultdict(list)
    seen_ids = set()

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each requirement must be a JSON object.")

        project_id = record.get("project_id")
        requirement_id = record.get("requirement_id")

        if not project_id or not requirement_id:
            raise ValueError(
                "Each requirement needs project_id and requirement_id."
            )

        unique_key = (project_id, requirement_id)
        if unique_key in seen_ids:
            raise ValueError(f"Duplicate requirement: {unique_key}")

        seen_ids.add(unique_key)
        projects[project_id].append(record)

    if len(projects) < 3:
        raise ValueError(
            "At least 3 projects are needed for project-separated splits."
        )

    project_ids = sorted(projects)
    random.Random(SEED).shuffle(project_ids)

    total = len(records)
    targets = [
        total * TRAIN_RATIO,
        total * VALIDATION_RATIO,
        total * TEST_RATIO,
    ]

    splits = [[], [], []]
    counts = [0, 0, 0]

    # Allocate larger projects first.
    project_ids.sort(
        key=lambda project: len(projects[project]),
        reverse=True,
    )

    for index, project_id in enumerate(project_ids):
        remaining = len(project_ids) - index
        empty = [i for i in range(3) if not splits[i]]

        # Reserve at least one project for every split.
        if remaining == len(empty):
            chosen = max(empty, key=lambda i: targets[i])
        else:
            chosen = max(
                range(3),
                key=lambda i: (
                    targets[i] - counts[i]
                ) / targets[i],
            )

        splits[chosen].extend(projects[project_id])
        counts[chosen] += len(projects[project_id])

    filenames = ("train.json", "validation.json", "test.json")

    for filename, items in zip(filenames, splits):
        output_path = DATA_DIR / filename

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(items, file, ensure_ascii=False, indent=2)
            file.write("\n")

        unique_projects = sorted({
            item["project_id"] for item in items
        })

        print(
            f"{filename}: {len(items)} requirements, "
            f"{len(unique_projects)} projects: {unique_projects}"
        )

    print(f"Total: {sum(counts)} requirements")
    print("Project-separated split completed successfully.")


if __name__ == "__main__":
    split_dataset()
