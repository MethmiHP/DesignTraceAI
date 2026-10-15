"""
DesignTrace AI - Database Design Models
=======================================

Purpose:
    This file defines the standard structured output produced by the
    AI-Assisted Database Design Module.

What happens here:
    The Database Design Module will eventually receive:

        Requirements
            +
        Architecture Context
            +
        Extracted Database Concepts
            ↓
        Database Design Module
            ↓
        Structured DatabaseDesign object

The DatabaseDesign object contains:

    - Tables
    - Columns / attributes
    - Primary keys
    - Foreign keys
    - Relationships
    - Cardinalities
    - Constraints
    - Requirement references

Why this is important:
    We do NOT want the LLM to return only unstructured text.

    The generated database design should follow a predictable structure
    so that Python validation rules can check the design before the
    Coordinator accepts it.

Important:
    This represents a logical relational database design.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ForeignKeyReference(BaseModel):
    """
    Represents the target of a foreign key.

    Example:

        appointments.patient_id
                ↓
        patients.patient_id
    """

    # Referenced table.
    table: str

    # Referenced column.
    column: str


class DatabaseColumn(BaseModel):
    """
    Represents one column/attribute inside a relational table.

    Example:

        patient_id BIGINT PRIMARY KEY
    """

    # Column name.
    name: str

    # SQL-style data type.
    data_type: str

    # Whether NULL values are allowed.
    nullable: bool = True

    # Whether this column is a primary key.
    primary_key: bool = False

    # Whether values must be unique.
    unique: bool = False

    # Foreign-key information.
    # None means this column is not a foreign key.
    foreign_key: Optional[ForeignKeyReference] = None

    # Requirements that caused this column to be created.
    source_requirement_ids: list[str] = Field(default_factory=list)


class DatabaseTable(BaseModel):
    """
    Represents one relational database table.

    Example:

        patients
        ----------------
        patient_id PK
        email
        phone
    """

    # Table name.
    table_name: str

    # Short explanation of why the table exists.
    purpose: Optional[str] = None

    # Columns belonging to this table.
    columns: list[DatabaseColumn] = Field(default_factory=list)

    # Requirements supported by this table.
    source_requirement_ids: list[str] = Field(default_factory=list)


class DatabaseRelationship(BaseModel):
    """
    Represents a relationship between two tables.

    Example:

        patients 1 -------- * appointments

    relationship_type:
        one-to-one
        one-to-many
        many-to-many
    """

    # Unique relationship identifier.
    relationship_id: str

    # Parent/source table.
    from_table: str

    # Child/target table.
    to_table: str

    # Example: one-to-many.
    relationship_type: str

    # Foreign key that implements the relationship.
    # Example: appointments.patient_id
    foreign_key: Optional[str] = None

    # Requirements responsible for the relationship.
    source_requirement_ids: list[str] = Field(default_factory=list)


class DatabaseDesign(BaseModel):
    """
    Represents the complete logical relational database design.

    This will become the main structured output of the
    Database Design Module.
    """

    # All generated relational tables.
    tables: list[DatabaseTable] = Field(default_factory=list)

    # Relationships between generated tables.
    relationships: list[DatabaseRelationship] = Field(
        default_factory=list
    )

    # Additional database-level constraints.
    constraints: list[str] = Field(default_factory=list)