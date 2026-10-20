"""
Module input adapters for DesignTrace AI.

Phase 3B:
Build structured inputs from Coordinator project state.
Other Module adapters will be added as contracts are finalized.
"""

from copy import deepcopy


def build_requirement_analysis_input(project):
    """
    Build the documented Requirement Analysis input.

    This adapter does not execute the Module.
    """
    raw_description = (
        project.project_description or ""
    ).strip()

    if not raw_description:
        raise ValueError(
            "Requirement Analysis needs a project description."
        )

    return {
        "project_id": project.project_id,
        "raw_description": raw_description,
        "project_context": {
            "project_name": project.project_name,
            "domain": "",
            "system_type": "",
            "primary_users": [],
            "constraints": [],
            "technology_preferences": [],
        },
    }


def build_module_input(
    module_name,
    project,
    approved_outputs,
):
    """
    Create the exact input envelope passed to the
    Coordinator's mock execution boundary.

    The Requirement Analysis input follows its
    documented contract. Other Modules temporarily
    use a generic mock envelope.
    """
    if module_name == "requirement_analysis":
        return build_requirement_analysis_input(project)

    return {
        "project_id": project.project_id,
        "module_name": module_name,
        "project": project.model_dump(mode="json"),
        "approved_outputs": deepcopy(approved_outputs),
        "adapter_status": "MOCK_CONTRACT_PENDING",
    }
