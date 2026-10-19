"""
Extract explicit project-independent database constraints
from natural-language requirements.
"""

import re


NUMBERS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "sixteen": 16,
    "eighteen": 18,
}

NUMBER_PATTERN = (
    r"(-?\d+(?:\.\d+)?|"
    + "|".join(NUMBERS)
    + r")"
)

SUBJECT = r"(.+?)\s+(?:must|shall|should)\s+"

COMPARISONS = [
    (
        rf"{SUBJECT}be\s+greater than or equal to\s+"
        rf"{NUMBER_PATTERN}\b",
        ">=",
    ),
    (
        rf"{SUBJECT}be\s+less than or equal to\s+"
        rf"{NUMBER_PATTERN}\b",
        "<=",
    ),
    (
        rf"{SUBJECT}be\s+at least\s+{NUMBER_PATTERN}\b",
        ">=",
    ),
    (
        rf"{SUBJECT}be\s+at most\s+{NUMBER_PATTERN}\b",
        "<=",
    ),
    (
        rf"{SUBJECT}be\s+(?:strictly\s+)?greater than\s+"
        rf"{NUMBER_PATTERN}\b",
        ">",
    ),
    (
        rf"{SUBJECT}be\s+(?:strictly\s+)?less than\s+"
        rf"{NUMBER_PATTERN}\b",
        "<",
    ),
]


def parse_number(value):
    value = str(value).strip().lower()

    if value in NUMBERS:
        return NUMBERS[value]

    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return None


def clean_column_hint(text):
    text = str(text).lower().strip()

    text = re.sub(
        r"\b(each|every|the|a|an)\b",
        " ",
        text,
    )

    text = re.sub(
        r"\bemail addresses?\b",
        "email",
        text,
    )

    text = re.sub(r"[^a-z0-9]+", "_", text)

    return re.sub(r"_+", "_", text).strip("_")


def split_clauses(text):
    text = str(text).strip()

    parts = re.split(
        r"\s*[,;]\s*and\s+"
        r"(?=(?:the|each|every|a|an)\s+)"
        r"|\s+and\s+"
        r"(?=(?:the|each|every|a|an)\s+"
        r".+?\s+(?:must|shall|should)\s+)",
        text,
        flags=re.IGNORECASE,
    )

    return [
        part.strip(" ,;.")
        for part in parts
        if part.strip(" ,;.")
    ]


def extract_requirement_constraints(requirements):
    results = []

    for requirement in requirements:
        original = str(requirement).strip()

        for clause in split_clauses(original):
            normalized = clause.lower().strip().rstrip(".")
            base = {"source_requirement": original}

            # UNIQUE
            match = re.search(
                rf"{SUBJECT}be\s+unique\b",
                normalized,
            )

            if match:
                results.append({
                    **base,
                    "type": "UNIQUE",
                    "column_hint": clean_column_hint(
                        match.group(1)
                    ),
                })

            # Numeric CHECK comparisons
            comparison_found = False

            for pattern, operator in COMPARISONS:
                match = re.search(pattern, normalized)

                if not match:
                    continue

                value = parse_number(match.group(2))

                if value is not None:
                    results.append({
                        **base,
                        "type": "CHECK",
                        "column_hint": clean_column_hint(
                            match.group(1)
                        ),
                        "operator": operator,
                        "value": value,
                    })

                    comparison_found = True

                break

            # Positive and nonnegative values
            if not comparison_found:
                special_patterns = [
                    (
                        rf"{SUBJECT}be\s+positive\b",
                        ">",
                    ),
                    (
                        rf"{SUBJECT}be\s+"
                        r"(?:nonnegative|non-negative)\b",
                        ">=",
                    ),
                    (
                        r"(.+?)\s+"
                        r"(?:cannot|must not|shall not)"
                        r"\s+be\s+negative\b",
                        ">=",
                    ),
                ]

                for pattern, operator in special_patterns:
                    match = re.search(pattern, normalized)

                    if match:
                        results.append({
                            **base,
                            "type": "CHECK",
                            "column_hint": clean_column_hint(
                                match.group(1)
                            ),
                            "operator": operator,
                            "value": 0,
                        })
                        break

            # NOT NULL
            match = re.search(
                rf"{SUBJECT}"
                r"(?:not be null|be required)\b",
                normalized,
            )

            if match:
                results.append({
                    **base,
                    "type": "NOT_NULL",
                    "column_hint": clean_column_hint(
                        match.group(1)
                    ),
                })

            # Allowed values
            match = re.search(
                rf"{SUBJECT}be\s+one of\s+(.+)",
                normalized,
            )

            if match:
                values = [
                    item.strip(" '\".")
                    for item in re.split(
                        r",|\bor\b",
                        match.group(2),
                    )
                    if item.strip(" '\".")
                ]

                if values:
                    results.append({
                        **base,
                        "type": "CHECK",
                        "column_hint": clean_column_hint(
                            match.group(1)
                        ),
                        "allowed_values": values,
                    })

    # Compatibility with older code that expects "column".
    for item in results:
        tokens = item["column_hint"].split("_")
        item["column"] = tokens[-1] if tokens else ""

    return results