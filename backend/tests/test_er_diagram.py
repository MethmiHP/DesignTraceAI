from shared.models.database import (
    DatabaseColumn,
    DatabaseDesign,
    DatabaseTable,
)

from modules.database_design.er_diagram import (
    generate_er_diagram,
)


def create_sample_design():
    return DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="patients",
                purpose="Stores patient information.",
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
            )
        ]
    )


def test_mermaid_header():
    diagram = generate_er_diagram(create_sample_design())

    assert diagram.startswith("erDiagram")


def test_entity_generated():
    diagram = generate_er_diagram(create_sample_design())

    assert "patients {" in diagram


def test_primary_key_generated():
    diagram = generate_er_diagram(create_sample_design())

    assert "BIGINT patient_id PK" in diagram


def test_data_type_generated():
    diagram = generate_er_diagram(create_sample_design())

    assert "VARCHAR_255_ email" in diagram
