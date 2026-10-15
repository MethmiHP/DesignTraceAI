from shared.models.database import (
    DatabaseColumn,
    DatabaseDesign,
    DatabaseTable,
)
from shared.models.project import Requirement

from modules.database_design.artifact_builder import (
    build_database_artifacts,
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
                        source_requirement_ids=["FR-01"],
                    ),
                    DatabaseColumn(
                        name="email",
                        data_type="VARCHAR(255)",
                        nullable=False,
                        unique=True,
                        source_requirement_ids=["FR-01"],
                    ),
                ],
                source_requirement_ids=["FR-01"],
            ),
        ]
    )


def create_requirements():
    return [
        Requirement(
            requirement_id="FR-01",
            requirement_text="A patient can register an account.",
            requirement_type="FR",
            database_relevant=True,
        )
    ]


def test_artifacts_generated():
    result = build_database_artifacts(
        create_sample_design(),
        create_requirements(),
    )

    assert result["validation_report"]["passed"] is True
    assert result["er_diagram"].startswith("erDiagram")
    assert 'CREATE TABLE "patients"' in result["sql_schema"]


def test_requirement_mapping_generated():
    result = build_database_artifacts(
        create_sample_design(),
        create_requirements(),
    )

    mappings = result["requirement_mappings"]

    assert len(mappings) == 1
    assert mappings[0]["requirement_id"] == "FR-01"
    assert "patients" in mappings[0]["database_elements"]
    assert "patients.email" in mappings[0]["database_elements"]


def test_invalid_design_does_not_generate_sql():
    bad_design = DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="doctors",
                columns=[
                    DatabaseColumn(
                        name="doctor_name",
                        data_type="VARCHAR(255)",
                        nullable=False,
                    )
                ],
            )
        ]
    )

    result = build_database_artifacts(bad_design)

    assert result["validation_report"]["passed"] is False
    assert result["sql_schema"] is None
    assert result["er_diagram"] is None
