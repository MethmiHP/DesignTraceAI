"""
DesignTrace AI - Database Concept Extractor
============================================

Purpose:
    Extract candidate database concepts from
    natural-language software requirements.

Current Stage:
    Rule-based NLP baseline.

Later:
    Compare this baseline with BERT,
    RoBERTa, and DeBERTa models.
"""

import re

from pydantic import BaseModel, Field

from shared.models.project import Requirement


class ExtractedConcepts(BaseModel):
    """Stores concepts extracted from one requirement."""

    requirement_id: str
    entities: list[str] = Field(default_factory=list)
    attributes: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


# Initial vocabulary for testing.
# This will later be replaced or extended
# using trained NLP models.

ENTITY_TERMS = {
    "patient",
    "doctor",
    "appointment",
    "hospital",
    "user",
    "admin",
    "student",
    "course",
    "teacher",
    "order",
    "product",
    "customer",
    "payment",
    "booking",
    "book",
    "member",
    "borrowing",
}

ATTRIBUTE_TERMS = {
    "name",
    "email",
    "password",
    "phone",
    "address",
    "date",
    "time",
    "status",
    "price",
    "quantity",
    "specialization",
    "age",
    "title",
    "isbn",
    "publication_date",
}

ACTION_TERMS = {
    "register",
    "book",
    "borrow",
    "cancel",
    "update",
    "delete",
    "create",
    "view",
    "manage",
    "schedule",
    "pay",
    "assign",
    "store",
}


def extract_database_concepts(
    requirement: Requirement,
) -> ExtractedConcepts:
    """
    Extract entities, attributes, and actions
    from one software requirement.
    """

    text = requirement.requirement_text.lower()

    # Normalize common multi-word database attributes.
    text = re.sub(
        r"\bpublication\s+date\b",
        "publication_date",
        text,
    )

    # Extract words using simple tokenization.
    words = re.findall(r"[a-z_]+", text)

    entities = set()
    attributes = set()
    actions = set()

    for word in words:

        # Basic plural handling.
        normalized = word

        if word.endswith("ies") and len(word) > 3:
            normalized = word[:-3] + "y"
        elif word.endswith("s") and len(word) > 3:
            normalized = word[:-1]

        # Handle "book" as an action when followed by an appointment.
        if (
            normalized == "book"
            and re.search(r"\bbook\s+(?:an?\s+)?appointment\b", text)
        ):
            actions.add("book")
            continue

        # Match entities.
        if normalized in ENTITY_TERMS:
            entities.add(normalized)

        # Match attributes.
        if normalized in ATTRIBUTE_TERMS:
            attributes.add(normalized)

        # Match actions.
        if normalized in ACTION_TERMS:
            actions.add(normalized)

    return ExtractedConcepts(
        requirement_id=requirement.requirement_id,
        entities=sorted(entities),
        attributes=sorted(attributes),
        actions=sorted(actions),
    )


def extract_project_concepts(
    requirements: list[Requirement],
) -> list[ExtractedConcepts]:
    """
    Extract concepts from database-relevant
    requirements only.
    """

    results = []

    for requirement in requirements:

        if not requirement.database_relevant:
            continue

        concepts = extract_database_concepts(requirement)
        results.append(concepts)

    return results
