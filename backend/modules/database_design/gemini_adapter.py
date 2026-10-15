"""
DesignTrace AI - Gemini Database Design Adapter

Converts Gemini-generated JSON into the existing
DatabaseDesign structure.

Supports:
- Tables and columns
- Primary and foreign keys
- Relationships
- Table-level requirement traceability
- Column-level requirement traceability
- Relationship-level requirement traceability

Does not invent requirement mappings.
"""

from collections import defaultdict

from shared.models.database import (
    DatabaseDesign,
    DatabaseTable,
    DatabaseColumn,
    DatabaseRelationship,
    ForeignKeyReference,
)


def convert_gemini_design(gemini_design: dict) -> DatabaseDesign:

    if not isinstance(gemini_design, dict):
        raise ValueError(
            "Gemini design must be a dictionary."
        )

    raw_tables = gemini_design.get("tables", [])
    raw_relationships = gemini_design.get(
        "relationships", []
    )
    raw_mappings = gemini_design.get(
        "requirement_mapping", []
    )

    if not isinstance(raw_tables, list):
        raise ValueError("'tables' must be a list.")

    if not isinstance(raw_relationships, list):
        raise ValueError(
            "'relationships' must be a list."
        )

    if not isinstance(raw_mappings, list):
        raise ValueError(
            "'requirement_mapping' must be a list."
        )

    table_sources = defaultdict(set)
    column_sources = defaultdict(set)
    relationship_sources = defaultdict(set)

    # ---------------------------------------
    # Step 1: Read detailed requirement links
    # ---------------------------------------

    for mapping in raw_mappings:

        requirement_id = mapping[
            "requirement_id"
        ]

        for table_name in mapping.get(
            "related_tables", []
        ):
            table_sources[table_name].add(
                requirement_id
            )

        for column_ref in mapping.get(
            "related_columns", []
        ):
            column_sources[column_ref].add(
                requirement_id
            )

        for relationship_ref in mapping.get(
            "related_relationships", []
        ):
            relationship_sources[
                relationship_ref
            ].add(requirement_id)

    # ---------------------------------------
    # Step 2: Convert tables and columns
    # ---------------------------------------

    tables = []
    table_lookup = {}

    for raw_table in raw_tables:

        table_name = raw_table["name"]

        if table_name in table_lookup:
            raise ValueError(
                f"Duplicate table: {table_name}"
            )

        columns = []
        column_lookup = {}

        for raw_column in raw_table.get(
            "columns", []
        ):

            column_name = raw_column["name"]

            if column_name in column_lookup:
                raise ValueError(
                    f"Duplicate column: "
                    f"{table_name}.{column_name}"
                )

            column_ref = (
                f"{table_name}.{column_name}"
            )

            direct_ids = raw_column.get(
                "source_requirement_ids", []
            )

            if not isinstance(direct_ids, list):
                raise ValueError(
                    f"Invalid requirement IDs for "
                    f"{column_ref}"
                )

            source_ids = set(
                column_sources[column_ref]
            )
            source_ids.update(direct_ids)

            column = DatabaseColumn(
                name=column_name,
                data_type=raw_column["data_type"],
                nullable=raw_column.get(
                    "nullable", True
                ),
                primary_key=raw_column.get(
                    "primary_key", False
                ),
                unique=raw_column.get(
                    "unique", False
                ),
                source_requirement_ids=sorted(
                    source_ids
                ),
            )

            columns.append(column)
            column_lookup[column_name] = column

        direct_table_ids = raw_table.get(
            "source_requirement_ids", []
        )

        if not isinstance(direct_table_ids, list):
            raise ValueError(
                f"Invalid requirement IDs for "
                f"table {table_name}"
            )

        source_ids = set(
            table_sources[table_name]
        )
        source_ids.update(direct_table_ids)

        table = DatabaseTable(
            table_name=table_name,
            purpose=raw_table.get("purpose"),
            columns=columns,
            source_requirement_ids=sorted(
                source_ids
            ),
        )

        tables.append(table)

        table_lookup[table_name] = {
            "table": table,
            "columns": column_lookup,
        }

    # ---------------------------------------
    # Step 3: Convert foreign keys
    # ---------------------------------------

    foreign_keys = []

    for raw_table in raw_tables:

        table_name = raw_table["name"]

        for raw_fk in raw_table.get(
            "foreign_keys", []
        ):

            source_column = raw_fk["column"]
            target_table = raw_fk[
                "references_table"
            ]
            target_column = raw_fk[
                "references_column"
            ]

            if source_column not in table_lookup[
                table_name
            ]["columns"]:
                raise ValueError(
                    f"Missing foreign key column: "
                    f"{table_name}.{source_column}"
                )

            if target_table not in table_lookup:
                raise ValueError(
                    f"Missing referenced table: "
                    f"{target_table}"
                )

            if target_column not in table_lookup[
                target_table
            ]["columns"]:
                raise ValueError(
                    f"Missing referenced column: "
                    f"{target_table}.{target_column}"
                )

            source = table_lookup[
                table_name
            ]["columns"][source_column]

            if source.foreign_key is not None:
                raise ValueError(
                    f"Multiple foreign keys on "
                    f"{table_name}.{source_column}"
                )

            source.foreign_key = (
                ForeignKeyReference(
                    table=target_table,
                    column=target_column,
                )
            )

            foreign_keys.append({
                "child_table": table_name,
                "child_column": source_column,
                "parent_table": target_table,
                "parent_column": target_column,
            })

    # ---------------------------------------
    # Step 4: Convert relationships
    # ---------------------------------------

    relationships = []

    cardinality_map = {
        "1:1": "one-to-one",
        "1:N": "one-to-many",
        "N:1": "many-to-one",
        "N:M": "many-to-many",
        "one-to-one": "one-to-one",
        "one-to-many": "one-to-many",
        "many-to-one": "many-to-one",
        "many-to-many": "many-to-many",
    }

    for index, raw_rel in enumerate(
        raw_relationships,
        start=1,
    ):

        parent_table = raw_rel["from_table"]
        child_table = raw_rel["to_table"]

        raw_cardinality = raw_rel["cardinality"]

        if raw_cardinality not in cardinality_map:
            raise ValueError(
                f"Unsupported cardinality: "
                f"{raw_cardinality}"
            )

        if parent_table not in table_lookup:
            raise ValueError(
                f"Unknown table: {parent_table}"
            )

        if child_table not in table_lookup:
            raise ValueError(
                f"Unknown table: {child_table}"
            )

        foreign_key_column = raw_rel.get(
            "foreign_key_column"
        )

        if not foreign_key_column:
            raise ValueError(
                f"Missing foreign_key_column for "
                f"{parent_table} -> {child_table}"
            )

        matching_fks = [
            fk for fk in foreign_keys
            if (
                fk["parent_table"] == parent_table
                and fk["child_table"] == child_table
                and fk["child_column"]
                == foreign_key_column
            )
        ]

        if len(matching_fks) != 1:
            raise ValueError(
                f"Invalid relationship foreign key: "
                f"{child_table}."
                f"{foreign_key_column}"
            )

        fk_reference = (
            f"{child_table}."
            f"{foreign_key_column}"
        )

        direct_ids = raw_rel.get(
            "source_requirement_ids", []
        )

        if not isinstance(direct_ids, list):
            raise ValueError(
                f"Invalid relationship requirement "
                f"IDs for {fk_reference}"
            )

        source_ids = set(
            relationship_sources[fk_reference]
        )
        source_ids.update(direct_ids)

        relationships.append(
            DatabaseRelationship(
                relationship_id=(
                    f"REL-{index:03d}"
                ),
                from_table=parent_table,
                to_table=child_table,
                relationship_type=(
                    cardinality_map[
                        raw_cardinality
                    ]
                ),
                foreign_key=fk_reference,
                source_requirement_ids=sorted(
                    source_ids
                ),
            )
        )

    # ---------------------------------------
    # Step 5: Return standard design
    # ---------------------------------------

    return DatabaseDesign(
        tables=tables,
        relationships=relationships,
        constraints=gemini_design.get(
            "constraints", []
        ),
    )
