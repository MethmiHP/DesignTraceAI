from shared.models.database import (
    DatabaseColumn,
    DatabaseTable,
    DatabaseDesign,
)

from modules.database_design.requirement_constraint_applier import (
    apply_requirement_constraints,
)


def make_design():
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
                    ),
                    DatabaseColumn(
                        name="age",
                        data_type="INTEGER",
                    ),
                ],
            ),
        ],
        relationships=[],
        constraints=[],
    )


def test_unique_constraint_applied():
    design = make_design()

    result = apply_requirement_constraints(
        design,
        [{
            "type": "UNIQUE",
            "table": "patients",
            "column": "email",
            "status": "MAPPED",
        }],
    )

    assert result.tables[0].columns[1].unique is True


def test_not_null_constraint_applied():
    design = make_design()

    result = apply_requirement_constraints(
        design,
        [{
            "type": "NOT_NULL",
            "table": "patients",
            "column": "email",
            "status": "MAPPED",
        }],
    )

    assert result.tables[0].columns[1].nullable is False


def test_check_constraint_applied():
    design = make_design()

    result = apply_requirement_constraints(
        design,
        [{
            "type": "CHECK",
            "table": "patients",
            "column": "age",
            "expression": ">= 18",
            "status": "MAPPED",
        }],
    )

    assert "CHECK (age >= 18)" in result.constraints


def test_unmapped_constraint_ignored():
    design = make_design()

    result = apply_requirement_constraints(
        design,
        [{
            "type": "UNIQUE",
            "table": None,
            "column": "email",
            "status": "UNMAPPED",
        }],
    )

    assert result.tables[0].columns[1].unique is False
