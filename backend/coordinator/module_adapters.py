from copy import deepcopy

from coordinator.dependency_manager import MODULE_DEPENDENCIES


def build_requirement_analysis_input(project):
    description = (
        project.project_description or ""
    ).strip()

    if not description:
        raise ValueError(
            "Project description is required."
        )

    return {
        "project_id": project.project_id,
        "raw_description": description,
        "project_context": {
            "project_name": project.project_name,
            "domain": "Library Management",
            "system_type": "Web Application",
            "primary_users": [
                "Librarian",
                "Library Member",
            ],
            "constraints": [
                "Maintain relational integrity",
                "Track book borrowing records",
            ],
            "technology_preferences": [
                "PostgreSQL",
            ],
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

    required = MODULE_DEPENDENCIES[module_name]

    missing = [
        name
        for name in required
        if name not in approved_outputs
    ]

    if missing:
        raise ValueError(
            f"{module_name}: missing approved inputs: {missing}"
        )

    upstream = {
        name: deepcopy(approved_outputs[name])
        for name in required
    }

    # Keep the existing transport contract for PP1.
    payload = {
        "project_id": project.project_id,
        "module_name": module_name,
        "execution_mode": "MOCK_PP1",
        "approved_upstream_outputs": upstream,
    }

    # Add convenient named inputs without removing
    # the original approved_upstream_outputs field.
    field_names = {
        "requirement_analysis": "requirements_output",
        "architecture_design": "architecture_output",
        "database_design": "database_output",
        "api_component_design": "api_component_output",
        "traceability": "traceability_output",
        "quality_evaluation": "quality_output",
        "adr": "adr_output",
    }

    for name, output in upstream.items():
        payload[field_names[name]] = deepcopy(output)

    return payload
