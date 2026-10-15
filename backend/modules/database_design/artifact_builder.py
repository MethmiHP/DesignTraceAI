"""
Combine database design artifacts into one output.
"""

from typing import Any

from shared.models.database import DatabaseDesign

from modules.database_design.validator import (
    validate_database_design,
)
from modules.database_design.er_diagram import (
    generate_er_diagram,
)
from modules.database_design.sql_generator import (
    generate_sql_schema,
)


def build_database_artifacts(
    design: DatabaseDesign,
    requirements: list | None = None,
) -> dict[str, Any]:
    """
    Validate and combine database design artifacts.

    The Coordinator Agent handles human approval.
    """

    validation = validate_database_design(
        design,
        requirements,
    )

    result = {
        "database_design": design.model_dump(mode="json"),
        "validation_report": validation.model_dump(mode="json"),
        "er_diagram": None,
        "sql_schema": None,
        "requirement_mappings": [],
    }

    # Collect requirement-to-database mappings.
    # Only use database-relevant requirements.
    if requirements is not None:
        for requirement in requirements:
            if not requirement.database_relevant:
                continue

            requirement_id = requirement.requirement_id
            database_elements = []

            for table in design.tables:
                if requirement_id in table.source_requirement_ids:
                    database_elements.append(table.table_name)

                for column in table.columns:
                    if requirement_id in column.source_requirement_ids:
                        database_elements.append(
                            f"{table.table_name}.{column.name}"
                        )

            for relationship in design.relationships:
                if requirement_id in relationship.source_requirement_ids:
                    database_elements.append(
                        relationship.relationship_id
                    )

            result["requirement_mappings"].append(
                {
                    "requirement_id": requirement_id,
                    "database_elements": sorted(
                        set(database_elements)
                    ),
                }
            )

    # Generate artifacts only when validation passes.
    if validation.passed:
        result["er_diagram"] = generate_er_diagram(design)
        result["sql_schema"] = generate_sql_schema(design)

    return result
