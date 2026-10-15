"""
DesignTrace AI - Gemini Database Design Generator

Generates logical relational database schemas using Gemini.

Supports:
1. Original project requirements
2. Architecture context
3. RoBERTa-extracted NLP concepts
4. Structured JSON generation
5. Table-level requirement traceability
6. Column-level requirement traceability
7. Relationship-level requirement traceability
8. Gemini retry handling
9. Saving generated JSON

This module generates a draft database design.
Human approval belongs to the Coordinator Agent.
"""

import json
import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors
from pydantic import BaseModel, Field

from modules.database_design.llm.prompts import (
    DATABASE_DESIGN_SYSTEM_PROMPT,
)



# Project paths and environment


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

# Gemini structured output models


class Column(BaseModel):
    name: str
    data_type: str
    nullable: bool
    primary_key: bool
    unique: bool


class ForeignKey(BaseModel):
    column: str
    references_table: str
    references_column: str


class DatabaseTable(BaseModel):
    name: str
    columns: list[Column]
    foreign_keys: list[ForeignKey] = Field(
        default_factory=list
    )


class Relationship(BaseModel):
    from_table: str
    to_table: str
    cardinality: str
    foreign_key_column: str


class RequirementMapping(BaseModel):
    requirement_id: str

    related_tables: list[str] = Field(
        default_factory=list
    )

    related_columns: list[str] = Field(
        default_factory=list
    )

    related_relationships: list[str] = Field(
        default_factory=list
    )


class DatabaseDesign(BaseModel):
    project_name: str

    tables: list[DatabaseTable] = Field(
        default_factory=list
    )

    relationships: list[Relationship] = Field(
        default_factory=list
    )

    constraints: list[str] = Field(
        default_factory=list
    )

    requirement_mapping: list[RequirementMapping] = Field(
        default_factory=list
    )

    assumptions: list[str] = Field(
        default_factory=list
    )

# Prompt builder

def build_gemini_database_prompt(
    requirements,
    project_name="DesignTrace AI Project",
    architecture_context=None,
    database_constraints=None,
    extracted_concepts=None,
):
    """
    Build the prompt for Gemini using:
    - original requirements
    - architecture context
    - database constraints
    - extracted NLP concepts

    The main instructions come from llm/prompts.py.
    """

    input_data = {
        "project_name": project_name,
        "requirements": requirements,
        "architecture_context": (
            architecture_context or {}
        ),
        "database_constraints": (
            database_constraints or []
        ),
        "extracted_concepts": (
            extracted_concepts
            if extracted_concepts is not None
            else []
        ),
    }

    additional_instructions = """
IMPORTANT OUTPUT REQUIREMENTS:

Return a JSON object containing:

1. project_name
2. tables
3. relationships
4. constraints
5. requirement_mapping
6. assumptions

TABLE FORMAT:

Each table must contain:
- name
- columns
- foreign_keys

Each column must contain:
- name
- data_type
- nullable
- primary_key
- unique

Each foreign key must contain:
- column
- references_table
- references_column

RELATIONSHIP FORMAT:

Each relationship must contain:
- from_table
- to_table
- cardinality
- foreign_key_column

The from_table is the referenced parent table.
The to_table is the child table containing the foreign key.

Use these cardinalities:
- "1:1"
- "1:N"

For many-to-many relationships, create a junction table
and represent the resulting one-to-many relationships.

If two foreign keys connect the same pair of tables,
generate a separate relationship for each foreign key.

REQUIREMENT TRACEABILITY:

Every requirement_mapping entry must contain:

- requirement_id
- related_tables
- related_columns
- related_relationships

related_tables:
Use actual generated table names.

Example:
["patients", "appointments"]

related_columns:
Use fully qualified column names.

Example:
["patients.email", "appointments.appointment_date"]

related_relationships:
Use the fully qualified foreign-key column that
implements the relationship.

Example:
["appointments.patient_id"]

Only map elements directly supported by the requirement.

Do not map every requirement to every column.

Do not invent requirement IDs.

Do not reference tables, columns, or foreign keys
that do not exist in the generated design.

NLP CONCEPT RULES:

The extracted NLP concepts are supporting information.

The original requirements are the primary source of truth.

An ACTION is not automatically a database entity.

For example:
"Patients can book appointments"

The action "book" should not automatically create
a "books" table.

Generate database tables based on the actual
data-storage needs described by the requirements.

DATABASE DESIGN RULES:

Every table must have a primary key.

Every foreign key must reference an existing table
and an existing column.

Use PostgreSQL-compatible data types.

Respect the supplied architecture context.

Include relevant database constraints.

Avoid unrelated tables.

Record any assumptions in the assumptions field.

Return only valid JSON.
Do not include Markdown formatting.
"""

    prompt = (
        DATABASE_DESIGN_SYSTEM_PROMPT
        + "\n\n"
        + additional_instructions
        + "\n\nPROJECT INPUT:\n"
        + json.dumps(
            input_data,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
        + "\n\nGenerate the database design JSON now."
    )

    return prompt



# Gemini database generation

def generate_database_design(
    requirements,
    project_name="DesignTrace AI Project",
    architecture_context=None,
    database_constraints=None,
    extracted_concepts=None,
):
    """
    Generate a logical relational database design
    using Gemini.

    Returns a Python dictionary compatible with
    the existing Gemini database adapter.
    """

    # Step 1: Read API key.

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing from backend/.env"
        )

    # Step 2: Create Gemini client.

    client = genai.Client(
        api_key=api_key
    )

    # Keep the configured model from .env.
    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.8-flash"
    )

    # Step 3: Build prompt.

    prompt = build_gemini_database_prompt(
        requirements=requirements,
        project_name=project_name,
        architecture_context=architecture_context,
        database_constraints=database_constraints,
        extracted_concepts=extracted_concepts,
    )

    # Step 4: Call Gemini with retries.

    max_attempts = 3
    response = None

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        try:
            print(
                f"Calling Gemini model: {model_name} "
                f"(attempt {attempt}/{max_attempts})"
            )

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": DatabaseDesign,
                    "temperature": 0.2,
                },
            )

            break

        except errors.ServerError as error:

            if (
                error.code != 503
                or attempt == max_attempts
            ):
                raise

            wait_seconds = min(
                2 ** attempt
                + random.uniform(0, 1),
                15,
            )

            print(
                "Gemini temporarily unavailable. "
                f"Retrying in {wait_seconds:.1f} seconds..."
            )

            time.sleep(
                wait_seconds
            )

    # Step 5: Check Gemini response.

    if response is None:
        raise RuntimeError(
            "Gemini did not return a response."
        )

    # Step 6: Parse structured output.

    if response.parsed is not None:

        design = DatabaseDesign.model_validate(
            response.parsed
        )

    elif response.text:

        design = DatabaseDesign.model_validate_json(
            response.text
        )

    else:

        raise RuntimeError(
            "Gemini returned no database design."
        )

    # Step 7: Convert Pydantic output to dictionary.

    design_data = design.model_dump(
        mode="json"
    )

    # Step 8: Report generated design information.

    print(
        "Gemini database design generated successfully."
    )

    print(
        "Generated tables:",
        len(design_data["tables"])
    )

    print(
        "Generated relationships:",
        len(design_data["relationships"])
    )

    print(
        "Requirement mappings:",
        len(design_data["requirement_mapping"])
    )

    return design_data


# Save generated database design


def save_database_design(
    design,
    filename,
):
    """
    Save Gemini-generated database design
    as a JSON file.
    """

    output_dir = (
        BASE_DIR
        / "outputs"
        / "database_designs"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir / filename
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            design,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return output_path
