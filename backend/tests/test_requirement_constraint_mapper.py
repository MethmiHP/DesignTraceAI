from shared.models.database import (
    DatabaseColumn,
    DatabaseTable,
    DatabaseDesign,
)

from modules.database_design.requirement_constraint_mapper import (
    map_requirement_constraints,
)


def make_design():
    return DatabaseDesign(
        tables=[
            DatabaseTable(
                table_name="patients",
                purpose="Stores patients.",
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
                    ),
                ],
            ),
        ],
        relationships=[],
        constraints=[],
    )


def test_unique_constraint_mapped():
    design = make_design()

    constraints = [{
        "type": "UNIQUE",
        "column": "email",
        "source_requirement": "Patient email must be unique.",
    }]

    result = map_requirement_constraints(
        design,
        constraints,
    )

    assert result[0]["table"] == "patients"
    assert result[0]["status"] == "MAPPED"


def test_unknown_column_unmapped():
    design = make_design()

    constraints = [{
        "type": "NOT_NULL",
        "column": "phone",
        "source_requirement": "Phone must be required.",
    }]

    result = map_requirement_constraints(
        design,
        constraints,
    )

    assert result[0]["status"] == "UNMAPPED"


def test_ambiguous_column_not_applied():
    design = make_design()

    design.tables.append(
        DatabaseTable(
            table_name="doctors",
            purpose="Stores doctors.",
            columns=[
                DatabaseColumn(
                    name="doctor_id",
                    data_type="BIGINT",
                    nullable=False,
                    primary_key=True,
                ),
                DatabaseColumn(
                    name="email",
                    data_type="VARCHAR(255)",
                ),
            ],
        )
    )

    constraints = [{
        "type": "UNIQUE",
        "column": "email",
        "source_requirement": "Email must be unique.",
    }]

    result = map_requirement_constraints(
        design,
        constraints,
    )

    assert result[0]["status"] == "AMBIGUOUS"
    assert result[0]["table"] is None
