"""
DesignTrace AI - Module Output Version Manager

Stores versioned Module outputs in the
Coordinator's shared project state.
"""

from copy import deepcopy

from coordinator.state_manager import ProjectState


def save_module_output_version(
    state: ProjectState,
    module_name: str,
    output: dict,
) -> ProjectState:
    """
    Save a new output version without deleting
    previous versions.
    """

    if module_name not in state.module_states:
        raise ValueError(
            f"Unknown Module: {module_name}"
        )

    module = state.module_states[module_name]

    # Create history when saving the first version.
    if module_name not in state.module_output_history:
        state.module_output_history[module_name] = []

    # Version number is based on saved history.
    version = len(
        state.module_output_history[module_name]
    ) + 1

    version_record = {
        "version": version,
        "output": deepcopy(output),
        "status": "DRAFT",
    }

    state.module_output_history[module_name].append(
        version_record
    )

    # Keep the latest output available.
    state.module_outputs[module_name] = deepcopy(output)

    module.version = version

    return state


def get_module_output_history(
    state: ProjectState,
    module_name: str,
) -> list[dict]:
    """Return all saved versions for one Module."""

    return deepcopy(
        state.module_output_history.get(module_name, [])
    )


def get_module_output_version(
    state: ProjectState,
    module_name: str,
    version: int,
) -> dict | None:
    """Retrieve a particular saved version."""

    history = state.module_output_history.get(
        module_name, []
    )

    for record in history:
        if record["version"] == version:
            return deepcopy(record)

    return None
