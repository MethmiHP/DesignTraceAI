"""
DesignTrace AI - Requirement-to-Database Mapper
================================================

Maps requirements to database tables, columns,
foreign keys, and relationships.

Deterministic baseline.

Improvements:
1. Separates storage, interaction, and constraint requirements.
2. Avoids unrelated table and column mappings.
3. Excludes implicit primary keys.
4. Maps foreign keys and relationships using provenance.
5. Uses column-level evidence for attribute constraints.
6. Preserves the existing JSON output structure.
"""

import re

from shared.models.project import Requirement
from shared.models.database import DatabaseDesign


def _normalize(text: str) -> str:
    """Normalize text for basic matching."""
    return text.lower().replace("_", " ").strip()


def _mentions(text: str, name: str) -> bool:
    """Match singular and plural entity names."""

    normalized = _normalize(name)

    if normalized.endswith("ies"):
        singular = normalized[:-3] + "y"
        forms = [normalized, singular]

    elif normalized.endswith("s"):
        singular = normalized[:-1]
        forms = [normalized, singular]

    else:
        forms = [
            normalized,
            normalized + "s",
            normalized + "es",
        ]

    return any(
        re.search(
            rf"\b{re.escape(form)}\b",
            text,
        )
        for form in forms
    )

def _requirement_type(text: str) -> str:
    """
    Classify requirements into:
    storage, interaction, constraint, or general.
    """

    text = _normalize(text)

    constraint_keywords = (
        "must be unique",
        "should be unique",
        "must have",
        "must contain",
        "must not be null",
        "cannot be null",
        "required",
        "one of",
    )

    storage_keywords = (
        "store",
        "save",
        "record information",
        "manage information",
    )

    interaction_keywords = (
        "borrow",
        "borrowing",
        "book an appointment",
        "place an order",
        "create an order",
        "contains products",
        "containing products",
    )

    # Check constraints first.
    if any(
        keyword in text
        for keyword in constraint_keywords
    ):
        return "constraint"

    # Check storage before interactions.
    if any(
        keyword in text
        for keyword in storage_keywords
    ):
        return "storage"

    # Match specific interaction phrases.
    if any(
        keyword in text
        for keyword in interaction_keywords
    ):
        return "interaction"

    return "general"



def generate_requirement_mappings(
    design: DatabaseDesign,
    requirements: list[Requirement],
) -> dict:
    """
    Generate requirement-to-database mappings.
    """

    mappings = []

    for requirement in requirements:

        if not requirement.database_relevant:
            continue

        requirement_id = requirement.requirement_id

        text = _normalize(
            requirement.requirement_text
        )

        req_type = _requirement_type(text)

        database_elements = set()

        # Step 1: Map tables and columns.
        for table in design.tables:

            table_is_source = (
                requirement_id
                in table.source_requirement_ids
            )

            table_is_mentioned = _mentions(
                text,
                table.table_name,
            )

            table_context = (
                table_is_source or table_is_mentioned
            )

            if not table_context:
                continue

            # Table-level links are suitable for
            # storage requirements.
            if table_is_source and req_type in {
                "storage",
                "general",
            }:
                database_elements.add(
                    table.table_name
                )

            # For interactions, the participating
            # child table may be relevant.
            if (
                req_type == "interaction"
                and table_is_source
            ):
                # Prefer relationship evidence below.
                pass

            for column in table.columns:

                column_is_source = (
                    requirement_id
                    in column.source_requirement_ids
                )

                column_is_mentioned = _mentions(
                    text,
                    column.name,
                )

                # Implicit primary keys are excluded.
                # Explicitly mentioned PKs can be mapped.
                if column.primary_key:
                    if column_is_mentioned:
                        database_elements.add(
                            f"{table.table_name}.{column.name}"
                        )
                    continue

                # Foreign keys for interaction requirements
                # are handled using relationship evidence.
                if column.foreign_key is not None:
                    if (
                        column_is_source
                        and req_type != "constraint"
                    ):
                        database_elements.add(
                            f"{table.table_name}.{column.name}"
                        )
                    continue

                # Column provenance is stronger than
                # simple text matching.
                if column_is_source:
                    database_elements.add(
                        f"{table.table_name}.{column.name}"
                    )

                elif column_is_mentioned:
                    database_elements.add(
                        f"{table.table_name}.{column.name}"
                    )

        # Step 2: Map relationships.
        for relationship in design.relationships:

            relationship_is_source = (
                requirement_id
                in relationship.source_requirement_ids
            )

            if (
                req_type == "interaction"
                and relationship_is_source
            ):
                database_elements.add(
                    f"relationship:{relationship.relationship_id}"
                )

                database_elements.add(
                    relationship.foreign_key
                )

                database_elements.add(
                    relationship.to_table
                )

        # Step 3: Store mapping.
        mappings.append(
            {
                "requirement_id": requirement_id,
                "database_elements": sorted(
                    database_elements
                ),
                "mapped": bool(database_elements),
            }
        )

    return {
        "requirement_mappings": mappings,
    }
