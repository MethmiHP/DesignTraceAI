from collections import Counter


def validate_database_design(design):
    errors = []
    warnings = []

    tables = design.get("tables", [])

    if not tables:
        errors.append("Database design contains no tables.")

    table_names = [table["name"] for table in tables]
    table_lookup = {
        table["name"]: table for table in tables
    }

    # 1. Check duplicate table names
    for name, count in Counter(table_names).items():
        if count > 1:
            errors.append(f"Duplicate table: {name}")

    # 2. Validate tables and columns
    for table in tables:
        table_name = table["name"]
        columns = table.get("columns", [])

        if not columns:
            errors.append(
                f"Table '{table_name}' has no columns."
            )
            continue

        column_names = [
            column["name"] for column in columns
        ]

        for name, count in Counter(column_names).items():
            if count > 1:
                errors.append(
                    f"Duplicate column '{name}' "
                    f"in table '{table_name}'."
                )

        # Check primary key
        primary_keys = [
            column for column in columns
            if column.get("primary_key", False)
        ]

        if not primary_keys:
            errors.append(
                f"Table '{table_name}' has no primary key."
            )

        for column in primary_keys:
            if column.get("nullable", True):
                errors.append(
                    f"Primary key '{table_name}."
                    f"{column['name']}' cannot be nullable."
                )

        # 3. Validate foreign keys
        for fk in table.get("foreign_keys", []):
            fk_column = fk["column"]
            ref_table = fk["references_table"]
            ref_column = fk["references_column"]

            if fk_column not in column_names:
                errors.append(
                    f"Foreign key column '{table_name}."
                    f"{fk_column}' does not exist."
                )

            if ref_table not in table_lookup:
                errors.append(
                    f"Referenced table '{ref_table}' "
                    f"does not exist."
                )
                continue

            ref_columns = [
                col["name"]
                for col in table_lookup[ref_table]["columns"]
            ]

            if ref_column not in ref_columns:
                errors.append(
                    f"Referenced column '{ref_table}."
                    f"{ref_column}' does not exist."
                )

    # 4. Validate relationships
    for relationship in design.get(
        "relationships", []
    ):
        from_table = relationship["from_table"]
        to_table = relationship["to_table"]

        if from_table not in table_lookup:
            errors.append(
                f"Relationship references unknown "
                f"table '{from_table}'."
            )

        if to_table not in table_lookup:
            errors.append(
                f"Relationship references unknown "
                f"table '{to_table}'."
            )

    # 5. Check requirement mappings
    for mapping in design.get(
        "requirement_mapping", []
    ):
        requirement_id = mapping["requirement_id"]

        for table_name in mapping.get(
            "related_tables", []
        ):
            if table_name not in table_lookup:
                errors.append(
                    f"Requirement '{requirement_id}' "
                    f"maps to unknown table '{table_name}'."
                )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "statistics": {
            "total_tables": len(tables),
            "total_relationships": len(
                design.get("relationships", [])
            ),
            "total_requirement_mappings": len(
                design.get("requirement_mapping", [])
            ),
            "total_errors": len(errors),
            "total_warnings": len(warnings),
        },
    }
