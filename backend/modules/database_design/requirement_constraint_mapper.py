"""
DesignTrace AI - Requirement Constraint Mapper

Maps extracted requirement constraints to
existing database tables and columns.
"""

from shared.models.database import DatabaseDesign


def map_requirement_constraints(
    design: DatabaseDesign,
    constraints: list[dict],
) -> list[dict]:
    """
    Find the database table and column for each constraint.

    Only map when exactly one matching column exists.
    Unmatched or ambiguous constraints are not applied.
    """

    mapped = []

    for constraint in constraints:
        column_name = constraint["column"]

        matches = []

        for table in design.tables:
            for column in table.columns:
                if column.name == column_name:
                    matches.append(table.table_name)

        if len(matches) == 1:
            mapped.append({
                **constraint,
                "table": matches[0],
                "status": "MAPPED",
            })
        else:
            mapped.append({
                **constraint,
                "table": None,
                "status": (
                    "UNMAPPED"
                    if not matches
                    else "AMBIGUOUS"
                ),
            })

    return mapped
