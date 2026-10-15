"""
DesignTrace AI - Artifact Adapter

Converts the standard DatabaseDesign model into
the dictionary format expected by artifact_generator.py.
"""

from shared.models.database import DatabaseDesign


def convert_design_for_artifacts(
    design: DatabaseDesign,
) -> dict:
    """
    Convert standard DatabaseDesign into the
    existing artifact generator format.
    """

    tables = []

    for table in design.tables:
        columns = []
        foreign_keys = []

        for column in table.columns:
            columns.append(
                {
                    "name": column.name,
                    "data_type": column.data_type,
                    "nullable": column.nullable,
                    "primary_key": column.primary_key,
                    "unique": column.unique,
                }
            )

            if column.foreign_key is not None:
                foreign_keys.append(
                    {
                        "column": column.name,
                        "references_table": (
                            column.foreign_key.table
                        ),
                        "references_column": (
                            column.foreign_key.column
                        ),
                    }
                )

        tables.append(
            {
                "name": table.table_name,
                "columns": columns,
                "foreign_keys": foreign_keys,
            }
        )

    return {
        "tables": tables,
        "relationships": [
            {
                "from_table": relationship.from_table,
                "to_table": relationship.to_table,
                "cardinality": (
                    relationship.relationship_type
                ),
            }
            for relationship in design.relationships
        ],
        "constraints": design.constraints,
    }
