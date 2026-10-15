"""
DesignTrace AI - Database Design Module

This is a deterministic baseline implementation.
It generates an example relational database design
and supports human feedback for regeneration.
"""

from copy import deepcopy
import re

from shared.models.project import ProjectInput
from shared.models.database import (
    DatabaseColumn,
    DatabaseTable,
    DatabaseRelationship,
    DatabaseDesign,
    ForeignKeyReference,
)


def generate_database_design(
    project: ProjectInput,
    previous_design: DatabaseDesign | None = None,
    human_feedback: list[str] | None = None,
) -> DatabaseDesign:
    """
    Generate an initial design or revise an existing design.
    """

    feedback = [
        item.strip()
        for item in (human_feedback or [])
        if item.strip()
    ]

    if previous_design is not None:
        design = deepcopy(previous_design)
    else:
        design = _generate_initial_design()

    if feedback:
        design = _apply_feedback(design, feedback)

    return design


def _generate_initial_design() -> DatabaseDesign:
    """Create the initial example relational database."""

    patients_table = DatabaseTable(
        table_name="patients",
        purpose="Stores registered patient information.",
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
    )

    appointments_table = DatabaseTable(
        table_name="appointments",
        purpose="Stores patient appointment bookings.",
        columns=[
            DatabaseColumn(
                name="appointment_id",
                data_type="BIGINT",
                nullable=False,
                primary_key=True,
                source_requirement_ids=["FR-02"],
            ),
            DatabaseColumn(
                name="patient_id",
                data_type="BIGINT",
                nullable=False,
                foreign_key=ForeignKeyReference(
                    table="patients",
                    column="patient_id",
                ),
                source_requirement_ids=["FR-02"],
            ),
            DatabaseColumn(
                name="status",
                data_type="VARCHAR(50)",
                nullable=False,
                source_requirement_ids=["FR-02"],
            ),
        ],
        source_requirement_ids=["FR-02"],
    )

    relationship = DatabaseRelationship(
        relationship_id="REL-01",
        from_table="patients",
        to_table="appointments",
        relationship_type="one-to-many",
        foreign_key="appointments.patient_id",
        source_requirement_ids=["FR-02"],
    )

    return DatabaseDesign(
        tables=[patients_table, appointments_table],
        relationships=[relationship],
        constraints=["Patient email must be unique."],
    )


def _apply_feedback(
    design: DatabaseDesign,
    feedback: list[str],
) -> DatabaseDesign:
    """
    Apply supported deterministic database changes.
    """

    for instruction in feedback:

        normalized = re.sub(
            r"\s+",
            " ",
            instruction.lower().strip(),
        )

        mentions_doctor = bool(
            re.search(r"\bdoctors?\b", normalized)
        )

        add_doctors = (
            mentions_doctor
            and "table" in normalized
            and any(
                word in normalized
                for word in ("add", "create", "include")
            )
        )

        link_doctors = (
            mentions_doctor
            and "appointments" in normalized
            and any(
                word in normalized
                for word in ("link", "connect", "relationship")
            )
        )

        add_specialization = (
            "doctor" in normalized
            and "specialization" in normalized
            and "add" in normalized
        )

        improve_relationships = (
            normalized == "improve relationships."
            or normalized == "improve relationships"
        )

        add_constraints = (
            "add" in normalized
            and "database constraints" in normalized
        )

        # Reject unsupported feedback.
        if not any([
            add_doctors,
            link_doctors,
            add_specialization,
            improve_relationships,
            add_constraints,
        ]):
            raise ValueError(
                f"Unsupported database feedback: {instruction}"
            )

        # Create doctors table if required.
        if add_doctors or link_doctors or add_specialization:
            _ensure_doctors_table(design)

        # Connect doctors and appointments.
        if link_doctors:
            _ensure_doctor_appointment_relationship(design)

        # Add specialization to doctors.
        if add_specialization:

            doctors = next(
                table for table in design.tables
                if table.table_name == "doctors"
            )

            if not any(
                col.name == "specialization"
                for col in doctors.columns
            ):
                doctors.columns.append(
                    DatabaseColumn(
                        name="specialization",
                        data_type="VARCHAR(255)",
                        nullable=False,
                    )
                )

        # FIX: table_names is defined and used
        # inside the same conditional block.
        if improve_relationships:

            table_names = {
                table.table_name
                for table in design.tables
            }

            # Only create the relationship when
            # both required tables already exist.
            if (
                "doctors" in table_names
                and "appointments" in table_names
            ):
                _ensure_doctor_appointment_relationship(design)

        # Add example database constraint.
        if add_constraints:

            constraint = (
                "Appointment status must be "
                "a valid predefined value."
            )

            if constraint not in design.constraints:
                design.constraints.append(constraint)

    return design


def _ensure_doctors_table(
    design: DatabaseDesign,
) -> None:
    """Add doctors table if it does not already exist."""

    if any(
        table.table_name == "doctors"
        for table in design.tables
    ):
        return

    doctors_table = DatabaseTable(
        table_name="doctors",
        purpose="Stores doctor information.",
        columns=[
            DatabaseColumn(
                name="doctor_id",
                data_type="BIGINT",
                nullable=False,
                primary_key=True,
            ),
            DatabaseColumn(
                name="name",
                data_type="VARCHAR(255)",
                nullable=False,
            ),
        ],
    )

    design.tables.append(doctors_table)


def _ensure_doctor_appointment_relationship(
    design: DatabaseDesign,
) -> None:
    """Connect appointments to doctors."""

    appointments = next(
        (
            table
            for table in design.tables
            if table.table_name == "appointments"
        ),
        None,
    )

    if appointments is None:
        raise ValueError(
            "Cannot link doctors: appointments table is missing."
        )

    doctor_column_exists = any(
        column.name == "doctor_id"
        for column in appointments.columns
    )

    # Add doctor_id foreign key if missing.
    if not doctor_column_exists:

        appointments.columns.append(
            DatabaseColumn(
                name="doctor_id",
                data_type="BIGINT",
                nullable=False,
                foreign_key=ForeignKeyReference(
                    table="doctors",
                    column="doctor_id",
                ),
            )
        )

    relationship_exists = any(
        relationship.foreign_key == "appointments.doctor_id"
        for relationship in design.relationships
    )

    # Avoid duplicate relationships.
    if not relationship_exists:

        existing_ids = {
            relationship.relationship_id
            for relationship in design.relationships
        }

        number = 1

        while f"REL-{number:02d}" in existing_ids:
            number += 1

        design.relationships.append(
            DatabaseRelationship(
                relationship_id=f"REL-{number:02d}",
                from_table="doctors",
                to_table="appointments",
                relationship_type="one-to-many",
                foreign_key="appointments.doctor_id",
            )
        )
