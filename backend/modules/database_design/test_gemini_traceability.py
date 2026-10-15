from modules.database_design.gemini_adapter import (
    convert_gemini_design,
)


sample = {
    "tables": [
        {
            "name": "patients",
            "columns": [
                {
                    "name": "patient_id",
                    "data_type": "BIGINT",
                    "nullable": False,
                    "primary_key": True,
                },
                {
                    "name": "email",
                    "data_type": "VARCHAR(255)",
                    "unique": True,
                },
            ],
        },
        {
            "name": "appointments",
            "columns": [
                {
                    "name": "appointment_id",
                    "data_type": "BIGINT",
                    "nullable": False,
                    "primary_key": True,
                },
                {
                    "name": "patient_id",
                    "data_type": "BIGINT",
                    "nullable": False,
                },
            ],
            "foreign_keys": [
                {
                    "column": "patient_id",
                    "references_table": "patients",
                    "references_column": "patient_id",
                }
            ],
        },
    ],
    "relationships": [
        {
            "from_table": "patients",
            "to_table": "appointments",
            "cardinality": "1:N",
            "foreign_key_column": "patient_id",
        }
    ],
    "requirement_mapping": [
        {
            "requirement_id": "FR-001",
            "related_tables": ["patients"],
            "related_columns": [
                "patients.email"
            ],
            "related_relationships": [],
        },
        {
            "requirement_id": "FR-002",
            "related_tables": [
                "patients",
                "appointments",
            ],
            "related_columns": [
                "appointments.patient_id"
            ],
            "related_relationships": [
                "appointments.patient_id"
            ],
        },
    ],
    "constraints": [],
}


design = convert_gemini_design(sample)

patients = next(
    table for table in design.tables
    if table.table_name == "patients"
)

email = next(
    column for column in patients.columns
    if column.name == "email"
)

relationship = design.relationships[0]

assert email.source_requirement_ids == [
    "FR-001"
]

assert relationship.source_requirement_ids == [
    "FR-002"
]

print("Column traceability:", email.source_requirement_ids)
print(
    "Relationship traceability:",
    relationship.source_requirement_ids,
)
print("Traceability adapter test passed!")
