# Loads and normalizes the Requirement Analysis datasets used by DesignTraceAI.
# The loader supports PROMISE, PROMISE_exp, PURE, and human-gold data in
# multiple formats and converts them into Python-friendly records for
# preprocessing, training, evaluation, and dataset inspection.

from pathlib import Path
import csv
import io
import json
import tarfile
import zipfile
import xml.etree.ElementTree as ET
from typing import Any


# BASE PATHS

BASE_DIR = Path(__file__).resolve().parents[2]

DATASET_DIR = BASE_DIR / "datasets" / "requirement_analysis"

PROMISE_DIR = DATASET_DIR / "promise"
PROMISE_EXP_DIR = DATASET_DIR / "promise_exp"
PURE_DIR = DATASET_DIR / "pure"
HUMAN_GOLD_DIR = DATASET_DIR / "human_gold"


# GENERIC HELPERS

def load_csv_file(file_path: Path) -> list[dict[str, Any]]:
    # Load a CSV file into a list of dictionaries.

    if not file_path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {file_path}"
        )

    rows = []

    with file_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            rows.append(dict(row))

    return rows


def load_text_file(file_path: Path) -> str:
    # Load a plain-text file.

    if not file_path.exists():
        raise FileNotFoundError(
            f"Text file not found: {file_path}"
        )

    return file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )


def find_files(
    directory: Path,
    extensions: tuple[str, ...]
) -> list[Path]:
    # Recursively find files with selected extensions.

    if not directory.exists():
        return []

    files = []

    for extension in extensions:
        files.extend(
            directory.rglob(f"*{extension}")
        )

    return sorted(files)


# ARFF PARSER

def parse_arff_text(
    text: str,
    source_name: str = ""
) -> list[dict[str, Any]]:

    attributes = []
    records = []

    data_started = False

    for raw_line in text.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        # ARFF comment
        if line.startswith("%"):
            continue

        lower_line = line.lower()


        # ATTRIBUTE

        if lower_line.startswith("@attribute"):

            # Example:
            # @attribute requirement string
            # @attribute class {F,NF}

            rest = line[len("@attribute"):].strip()

            if rest.startswith("'"):
                end_index = rest.find("'", 1)

                attribute_name = rest[
                    1:end_index
                ]

            elif rest.startswith('"'):
                end_index = rest.find('"', 1)

                attribute_name = rest[
                    1:end_index
                ]

            else:
                attribute_name = rest.split(
                    maxsplit=1
                )[0]

            attributes.append(
                attribute_name
            )

            continue

        # DATA START

        if lower_line.startswith("@data"):

            data_started = True
            continue

        if not data_started:
            continue


        # DATA ROW

        try:
            reader = csv.reader(
                [line],
                quotechar="'",
                skipinitialspace=True
            )

            values = next(reader)

        except Exception:
            continue

        # If the row contains fewer/more columns,
        # we still try to preserve the data.
        record = {}

        for index, attribute in enumerate(
            attributes
        ):

            value = (
                values[index].strip()
                if index < len(values)
                else None
            )

            if value == "?":
                value = None

            record[attribute] = value

        record["_source_file"] = source_name

        records.append(record)

    return records


def load_arff_file(
    file_path: Path
) -> list[dict[str, Any]]:
    # Load an ARFF file.

    if not file_path.exists():
        raise FileNotFoundError(
            f"ARFF file not found: {file_path}"
        )

    text = file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    return parse_arff_text(
        text,
        source_name=file_path.name
    )


# PROMISE DATASET

