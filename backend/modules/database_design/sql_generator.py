"""
Generate PostgreSQL SQL schema suggestions
from a structured DatabaseDesign.
"""

import re

from shared.models.database import DatabaseDesign


def quote_identifier(name: str) -> str:
    """Safely quote a PostgreSQL identifier."""
    if not name or "\x00" in name:
        raise ValueError("Invalid SQL identifier")
    return '"' + name.replace('"', '""') + '"'


def validate_sql_type(data_type: str) -> str:
    """Allow common relational SQL data types."""
    sql_type = data_type.strip().upper()

    allowed = re.fullmatch(
        r"(BIGINT|INTEGER|INT|SMALLINT|BOOLEAN|DATE|"
        r"TIMESTAMP|TEXT|UUID|"
        r"VARCHAR\(\d+\)|CHAR\(\d+\)|"
        r"DECIMAL\(\d+,\s*\d+\)|NUMERIC\(\d+,\s*\d+\))",
        sql_type,
    )

    if not allowed:
        raise ValueError(
            f"Unsupported SQL data type: {data_type}"
        )

    return sql_type


def generate_sql_schema(design: DatabaseDesign) -> str:
    """Generate PostgreSQL CREATE TABLE statements."""

    statements = []
    foreign_keys = []

    for table in design.tables:
        table_name = quote_identifier(table.table_name)
        definitions = []
        primary_keys = []

        for column in table.columns:
            column_name = quote_identifier(column.name)
            data_type = validate_sql_type(column.data_type)

            parts = [column_name, data_type]

            if not column.nullable:
                parts.append("NOT NULL")

            if column.unique and not column.primary_key:
                parts.append("UNIQUE")

            definitions.append(" ".join(parts))

            if column.primary_key:
                primary_keys.append(column_name)

            if column.foreign_key is not None:
                reference = column.foreign_key

                foreign_keys.append(
                    (
                        table.table_name,
                        column.name,
                        reference.table,
                        reference.column,
                    )
                )

        if primary_keys:
            definitions.append(
                f"PRIMARY KEY ({', '.join(primary_keys)})"
            )

        body = ",\n    ".join(definitions)

        statements.append(
            f"CREATE TABLE {table_name} (\n"
            f"    {body}\n"
            f");"
        )

    # Add foreign keys after all tables have been created.
    for table_name, column_name, ref_table, ref_column in foreign_keys:
        statements.append(
            f"ALTER TABLE {quote_identifier(table_name)} "
            f"ADD FOREIGN KEY ({quote_identifier(column_name)}) "
            f"REFERENCES {quote_identifier(ref_table)} "
            f"({quote_identifier(ref_column)});"
        )

    return "\n\n".join(statements)
