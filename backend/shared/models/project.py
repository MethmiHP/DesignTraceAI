"""
DesignTrace AI - Project Input Models
=====================================

Purpose:
    This file defines the standard input structures used by
    DesignTrace AI.

What happens here:
    The Coordinator Agent receives information about a software
    project, including:

        - Project ID
        - Project name
        - Project description
        - Software requirements
        - Architecture information

Why this is important:
    Different Modules need to exchange information using the same
    structured format.

    Instead of passing unstructured Python dictionaries everywhere,
    Pydantic models are used to define and validate the expected
    project data.

Example workflow:

    Project Input
         ↓
    Coordinator Agent
         ↓
    Requirement Analysis Module
         ↓
    Architecture Decision Module
         ↓
    Database Design Module

Note:
    This is the initial model. More fields can be added later when
    other DesignTrace AI Modules are integrated.
"""

from typing import Optional

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """
    Represents one software requirement.

    Example:
        FR-01:
        "A patient can register an account."
    """

    # Unique requirement identifier.
    requirement_id: str

    # Original natural-language requirement.
    requirement_text: str

    # Requirement category such as FR, NFR or ASR.
    # It is optional because the Requirement Analysis Module may
    # determine this later.
    requirement_type: Optional[str] = None

    # Indicates whether this requirement affects database design.
    database_relevant: bool = False


class ArchitectureContext(BaseModel):
    """
    Represents architecture information that may influence
    database design.

    This information will normally come from the approved
    Architecture Decision Module output.
    """

    # Example: Layered Architecture, Microservices, etc.
    architecture_style: Optional[str] = None

    # Our research currently focuses on relational databases.
    database_type: str = "Relational"

    # Architecture or database-related constraints.
    constraints: list[str] = Field(default_factory=list)


class ProjectInput(BaseModel):
    """
    Represents the basic input of one DesignTrace AI project.

    The Coordinator Agent receives this information and maintains
    it as part of the shared project state.
    """

    # Unique project identifier.
    project_id: str

    # Human-readable project name.
    project_name: str

    # Short explanation of the software project.
    project_description: str

    # Requirements belonging to the project.
    requirements: list[Requirement] = Field(default_factory=list)

    # Architecture information is optional at the beginning because
    # it may be generated later by the Architecture Decision Module.
    architecture_context: Optional[ArchitectureContext] = None