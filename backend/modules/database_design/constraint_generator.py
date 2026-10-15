"""
DesignTrace AI - Database Constraint Generator

Adds basic relational database constraints
to an existing database design.
"""

from shared.models.database import DatabaseDesign


def generate_database_constraints(
    design: DatabaseDesign,
) -> DatabaseDesign:
    """
    Add supported database constraints.
    Avoid adding duplicate constraints.
    """

    for table in design.tables:
        for column in table.columns:

            # Primary keys cannot contain NULL.
            if column.primary_key:
                column.nullable = False

            # Foreign keys should reference valid tables.
            if column.foreign_key is not None:
                referenced_table = column.foreign_key.table

                table_exists = any(
                    t.table_name == referenced_table
                    for t in design.tables
                )

                if not table_exists:
                    raise ValueError(
                        f"Invalid foreign key: "
                        f"{table.table_name}.{column.name} "
                        f"references missing table "
                        f"{referenced_table}"
                    )

            # Email uniqueness rule.
            if column.name == "email":
                column.unique = True

    return design
