"""
DesignTrace AI - Coordinator State Manager
==========================================

Purpose:
    This file manages the shared project state used by the
    Coordinator Agent.

What happens here:
    When a new project enters DesignTrace AI, the Coordinator
    creates one central ProjectState.

The ProjectState contains:

    1. Original project information
    2. Current status of every Module
    3. Generated artifacts
    4. Module outputs
    5. Validation results and workflow information

Why this is important:
    The Coordinator needs a single source of truth for the
    complete DesignTrace AI workflow.

Current implementation:
    State is stored in memory using Pydantic models.

Future improvement:
    The same state can later be saved using PostgreSQL,
    Redis, or another storage system.
"""

from typing import Any

from pydantic import BaseModel, Field

from shared.models.project import ProjectInput
from shared.models.workflow import ModuleState, WorkflowStatus


# ------------------------------------------------------------
# MODULES CONTROLLED BY THE COORDINATOR
# ------------------------------------------------------------

DESIGNTRACE_MODULES = [
    "requirement_analysis",
    "architecture_design",
    "database_design",
    "api_component_design",
    "traceability",
    "quality_evaluation",
    "adr",
]


# ------------------------------------------------------------
# SHARED PROJECT STATE
# ------------------------------------------------------------

class ProjectState(BaseModel):
    """
    Represents the complete shared state of one
    DesignTrace AI project.
    """

    # Original project information.
    project: ProjectInput

    # Current status of every Module.
    module_states: dict[str, ModuleState] = Field(
        default_factory=dict
    )

    # Existing storage for generated artifacts.
    artifacts: dict[str, Any] = Field(
        default_factory=dict
    )

    # NEW: Stores generated outputs from Modules.
    #
    # Example:
    # module_outputs["database_design"] = {
    #     "validation_report": {...},
    #     "er_diagram": "...",
    #     "sql_schema": "...",
    #     "requirement_mappings": [...]
    # }
    module_outputs: dict[str, dict] = Field(
        default_factory=dict
    )

    # Stores previous versions of Module outputs.
    module_output_history: dict[str, list[dict]] = Field(
    default_factory=dict
    )


# ------------------------------------------------------------
# INITIAL PROJECT STATE CREATION
# ------------------------------------------------------------

def create_initial_project_state(
    project: ProjectInput,
) -> ProjectState:
    """
    Create the initial Coordinator state for a new project.

    Every Module starts with:

        status = PENDING
        version = 0
        retry_count = 0
        validation_passed = False

    All generated outputs start empty.
    """

    module_states = {}

    # Create an initial state for each Module.
    for module_name in DESIGNTRACE_MODULES:

        module_states[module_name] = ModuleState(
            module_name=module_name,
            status=WorkflowStatus.PENDING,
        )

    # Create the complete shared project state.
    return ProjectState(
        project=project,
        module_states=module_states,
        artifacts={},
        module_outputs={},
    )