def load_promise_dataset() -> list[dict[str, Any]]:
    """
    Load original PROMISE NFR dataset.

    Current project format:
        datasets/
        requirement_analysis/
        promise/
        nfr.tar

    The TAR archive is inspected for:
    - .arff
    - .csv
    - .txt
    """

    records = []

    tar_files = find_files(
        PROMISE_DIR,
        (".tar",)
    )

    for tar_path in tar_files:

        try:

            with tarfile.open(
                tar_path,
                mode="r:*"
            ) as archive:

                for member in archive.getmembers():

                    if not member.isfile():
                        continue

                    member_name = member.name.lower()

                    extracted = archive.extractfile(
                        member
                    )

                    if extracted is None:
                        continue

                    raw_bytes = extracted.read()

                    text = raw_bytes.decode(
                        "utf-8",
                        errors="ignore"
                    )


                    # ARFF

                    if member_name.endswith(
                        ".arff"
                    ):

                        data = parse_arff_text(
                            text,
                            source_name=member.name
                        )

                        records.extend(
                            data
                        )


                    # CSV

                    elif member_name.endswith(
                        ".csv"
                    ):

                        reader = csv.DictReader(
                            io.StringIO(text)
                        )

                        for row in reader:

                            row = dict(row)

                            row["_source_file"] = (
                                member.name
                            )

                            records.append(
                                row
                            )


                    # TEXT

                    elif member_name.endswith(
                        ".txt"
                    ):

                        records.append({
                            "text": text.strip(),
                            "_source_file":
                                member.name
                        })

        except tarfile.TarError as exc:

            print(
                f"Could not read PROMISE archive "
                f"{tar_path}: {exc}"
            )

    # Also support extracted files if you later
    # unpack the archive manually.

    arff_files = find_files(
        PROMISE_DIR,
        (".arff",)
    )

    for file_path in arff_files:

        records.extend(
            load_arff_file(
                file_path
            )
        )

    csv_files = find_files(
        PROMISE_DIR,
        (".csv",)
    )

    for file_path in csv_files:

        data = load_csv_file(
            file_path
        )

        for row in data:

            row["_source_file"] = (
                file_path.name
            )

            records.append(row)

    return records


# PROMISE_EXP DATASET

def load_promise_exp_dataset() -> list[dict[str, Any]]:

    # Load PROMISE_exp dataset.

    # Current project format:

    #     promise_exp/
    #         PROMISE_exp.arff

    # Used mainly for:
    # - FR/NFR classification evaluation
    # - NFR quality-attribute evaluation
    records = []

    arff_files = find_files(
        PROMISE_EXP_DIR,
        (".arff",)
    )

    for file_path in arff_files:

        data = load_arff_file(
            file_path
        )

        records.extend(
            data
        )

    return records


# PURE XML HELPERS

def extract_xml_text(
    xml_text: str
) -> str:

    # Extract readable textual content from XML.

    # This does not assume one exact PURE XML schema.
    # It collects non-empty text nodes.

    try:

        root = ET.fromstring(
            xml_text
        )

    except ET.ParseError:

        return ""

    text_parts = []

    for element in root.iter():

        if element.text:

            value = element.text.strip()

            if value:
                text_parts.append(
                    value
                )

    return "\n".join(
        text_parts
    )


# PURE DATASET

def load_pure_documents() -> list[dict[str, Any]]:

    documents = []

    zip_files = find_files(
        PURE_DIR,
        (".zip",)
    )

    for zip_path in zip_files:

        try:

            with zipfile.ZipFile(
                zip_path,
                mode="r"
            ) as archive:

                for member_name in archive.namelist():

                    # Skip folders
                    if member_name.endswith("/"):
                        continue

                    lower_name = (
                        member_name.lower()
                    )

                    try:

                        raw_bytes = archive.read(
                            member_name
                        )

                    except Exception:
                        continue


                    # TEXT

                    if lower_name.endswith(
                        ".txt"
                    ):

                        text = raw_bytes.decode(
                            "utf-8",
                            errors="ignore"
                        )

                        documents.append({
                            "document_id":
                                member_name,

                            "source_archive":
                                zip_path.name,

                            "file_type":
                                "txt",

                            "content":
                                text.strip()
                        })


                    # XML

                    elif lower_name.endswith(
                        ".xml"
                    ):

                        xml_text = (
                            raw_bytes.decode(
                                "utf-8",
                                errors="ignore"
                            )
                        )

                        readable_text = (
                            extract_xml_text(
                                xml_text
                            )
                        )

                        documents.append({
                            "document_id":
                                member_name,

                            "source_archive":
                                zip_path.name,

                            "file_type":
                                "xml",

                            "content":
                                readable_text,

                            "raw_xml":
                                xml_text
                        })


                    # CSV

                    elif lower_name.endswith(
                        ".csv"
                    ):

                        text = raw_bytes.decode(
                            "utf-8",
                            errors="ignore"
                        )

                        reader = csv.DictReader(
                            io.StringIO(text)
                        )

                        documents.append({
                            "document_id":
                                member_name,

                            "source_archive":
                                zip_path.name,

                            "file_type":
                                "csv",

                            "content":
                                [
                                    dict(row)
                                    for row in reader
                                ]
                        })


                    # JSON

                    elif lower_name.endswith(
                        ".json"
                    ):

                        text = raw_bytes.decode(
                            "utf-8",
                            errors="ignore"
                        )

                        try:
                            content = json.loads(
                                text
                            )

                        except json.JSONDecodeError:
                            content = None

                        documents.append({
                            "document_id":
                                member_name,

                            "source_archive":
                                zip_path.name,

                            "file_type":
                                "json",

                            "content":
                                content
                        })

        except zipfile.BadZipFile as exc:

            print(
                f"Could not read PURE ZIP "
                f"{zip_path}: {exc}"
            )

    return documents


