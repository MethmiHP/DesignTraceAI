import re

from modules.database_design.nlp.label_schema import ExtractedConcepts


ENTITY_TERMS = {
    "student", "course", "enrollment",
    "patient", "doctor", "appointment",
    "book", "member", "borrowing",
    "customer", "product", "order",
}

ATTRIBUTE_TERMS = {
    "name", "email", "phone", "status",
    "title", "isbn", "publication date",
    "price", "quantity", "code", "credits",
    "specialization",
}

ACTION_TERMS = {
    "enroll", "register", "borrow",
    "book", "cancel", "place",
    "create", "update", "store",
}


def _find_terms(text: str, terms: set[str]) -> list[str]:
    matches = []

    for term in sorted(terms):
        pattern = rf"\b{re.escape(term)}(?:s|es)?\b"

        if re.search(pattern, text, re.IGNORECASE):
            matches.append(term)

    return matches


def extract_concepts(requirement_text: str) -> ExtractedConcepts:
    return ExtractedConcepts(
        entities=_find_terms(requirement_text, ENTITY_TERMS),
        attributes=_find_terms(requirement_text, ATTRIBUTE_TERMS),
        actions=_find_terms(requirement_text, ACTION_TERMS),
    )
