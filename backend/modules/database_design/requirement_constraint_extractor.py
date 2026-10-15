"""
Extract explicit database constraints from natural-language
requirements and architecture constraints.

Project-independent: no hardcoded table names.
"""

import re

NUMBERS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "sixteen": 16,
    "eighteen": 18,
}


def parse_number(value):
    value = str(value).strip().lower()

    if value in NUMBERS:
        return NUMBERS[value]

    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return None


def clean_column_hint(text):
    text = text.lower().strip()

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

    text = re.sub(r"\s+", "_", text.strip())
    return text


def extract_requirement_constraints(requirements):
    """
    Input:
        List of requirement/constraint strings.

    Output:
        List of structured constraint dictionaries.
    """

    results = []

    number_pattern = (
        r"(-?\d+(?:\.\d+)?|zero|one|two|three|"
        r"sixteen|eighteen)"
    )

    comparison_patterns = [
        (
            rf"(.+?)\s+(?:must|shall|should)\s+be\s+"
            rf"(?:strictly\s+)?greater than\s+{number_pattern}",
            ">",
        ),
        (
            rf"(.+?)\s+(?:must|shall|should)\s+be\s+"
            rf"(?:greater than or equal to|at least)\s+"
            rf"{number_pattern}",
            ">=",
        ),
        (
            rf"(.+?)\s+(?:must|shall|should)\s+be\s+"
            rf"less than\s+{number_pattern}",
            "<",
        ),
        (
            rf"(.+?)\s+(?:must|shall|should)\s+be\s+"
            rf"(?:at most|less than or equal to)\s+"
            rf"{number_pattern}",
            "<=",
        ),
    ]

    for requirement in requirements:
        text = str(requirement).strip()
        normalized = text.lower().rstrip(". ")

        # UNIQUE
        unique_match = re.search(
            r"(.+?)\s+(?:must|shall|should)\s+be\s+unique\b",
            normalized,
        )

        if unique_match:
            results.append({
                "type": "UNIQUE",
                "column_hint": clean_column_hint(
                    unique_match.group(1)
                ),
                "source_requirement": text,
            })

        # Numeric comparisons
        comparison_found = False

        for pattern, operator in comparison_patterns:
            match = re.search(pattern, normalized)

            if not match:
                continue

            value = parse_number(match.group(2))

            if value is not None:
                results.append({
                    "type": "CHECK",
                    "column_hint": clean_column_hint(
                        match.group(1)
                    ),
                    "operator": operator,
                    "value": value,
                    "source_requirement": text,
                })

            comparison_found = True
            break

        # Positive / nonnegative / cannot be negative
        if not comparison_found:
            special_patterns = [
                (
                    r"(.+?)\s+(?:must|shall|should)\s+be\s+positive\b",
                    ">",
                ),
                (
                    r"(.+?)\s+(?:must|shall|should)\s+be\s+"
                    r"(?:nonnegative|non-negative)\b",
                    ">=",
                ),
                (
                    r"(.+?)\s+(?:cannot|must not|shall not)\s+"
                    r"be\s+negative\b",
                    ">=",
                ),
            ]

            for pattern, operator in special_patterns:
                match = re.search(pattern, normalized)

                if match:
                    results.append({
                        "type": "CHECK",
                        "column_hint": clean_column_hint(
                            match.group(1)
                        ),
                        "operator": operator,
                        "value": 0,
                        "source_requirement": text,
                    })
                    break

        # NOT NULL
        not_null_match = re.search(
            r"(.+?)\s+(?:must|shall|should)\s+"
            r"(?:not be null|be required)\b",
            normalized,
        )

        if not_null_match:
            results.append({
                "type": "NOT_NULL",
                "column_hint": clean_column_hint(
                    not_null_match.group(1)
                ),
                "source_requirement": text,
            })

        # Allowed values
        allowed_match = re.search(
            r"(.+?)\s+(?:must|shall|should)\s+"
            r"be one of\s+(.+)",
            normalized,
        )

        if allowed_match:
            values = [
                item.strip(" '\".")
                for item in re.split(
                    r",|\bor\b",
                    allowed_match.group(2),
                )
                if item.strip(" '\".")
            ]

            if values:
                results.append({
                    "type": "CHECK",
                    "column_hint": clean_column_hint(
                        allowed_match.group(1)
                    ),
                    "allowed_values": values,
                    "source_requirement": text,
                })

    return results