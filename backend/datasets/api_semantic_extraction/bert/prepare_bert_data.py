import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

TRAIN_FILE = BASE_DIR / "train.csv"
VALIDATION_FILE = BASE_DIR / "validation.csv"
TEST_FILE = BASE_DIR / "test.csv"

OUTPUT_DIR = Path(__file__).resolve().parent / "prepared"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


LABEL_LIST = [
    "O",
    "B-ACTOR",
    "I-ACTOR",
    "B-ACTION",
    "I-ACTION",
    "B-RESOURCE",
    "I-RESOURCE",
]


def load_csv(
    path: Path,
) -> list[dict]:

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return list(
            csv.DictReader(file)
        )


def find_span(
    text: str,
    phrase: str,
):

    if not phrase:
        return None

    start = text.lower().find(
        phrase.lower()
    )

    if start == -1:
        return None

    end = start + len(phrase)

    return start, end


def tokenize_with_offsets(
    text: str,
):

    tokens = []

    start = None

    for index, char in enumerate(text):

        if char.isalnum() or char in {
            "_",
            "-",
        }:

            if start is None:
                start = index

        else:

            if start is not None:

                tokens.append(
                    {
                        "text": text[start:index],
                        "start": start,
                        "end": index,
                    }
                )

                start = None

    if start is not None:

        tokens.append(
            {
                "text": text[start:],
                "start": start,
                "end": len(text),
            }
        )

    return tokens


def apply_bio_labels(
    tokens,
    span,
    entity_type,
):

    if span is None:
        return

    entity_start, entity_end = span

    matching_indexes = []

    for index, token in enumerate(tokens):

        overlaps = (
            token["start"] < entity_end
            and token["end"] > entity_start
        )

        if overlaps:
            matching_indexes.append(index)

    if not matching_indexes:
        return

    first_index = matching_indexes[0]

    tokens[first_index]["label"] = (
        f"B-{entity_type}"
    )

    for index in matching_indexes[1:]:

        tokens[index]["label"] = (
            f"I-{entity_type}"
        )


def prepare_row(
    row: dict,
):

    text = row["requirement_text"]

    tokens = tokenize_with_offsets(
        text
    )

    for token in tokens:
        token["label"] = "O"

    actor_span = find_span(
        text,
        row["actor_text"],
    )

    action_span = find_span(
        text,
        row["action_text"],
    )

    resource_span = find_span(
        text,
        row["resource_text"],
    )

    apply_bio_labels(
        tokens,
        actor_span,
        "ACTOR",
    )

    apply_bio_labels(
        tokens,
        action_span,
        "ACTION",
    )

    apply_bio_labels(
        tokens,
        resource_span,
        "RESOURCE",
    )

    return {
        "requirement_id": row[
            "requirement_id"
        ],
        "domain": row[
            "domain"
        ],
        "text": text,
        "tokens": [
            token["text"]
            for token in tokens
        ],
        "labels": [
            token["label"]
            for token in tokens
        ],
    }


def save_json(
    records,
    path,
):

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            records,
            file,
            indent=2,
            ensure_ascii=False,
        )


def process_split(
    input_path,
    output_name,
):

    rows = load_csv(
        input_path
    )

    prepared = [
        prepare_row(row)
        for row in rows
    ]

    output_path = (
        OUTPUT_DIR
        / output_name
    )

    save_json(
        prepared,
        output_path,
    )

    print(
        f"{output_name}: "
        f"{len(prepared)} requirements"
    )

    return prepared


def main():

    print(
        "Preparing BERT dataset..."
    )

    train = process_split(
        TRAIN_FILE,
        "train.json",
    )

    validation = process_split(
        VALIDATION_FILE,
        "validation.json",
    )

    test = process_split(
        TEST_FILE,
        "test.json",
    )

    print()
    print(
        "Label set:"
    )

    for label in LABEL_LIST:
        print(label)

    print()
    print(
        "Example:"
    )

    example = train[0]

    print(
        example["text"]
    )

    print()

    for token, label in zip(
        example["tokens"],
        example["labels"],
    ):

        print(
            f"{token:<20} {label}"
        )

    print()
    print(
        "BERT data preparation complete."
    )


if __name__ == "__main__":
    main()