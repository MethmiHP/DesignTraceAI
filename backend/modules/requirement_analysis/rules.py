# Applies rule-based quality checks to requirement text by detecting ambiguous terms,
# placeholder expressions, and weak quantifiers that may indicate ambiguity or incompleteness
import re

AMBIGUOUS_TERMS = [
    "fast",
    "quick",
    "quickly",
    "easy",
    "easily",
    "user friendly",
    "user-friendly",
    "efficient",
    "efficiently",
    "secure",
    "high performance",
    "soon",
    "appropriate",
    "reasonable",
    "sufficient",
    "several",
    "many",
    "some",
    "normally",
    "usually",
    "etc"
]


PLACEHOLDER_TERMS = [
    "tbd",
    "tba",
    "to be decided",
    "to be determined",
    "to be confirmed"
]


def detect_ambiguous_terms(text: str) -> list[str]:

    found = []

    lower_text = text.lower()

    for term in AMBIGUOUS_TERMS:
        if term in lower_text:
            found.append(term)

    return list(set(found))


def detect_placeholders(text: str) -> list[str]:

    found = []

    lower_text = text.lower()

    for term in PLACEHOLDER_TERMS:
        if term in lower_text:
            found.append(term)

    return list(set(found))


def detect_weak_quantifiers(text: str) -> list[str]:

    patterns = [
        r"\bmany\b",
        r"\bsome\b",
        r"\bseveral\b",
        r"\bfew\b",
        r"\boften\b",
        r"\busually\b"
    ]

    found = []

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            found.append(match.group())

    return found


def run_quality_rules(text: str) -> dict:

    ambiguous_terms = detect_ambiguous_terms(text)

    placeholders = detect_placeholders(text)

    weak_quantifiers = detect_weak_quantifiers(text)

    ambiguous = bool(
        ambiguous_terms
        or weak_quantifiers
    )

    incomplete = bool(placeholders)

    return {
        "ambiguous": ambiguous,
        "incomplete": incomplete,
        "ambiguous_terms": ambiguous_terms,
        "placeholders": placeholders,
        "weak_quantifiers": weak_quantifiers
    }