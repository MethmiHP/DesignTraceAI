"""
DesignTrace AI - Baseline Database Schema Generator
===================================================

Converts extracted database concepts into a basic
relational database design.

Tracks requirement IDs for generated tables and columns.

This is a deterministic baseline.
"""

import re

from shared.models.project import ProjectInput
from shared.models.database import (
    DatabaseColumn,
    DatabaseTable,
    DatabaseDesign,
)

from modules.database_design.concept_pipeline import (
    run_concept_pipeline,
)

from modules.database_design.requirement_constraint_extractor import (
    extract_requirement_constraints,
)


def generate_schema_from_concepts(
    project: ProjectInput,
) -> DatabaseDesign:
    """
    Generate a relational database design with
    table-level and column-level requirement traceability.
    """

    concepts = run_concept_pipeline(project)

    tables = []
    relationships = []

    # Extract constraints from database-related requirements.
    requirement_constraints = {}

    for requirement in project.requirements:

        if not requirement.database_relevant:
            continue

        requirement_constraints[
            requirement.requirement_id
        ] = extract_requirement_constraints(
            [requirement.requirement_text]
        )

    # Create one table for each extracted entity.
    for entity in concepts.candidate_entities:

        table_name = f"{entity}s"

        entity_attributes = set()
        source_ids = set()

        # Store which requirements mention each attribute.
        attribute_sources = {}

        # Step 1: Collect attributes from concept extraction.
        for result in concepts.requirement_concepts:

            if entity not in result.entities:
                continue

            source_ids.add(result.requirement_id)

            for attribute in result.attributes:

                entity_attributes.add(attribute)

                attribute_sources.setdefault(
                    attribute, set()
                ).add(result.requirement_id)

        # Step 2: Collect attributes from requirement constraints.
        for requirement in project.requirements:

            if not requirement.database_relevant:
                continue

            text = requirement.requirement_text.lower()

            entity_pattern = (
                rf"\b{re.escape(entity)}s?\b"
            )

            if not re.search(entity_pattern, text):
                continue

            extracted = requirement_constraints.get(
                requirement.requirement_id,
                [],
            )

            for constraint in extracted:

                attribute = constraint.get("column")

                if not attribute:
                    continue

                entity_attributes.add(attribute)

                attribute_sources.setdefault(
                    attribute, set()
                ).add(requirement.requirement_id)

                source_ids.add(requirement.requirement_id)

        # Step 3: Create primary key.
        primary_key = DatabaseColumn(
            name=f"{entity}_id",
            data_type="BIGINT",
            nullable=False,
            primary_key=True,
            source_requirement_ids=[],
        )


        columns = [primary_key]

        # Step 4: Create columns with requirement IDs.
        for attribute in sorted(entity_attributes):

            if attribute == f"{entity}_id":
                continue

            data_type = "VARCHAR(255)"

            if attribute in {"age", "quantity"}:
                data_type = "INTEGER"

            elif attribute == "price":
                data_type = "DECIMAL(10,2)"

            elif attribute in {"date", "publication_date"}:
                data_type = "DATE"

            elif attribute == "time":
                data_type = "TIME"

            columns.append(
                DatabaseColumn(
                    name=attribute,
                    data_type=data_type,
                    nullable=True,
                    source_requirement_ids=sorted(
                        attribute_sources.get(
                            attribute, set()
                        )
                    ),
                )
            )

        # Step 5: Create table with requirement IDs.
        tables.append(
            DatabaseTable(
                table_name=table_name,
                purpose=f"Stores {entity} information.",
                columns=columns,
                source_requirement_ids=sorted(source_ids),
            )
        )

    return DatabaseDesign(
        tables=tables,
        relationships=relationships,
        constraints=[],
    )