# HUMAN GOLD DATASET

def load_human_gold_dataset() -> list[dict[str, Any]]:
    """
    Load manually reviewed Requirement Analysis
    gold/candidate dataset.

    Current project file:

        requirement_analysis_human_gold_candidate.csv
    """

    records = []

    csv_files = find_files(
        HUMAN_GOLD_DIR,
        (".csv",)
    )

    for file_path in csv_files:

        data = load_csv_file(
            file_path
        )

        for row in data:

            row["_source_file"] = (
                file_path.name
            )

            records.append(row)

    return records



# NORMALIZATION HELPERS

def normalize_boolean(
    value: Any
) -> bool | None:
    """
    Convert common dataset boolean values.
    """

    if value is None:
        return None

    if isinstance(
        value,
        bool
    ):
        return value

    text = str(
        value
    ).strip().lower()

    if text in {
        "true",
        "1",
        "yes",
        "y"
    }:
        return True

    if text in {
        "false",
        "0",
        "no",
        "n"
    }:
        return False

    return None


def normalize_requirement_type(
    value: Any
) -> str | None:
    """
    Normalize dataset labels to FR / NFR.
    """

    if value is None:
        return None

    text = str(
        value
    ).strip().upper()

    functional_labels = {
        "FR",
        "F",
        "FUNCTIONAL",
        "FUNCTIONAL REQUIREMENT"
    }

    non_functional_labels = {
        "NFR",
        "NF",
        "NON-FUNCTIONAL",
        "NON FUNCTIONAL",
        "NON-FUNCTIONAL REQUIREMENT"
    }

    if text in functional_labels:
        return "FR"

    if text in non_functional_labels:
        return "NFR"

    return None



# INSPECTION HELPERS

def inspect_dataset_sample(
    records: list[dict[str, Any]],
    count: int = 3
) -> None:
    """
    Print a few records so you can understand
    the actual dataset columns.
    """

    print(
        f"\nTotal records: {len(records)}"
    )

    for index, record in enumerate(
        records[:count],
        start=1
    ):

        print(
            f"\n--- SAMPLE {index} ---"
        )

        print(
            record
        )


# DATASET SUMMARY

def get_dataset_summary() -> dict[str, Any]:
    """
    Return counts for all Requirement Analysis datasets.
    """

    promise = (
        load_promise_dataset()
    )

    promise_exp = (
        load_promise_exp_dataset()
    )

    pure = (
        load_pure_documents()
    )

    human_gold = (
        load_human_gold_dataset()
    )

    return {
        "promise_records":
            len(promise),

        "promise_exp_records":
            len(promise_exp),

        "pure_documents":
            len(pure),

        "human_gold_records":
            len(human_gold)
    }


# MANUAL TEST

if __name__ == "__main__":

    print(
        "\n================================"
    )

    print(
        "REQUIREMENT ANALYSIS DATASETS"
    )

    print(
        "================================"
    )

    summary = get_dataset_summary()

    for name, count in summary.items():

        print(
            f"{name}: {count}"
        )

    print(
        "\nPROMISE EXP SAMPLE"
    )

    promise_exp = (
        load_promise_exp_dataset()
    )

    inspect_dataset_sample(
        promise_exp,
        count=2
    )

    print(
        "\nHUMAN GOLD SAMPLE"
    )

    human_gold = (
        load_human_gold_dataset()
    )

    inspect_dataset_sample(
        human_gold,
        count=2
    )

    print(
        "\nPURE SAMPLE"
    )

    pure = (
        load_pure_documents()
    )

    inspect_dataset_sample(
        pure,
        count=1
    )