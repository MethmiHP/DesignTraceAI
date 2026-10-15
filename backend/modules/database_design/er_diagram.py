"""
Generate Mermaid ER diagram code from a DatabaseDesign object.
"""

import re

from shared.models.database import DatabaseDesign


def _safe_name(value: str) -> str:
    """Convert names to Mermaid-safe identifiers."""
    name = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not name or name[0].isdigit():
        name = "_" + name
    return name


def _safe_type(value: str) -> str:
    """Convert SQL data types to Mermaid-compatible types."""
    return _safe_name(value)


def generate_er_diagram(design: DatabaseDesign) -> str:
    """Return Mermaid ER diagram text."""

    lines = ["erDiagram"]

    # Generate entities and attributes.
    for table in design.tables:
        table_name = _safe_name(table.table_name)

        lines.append(f"    {table_name} {{")

        for column in table.columns:
            data_type = _safe_type(column.data_type)
            column_name = _safe_name(column.name)

            keys = []

            if column.primary_key:
                keys.append("PK")

            if column.foreign_key is not None:
                keys.append("FK")

            key_text = f" {','.join(keys)}" if keys else ""

            lines.append(
                f"        {data_type} {column_name}{key_text}"
            )

        lines.append("    }")

    # Generate relationships using the existing schema.
    for relationship in design.relationships:
        from_table = _safe_name(relationship.from_table)
        to_table = _safe_name(relationship.to_table)

        relationship_type = relationship.relationship_type.lower()

        if relationship_type == "one-to-many":
            connector = "||--o{"
        elif relationship_type == "one-to-one":
            connector = "||--o|"
        elif relationship_type == "many-to-many":
            connector = "}o--o{"
        else:
            connector = "||--o{"

        label = relationship.relationship_id.replace('"', "'")

        lines.append(
            f'    {from_table} {connector} {to_table} : "{label}"'
        )

    return "\n".join(lines)
