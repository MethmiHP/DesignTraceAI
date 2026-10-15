"""
Apply mapped constraints to the standard DatabaseDesign model.

Only confidently mapped constraints are applied.
"""

from shared.models.database import DatabaseDesign


def apply_requirement_constraints(
    design: DatabaseDesign,
    mapped_constraints: list[dict],
) -> DatabaseDesign:

    for rule in mapped_constraints:

        if rule.get("status") != "MAPPED":
            continue

        table_name = rule.get("table")
        column_name = rule.get("column")

        table = next(
            (
                table
                for table in design.tables
                if table.table_name == table_name
            ),
            None,
        )

        if table is None:
            continue

        column = next(
            (
                column
                for column in table.columns
                if column.name == column_name
            ),
            None,
        )

        if column is None:
            continue

        constraint_type = rule.get("type")

        if constraint_type == "UNIQUE":
            column.unique = True

        elif constraint_type == "NOT_NULL":
            column.nullable = False

        elif constraint_type == "CHECK":
            # CHECK rules are passed to the SQL generator
            # as structured constraints.
            #
            # Do not store raw, unvalidated SQL expressions
            # in the design model.
            pass

    return design