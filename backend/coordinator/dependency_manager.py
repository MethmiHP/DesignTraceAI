"""
DesignTrace AI - Coordinator Dependency Manager
================================================

Purpose:
    This file manages dependencies between the Modules in DesignTrace AI.

What happens here:
    Some Modules cannot run until outputs from earlier Modules have
    been approved.

    Example:

        Requirement Analysis Module
                    ↓
               APPROVED

        Architecture Design Module
                    ↓
               APPROVED

                    ↓
        Database Design Module
             CAN EXECUTE

    If one required dependency is not approved:

        Requirement Analysis = APPROVED
        Architecture Design  = REVIEW_REQUIRED

                    ↓
        Database Design Module
               IS BLOCKED

Why this is important:
    The Coordinator Agent must prevent Modules from running with
    incomplete, missing, failed, or unapproved upstream information.

Important rule:
    Only APPROVED dependencies are considered valid for downstream
    execution.
"""

from shared.models.workflow import ModuleState, WorkflowStatus


# -------------------------------------------------------------------
# MODULE DEPENDENCY DEFINITIONS
# -------------------------------------------------------------------
#
# Each key represents a Module.
# The list represents the Modules that must be APPROVED before
# that Module is allowed to execute.
#

MODULE_DEPENDENCIES = {

    "requirement_analysis": [],

    "architecture_design": [
        "requirement_analysis"
    ],

    "database_design": [
        "requirement_analysis",
        "architecture_design"
    ],

    "api_component_design": [
        "requirement_analysis",
        "architecture_design",
        "database_design"
    ],

    "traceability": [
        "requirement_analysis",
        "architecture_design",
        "database_design",
        "api_component_design"
    ],

    "quality_evaluation": [
        "requirement_analysis",
        "architecture_design",
        "database_design",
        "api_component_design"
    ],

    "adr": [
        "requirement_analysis",
        "architecture_design",
        "database_design",
        "api_component_design",
        "traceability",
        "quality_evaluation"
    ]
}


def check_dependencies(
    module_name: str,
    module_states: dict[str, ModuleState]
) -> tuple[bool, list[str]]:
    """
    Check whether all dependencies required by a Module are APPROVED.

    Parameters
    ----------
    module_name:
        Name of the Module that wants to execute.

        Example:
            "database_design"

    module_states:
        Current state of all Modules maintained by the Coordinator.

    Returns
    -------
    tuple[bool, list[str]]

    Example when dependencies are ready:

        (True, [])

    Example when architecture is not approved:

        (False, ["architecture_design"])
    """

    # Get the dependencies required by this Module.
    required_dependencies = MODULE_DEPENDENCIES.get(
        module_name,
        []
    )

    # Store dependencies that are missing or not approved.
    unavailable_dependencies = []

    for dependency_name in required_dependencies:

        # Try to find the current state of this dependency.
        dependency_state = module_states.get(
            dependency_name
        )

        # -----------------------------------------------------------
        # CASE 1:
        # Dependency does not exist in the Coordinator state.
        # -----------------------------------------------------------
        if dependency_state is None:

            unavailable_dependencies.append(
                dependency_name
            )

            continue

        # -----------------------------------------------------------
        # CASE 2:
        # Dependency exists but has not been APPROVED.
        # -----------------------------------------------------------
        if dependency_state.status != WorkflowStatus.APPROVED:

            unavailable_dependencies.append(
                dependency_name
            )

    # ---------------------------------------------------------------
    # If the list is empty, every dependency is approved.
    # ---------------------------------------------------------------
    dependencies_ready = (
        len(unavailable_dependencies) == 0
    )

    return (
        dependencies_ready,
        unavailable_dependencies
    )