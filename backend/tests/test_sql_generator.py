import pytest

from shared.models.database import (
    DatabaseColumn,
    DatabaseDesign,
    DatabaseTable,
    ForeignKeyReference,
)

from modules.database_design.sql_generator import (
    generate_sql_schema,
)


def create_sample_design():
    return DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="patients",
                columns=[
                    DatabaseColumn(
                        name="patient_id",
                        data_type="BIGINT",
                        nullable=False,
                        primary_key=True,
                    ),
                    DatabaseColumn(
                        name="email",
                        data_type="VARCHAR(255)",
                        nullable=False,
                        unique=True,
                    ),
                ],
            ),
            DatabaseTable(
                table_name="appointments",
                columns=[
                    DatabaseColumn(
                        name="appointment_id",
                        data_type="BIGINT",
                        nullable=False,
                        primary_key=True,
                    ),
                    DatabaseColumn(
                        name="patient_id",
                        data_type="BIGINT",
                        nullable=False,
                        foreign_key=ForeignKeyReference(
                            table="patients",
                            column="patient_id",
                        ),
                    ),
                ],
            ),
        ]
    )


def test_create_table_generated():
    sql = generate_sql_schema(create_sample_design())
    assert 'CREATE TABLE "patients"' in sql


def test_primary_key_generated():
    sql = generate_sql_schema(create_sample_design())
    assert 'PRIMARY KEY ("patient_id")' in sql


def test_unique_constraint_generated():
    sql = generate_sql_schema(create_sample_design())
    assert '"email" VARCHAR(255) NOT NULL UNIQUE' in sql


def test_foreign_key_generated():
    sql = generate_sql_schema(create_sample_design())
    assert 'REFERENCES "patients" ("patient_id")' in sql


def test_invalid_data_type_rejected():
    design = DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="test_table",
                columns=[
                    DatabaseColumn(
                        name="id",
                        data_type="INVALID_TYPE",
                        primary_key=True,
                    )
                ],
            )
        ]
    )

    with pytest.raises(ValueError):
        generate_sql_schema(design)
