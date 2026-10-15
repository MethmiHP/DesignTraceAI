"""
Deterministic validation rules:
"""
import re

from shared.models.database import DatabaseDesign


def validate_database_design(
    design: DatabaseDesign,
) -> dict:
    """
    Validate a relational database design.

    Returns a structured validation report.
    """

    results = []

        # DB-R05: Empty Database Design Validation.
    if not design.tables:
        results.append({
            "rule_id": "DB-R07",
            "status": "FAIL",
            "message": (
                "Database design contains no tables."
            ),
        })
    else:
        results.append({
            "rule_id": "DB-R07",
            "status": "PASS",
            "message": (
                "Database design contains at least one table."
            ),
        })

    # Create lookup for existing tables.
    table_lookup = {
        table.table_name: table
        for table in design.tables
    }

    # DB-R01: Primary Key Validation.
    for table in design.tables:

        primary_keys = [
            column
            for column in table.columns
            if column.primary_key
        ]

        if primary_keys:
            results.append({
                "rule_id": "DB-R01",
                "table": table.table_name,
                "status": "PASS",
                "message": (
                    f"Table '{table.table_name}' "
                    "has a primary key."
                ),
            })
        else:
            results.append({
                "rule_id": "DB-R01",
                "table": table.table_name,
                "status": "FAIL",
                "message": (
                    f"Table '{table.table_name}' "
                    "does not have a primary key."
                ),
            })

    # DB-R02: Foreign Key Validation.
    for table in design.tables:

        for column in table.columns:

            if column.foreign_key is None:
                continue

            referenced_table_name = (
                column.foreign_key.table
            )

            referenced_column_name = (
                column.foreign_key.column
            )

            referenced_table = table_lookup.get(
                referenced_table_name
            )

            if referenced_table is None:
                results.append({
                    "rule_id": "DB-R02",
                    "table": table.table_name,
                    "column": column.name,
                    "status": "FAIL",
                    "message": (
                        f"Foreign key '{column.name}' "
                        f"references missing table "
                        f"'{referenced_table_name}'."
                    ),
                })
                continue

            referenced_column = next(
                (
                    candidate
                    for candidate in referenced_table.columns
                    if candidate.name == referenced_column_name
                ),
                None,
            )

            if referenced_column is None:
                results.append({
                    "rule_id": "DB-R02",
                    "table": table.table_name,
                    "column": column.name,
                    "status": "FAIL",
                    "message": (
                        f"Foreign key '{column.name}' "
                        f"references missing column "
                        f"'{referenced_table_name}."
                        f"{referenced_column_name}'."
                    ),
                })
                continue

            results.append({
                "rule_id": "DB-R02",
                "table": table.table_name,
                "column": column.name,
                "status": "PASS",
                "message": (
                    f"Foreign key '{column.name}' "
                    f"correctly references "
                    f"'{referenced_table_name}."
                    f"{referenced_column_name}'."
                ),
            })

    
    # DB-R03: Relationship Validation.
    valid_relationship_types = {
        "one-to-one",
        "one-to-many",
        "many-to-many",
    }

    for relationship in design.relationships:

        errors = []

        # Check source table exists.
        if relationship.from_table not in table_lookup:
            errors.append(
                f"Source table '{relationship.from_table}' "
                "does not exist."
            )

        # Check target table exists.
        if relationship.to_table not in table_lookup:
            errors.append(
                f"Target table '{relationship.to_table}' "
                "does not exist."
            )

        # Check relationship type.
        if (
            relationship.relationship_type
            not in valid_relationship_types
        ):
            errors.append(
                f"Unsupported relationship type "
                f"'{relationship.relationship_type}'."
            )

        if errors:
            results.append({
                "rule_id": "DB-R03",
                "relationship_id": relationship.relationship_id,
                "status": "FAIL",
                "message": " ".join(errors),
            })
        else:
            results.append({
                "rule_id": "DB-R03",
                "relationship_id": relationship.relationship_id,
                "status": "PASS",
                "message": (
                    f"Relationship '{relationship.relationship_id}' "
                    "references valid tables and has a "
                    "supported relationship type."
                ),
            })

    
    # DB-R04: Data Type Validation.
    # Supported types for the current relational prototype.
    supported_types = {
        "BIGINT",
        "INTEGER",
        "INT",
        "SMALLINT",
        "BOOLEAN",
        "DATE",
        "TIME",
        "TIMESTAMP",
        "TEXT",
        "FLOAT",
        "DOUBLE",
    }

    for table in design.tables:
        for column in table.columns:

            data_type = column.data_type.strip().upper()

            valid = (
                data_type in supported_types
                or bool(
                    re.fullmatch(
                        r"VARCHAR\([1-9][0-9]*\)",
                        data_type,
                    )
                )
                or bool(
                    re.fullmatch(
                        r"DECIMAL\([1-9][0-9]*,[0-9]+\)",
                        data_type,
                    )
                )
            )

            if valid:
                results.append({
                    "rule_id": "DB-R04",
                    "table": table.table_name,
                    "column": column.name,
                    "status": "PASS",
                    "message": (
                        f"Valid data type '{data_type}'."
                    ),
                })
            else:
                results.append({
                    "rule_id": "DB-R04",
                    "table": table.table_name,
                    "column": column.name,
                    "status": "FAIL",
                    "message": (
                        f"Unsupported data type '{data_type}'."
                    ),
                })

    
    # DB-R05: Database Constraint Validation.
    # Check primary key nullability and supported CHECK constraints.

    for table in design.tables:
        for column in table.columns:

            # Primary key columns cannot contain NULL.
            if column.primary_key:
                valid = not column.nullable

                results.append({
                    "rule_id": "DB-R05",
                    "table": table.table_name,
                    "column": column.name,
                    "status": "PASS" if valid else "FAIL",
                    "message": (
                        f"Primary key '{column.name}' is NOT NULL."
                        if valid
                        else f"Primary key '{column.name}' allows NULL."
                    ),
                })

    # Supported CHECK format:
    # CHECK (status IN ('pending', 'confirmed'))
    check_pattern = re.compile(
        r"CHECK\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)"
        r"\s+IN\s*\(\s*"
        r"'[^']+'(?:\s*,\s*'[^']+')*"
        r"\s*\)\s*\)",
        re.IGNORECASE,
    )

    for constraint in design.constraints:

        match = check_pattern.fullmatch(constraint.strip())

        if match is None:
            results.append({
                "rule_id": "DB-R05",
                "status": "FAIL",
                "message": (
                    f"Unsupported CHECK constraint: {constraint}"
                ),
            })
            continue

        column_name = match.group(1)

        matching_tables = [
            table.table_name
            for table in design.tables
            if any(
                column.name == column_name
                for column in table.columns
            )
        ]

        if len(matching_tables) == 1:
            results.append({
                "rule_id": "DB-R05",
                "table": matching_tables[0],
                "column": column_name,
                "status": "PASS",
                "message": (
                    f"CHECK constraint references "
                    f"existing column '{column_name}'."
                ),
            })
        else:
            results.append({
                "rule_id": "DB-R05",
                "column": column_name,
                "status": "FAIL",
                "message": (
                    f"CHECK constraint column '{column_name}' "
                    "is missing or ambiguous."
                ),
            })



    # Calculate report totals.
    failed_checks = sum(
        result["status"] == "FAIL"
        for result in results
    )

    passed_checks = sum(
        result["status"] == "PASS"
        for result in results
    )

    return {
        "status": (
            "FAIL" if failed_checks else "PASS"
        ),
        "total_checks": len(results),
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "results": results,
    }
