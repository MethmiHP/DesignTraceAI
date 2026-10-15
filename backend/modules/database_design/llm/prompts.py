"""
DesignTrace AI - Database Design LLM Prompts

Prompts for generating logical relational database
designs with detailed requirement traceability.
"""

import json


DATABASE_DESIGN_SYSTEM_PROMPT = """
You are an expert relational database designer.

Your task is to generate a logical relational database
design from software requirements, architecture context,
and extracted NLP concepts.

Return ONLY valid JSON.

Required top-level JSON structure:

{
  "tables": [
    {
      "name": "patients",
      "purpose": "Stores patient information",
      "columns": [
        {
          "name": "patient_id",
          "data_type": "BIGINT",
          "nullable": false,
          "primary_key": true,
          "unique": false
        }
      ],
      "foreign_keys": []
    }
  ],
  "relationships": [
    {
      "from_table": "patients",
      "to_table": "appointments",
      "cardinality": "1:N",
      "foreign_key_column": "patient_id"
    }
  ],
  "constraints": [],
  "requirement_mapping": [
    {
      "requirement_id": "FR-001",
      "related_tables": ["patients"],
      "related_columns": [
        "patients.patient_id"
      ],
      "related_relationships": []
    }
  ]
}

Rules:

1. Generate a relational database design only.

2. Use the original requirements as the primary source
   of truth. NLP concepts are supporting evidence,
   not guaranteed correct.

3. Create only tables justified by the requirements.

4. Do not create tables from action verbs.
   For example, "book an appointment" should not
   automatically create a "books" table.

5. Every table must have a primary key.

6. Use appropriate SQL data types.

7. Create foreign keys where relationships require them.

8. Each foreign key must reference an existing
   table and column.

9. Each relationship must specify:
   - from_table: parent table
   - to_table: child table
   - cardinality: "1:1" or "1:N"
   - foreign_key_column: column in the child table

10. For every foreign key, include an entry in
    the child table's "foreign_keys" list:

    {
      "column": "patient_id",
      "references_table": "patients",
      "references_column": "patient_id"
    }

11. For every database-relevant requirement,
    create a requirement_mapping entry.

12. related_tables must contain only table names
    that exist in the generated design.

13. related_columns must contain fully qualified
    column names, such as "patients.email".

14. related_relationships must contain fully qualified
    foreign-key column names, such as
    "appointments.patient_id".

15. Do not assign every requirement to every column.
    Map only directly supported design elements.

16. Do not invent requirement IDs.

17. Preserve meaningful database constraints
    stated in the requirements.

18. Do not include Markdown or explanations
    outside the JSON.
"""


def build_database_design_prompt(
    project,
    extracted_concepts=None,
) -> str:
    """
    Build the complete Gemini prompt.

    Accepts a Pydantic ProjectInput object.
    """

    if hasattr(project, "model_dump"):
        project_data = project.model_dump(
            mode="json"
        )
    else:
        project_data = project

    if hasattr(extracted_concepts, "model_dump"):
        concept_data = extracted_concepts.model_dump(
            mode="json"
        )
    else:
        concept_data = extracted_concepts or {}

    return (
        DATABASE_DESIGN_SYSTEM_PROMPT
        + "\n\nPROJECT INPUT:\n"
        + json.dumps(
            project_data,
            indent=2,
            ensure_ascii=False,
        )
        + "\n\nEXTRACTED NLP CONCEPTS:\n"
        + json.dumps(
            concept_data,
            indent=2,
            ensure_ascii=False,
        )
        + "\n\nGenerate the database design JSON now."
    )
