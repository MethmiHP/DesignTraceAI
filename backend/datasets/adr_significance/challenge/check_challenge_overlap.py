import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

CHALLENGE_FILE = (
    BASE_DIR
    / "adr_significance_challenge.csv"
)

FINAL_DATASET_FILE = (
    BASE_DIR.parent
    / "processed"
    / "adr_significance_final.csv"
)


def load_rows(path):
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def main():
    challenge_rows = load_rows(
        CHALLENGE_FILE
    )

    final_rows = load_rows(
        FINAL_DATASET_FILE
    )

    challenge_families = {
        row["scenario_family"]
        for row in challenge_rows
    }

    final_families = {
        row["scenario_family"]
        for row in final_rows
    }

    overlap = (
        challenge_families
        & final_families
    )

    print()
    print("ADR Challenge Set Overlap Check")
    print("===============================")

    print(
        f"Challenge records: "
        f"{len(challenge_rows)}"
    )

    print(
        f"Challenge families: "
        f"{len(challenge_families)}"
    )

    print(
        f"Frozen dataset records: "
        f"{len(final_rows)}"
    )

    print(
        f"Frozen dataset families: "
        f"{len(final_families)}"
    )

    print()
    print(
        f"Scenario-family overlap: "
        f"{len(overlap)}"
    )

    if overlap:
        print()
        print("Overlapping families")
        print("--------------------")

        for family in sorted(overlap):
            print(family)

        print()
        print(
            "FAILED: challenge set contains "
            "scenario families already present "
            "in the frozen dataset."
        )

    else:
        print()
        print(
            "PASSED: no scenario-family overlap "
            "with the frozen dataset."
        )

        print(
            "The challenge benchmark is independent "
            "at scenario-family level."
        )


if __name__ == "__main__":
    main()