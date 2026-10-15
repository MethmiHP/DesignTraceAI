"""
DesignTrace AI - Baseline Relationship Generator
================================================

Creates known foreign keys and relationships.

Improvement:
Uses requirement text to identify relationship
provenance instead of relying only on shared
table source IDs.

Current implementation: Deterministic baseline.
"""

import re

from shared.models.project import Requirement
from shared.models.database import (
    DatabaseColumn,
    DatabaseRelationship,
    DatabaseDesign,
    ForeignKeyReference,
)


KNOWN_RELATIONSHIPS = [
    ("patients", "appointments", "patient_id"),
    ("doctors", "appointments", "doctor_id"),
    ("members", "borrowings", "member_id"),
    ("books", "borrowings", "book_id"),
    ("customers", "orders", "customer_id"),
    ("products", "orders", "product_id"),
]


# Baseline action vocabulary for sample projects.
RELATIONSHIP_ACTIONS = {
    "book",
    "books",
    "borrow",
    "borrows",
    "place",
    "places",
    "contain",
    "contains",
}


def _singular(name: str) -> str:
    """Convert basic plural table names to singular."""

    if name.endswith("ies"):
        return name[:-3] + "y"

    if name.endswith("s"):
        return name[:-1]

    return name


def _mentions_entity(text: str, table_name: str) -> bool:
    """Check whether text mentions a table's entity."""

    singular = _singular(table_name)

    return bool(
        re.search(
            rf"\b{re.escape(singular)}(?:s|es)?\b",
            text,
        )
        or re.search(
            rf"\b{re.escape(table_name)}\b",
            text,
        )
    )


def _has_relationship_action(text: str) -> bool:
    """Detect a supported relationship action."""

    return any(
        re.search(rf"\b{re.escape(action)}\b", text)
        for action in RELATIONSHIP_ACTIONS
    )


def _relationship_requirement_ids(
    requirements: list[Requirement],
    parent_name: str,
    child_name: str,
    table_names: set[str],
) -> list[str]:
    """
    Identify requirements describing a relationship.

    Supports requirements that directly mention the
    child table or describe an action connecting two
    parent entities.

    This remains a baseline heuristic.
    """

    source_ids = set()

    for requirement in requirements:

        if not requirement.database_relevant:
            continue

        text = requirement.requirement_text.lower()

        parent_mentioned = _mentions_entity(
            text, parent_name
        )

        child_mentioned = _mentions_entity(
            text, child_name
        )

        if not parent_mentioned:
            continue

        # Direct evidence: both relationship tables
        # appear in the requirement.
        if child_mentioned and _has_relationship_action(text):
            source_ids.add(requirement.requirement_id)
            continue

        # Indirect evidence:
        # A relationship action joins two parent entities,
        # while the child is a transaction table.
        other_entity_mentioned = any(
            _mentions_entity(text, table_name)
            for table_name in table_names
            if table_name not in {
                parent_name,
                child_name,
            }
        )

        if (
            other_entity_mentioned
            and _has_relationship_action(text)
        ):
            source_ids.add(requirement.requirement_id)

    return sorted(source_ids)


def add_database_relationships(
    design: DatabaseDesign,
    requirements: list[Requirement] | None = None,
) -> DatabaseDesign:
    """
    Add known one-to-many relationships and record
    supporting requirement IDs.
    """

    design = design.model_copy(deep=True)

    table_map = {
        table.table_name: table
        for table in design.tables
    }

    table_names = set(table_map)

    for parent_name, child_name, fk_name in KNOWN_RELATIONSHIPS:

        if (
            parent_name not in table_map
            or child_name not in table_map
        ):
            continue

        parent = table_map[parent_name]
        child = table_map[child_name]

        parent_pk = next(
            (
                column
                for column in parent.columns
                if column.primary_key
            ),
            None,
        )

        if parent_pk is None:
            continue

        if requirements is not None:
            relationship_source_ids = (
                _relationship_requirement_ids(
                    requirements,
                    parent_name,
                    child_name,
                    table_names,
                )
            )
        else:
            # Backward compatibility with existing callers.
            relationship_source_ids = sorted(
                set(parent.source_requirement_ids)
                & set(child.source_requirement_ids)
            )

        existing_column = next(
            (
                column
                for column in child.columns
                if column.name == fk_name
            ),
            None,
        )

        if existing_column is None:
            child.columns.append(
                DatabaseColumn(
                    name=fk_name,
                    data_type=parent_pk.data_type,
                    nullable=False,
                    foreign_key=ForeignKeyReference(
                        table=parent_name,
                        column=parent_pk.name,
                    ),
                    source_requirement_ids=relationship_source_ids,
                )
            )
        else:
            if existing_column.foreign_key is None:
                existing_column.foreign_key = (
                    ForeignKeyReference(
                        table=parent_name,
                        column=parent_pk.name,
                    )
                )

            existing_column.source_requirement_ids = sorted(
                set(existing_column.source_requirement_ids)
                | set(relationship_source_ids)
            )

        existing_relationship = next(
            (
                relationship
                for relationship in design.relationships
                if relationship.from_table == parent_name
                and relationship.to_table == child_name
            ),
            None,
        )

        if existing_relationship is None:
            design.relationships.append(
                DatabaseRelationship(
                    relationship_id=(
                        f"REL-{len(design.relationships) + 1:02d}"
                    ),
                    from_table=parent_name,
                    to_table=child_name,
                    relationship_type="one-to-many",
                    foreign_key=f"{child_name}.{fk_name}",
                    source_requirement_ids=relationship_source_ids,
                )
            )
        else:
            existing_relationship.source_requirement_ids = sorted(
                set(existing_relationship.source_requirement_ids)
                | set(relationship_source_ids)
            )

    return design
