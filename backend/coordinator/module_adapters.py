"""
DesignTrace AI - Coordinator Module Input Adapters

Routes approved upstream outputs to all seven
PP1 mock Modules.

These are PP1 transport contracts.
They are not a claim that all teammate Modules
already support these exact JSON structures.
"""

from copy import deepcopy

from coordinator.dependency_manager import MODULE_DEPENDENCIES


def build_requirement_analysis_input(project):
    description = (
        project.project_description or ""
    ).strip()

    if not description:
        raise ValueError(
            "Requirement Analysis needs a project description."
        )

    return {
        "project_id": project.project_id,
        "raw_description": description,
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
    if module_name == "requirement_analysis":
        return build_requirement_analysis_input(project)

    if module_name not in MODULE_DEPENDENCIES:
        raise ValueError(
            f"Unknown Module: {module_name}"
        )

    dependencies = MODULE_DEPENDENCIES[module_name]

    missing = [
        name
        for name in dependencies
        if name not in approved_outputs
    ]

    if missing:
        raise ValueError(
            f"{module_name}: missing approved inputs: {missing}"
        )

    upstream = {
        name: deepcopy(approved_outputs[name])
        for name in dependencies
    }

    payload = {
        "project_id": project.project_id,
        "module_name": module_name,
        "execution_mode": "MOCK_PP1",
        "approved_upstream_outputs": upstream,
    }

    if "requirement_analysis" in upstream:
        payload["requirements_output"] = deepcopy(
            upstream["requirement_analysis"]
        )

    if "architecture_design" in upstream:
        payload["architecture_output"] = deepcopy(
            upstream["architecture_design"]
        )

    if "database_design" in upstream:
        payload["database_output"] = deepcopy(
            upstream["database_design"]
        )

    if "api_component_design" in upstream:
        payload["api_component_output"] = deepcopy(
            upstream["api_component_design"]
        )

    if "quality_evaluation" in upstream:
        payload["quality_output"] = deepcopy(
            upstream["quality_evaluation"]
        )

    return payload
