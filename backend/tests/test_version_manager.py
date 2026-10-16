from coordinator.state_manager import (
    create_initial_project_state,
)
from coordinator.version_manager import (
    save_module_output_version,
    get_module_output_history,
    get_module_output_version,
)
from shared.models.project import ProjectInput


def create_state():
    project = ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment system.",
    )

    return create_initial_project_state(project)


def test_first_version_saved():
    state = create_state()

    save_module_output_version(
        state,
        "database_design",
        {"tables": ["patients"]},
    )

    assert state.module_states[
        "database_design"
    ].version == 1

    assert len(
        get_module_output_history(
            state, "database_design"
        )
    ) == 1


def test_second_version_preserves_first():
    state = create_state()

    save_module_output_version(
        state,
        "database_design",
        {"tables": ["patients"]},
    )

    save_module_output_version(
        state,
        "database_design",
        {"tables": ["patients", "doctors"]},
    )

    first = get_module_output_version(
        state, "database_design", 1
    )

    second = get_module_output_version(
        state, "database_design", 2
    )

    assert first["output"]["tables"] == ["patients"]

    assert second["output"]["tables"] == [
        "patients",
        "doctors",
    ]

    assert state.module_states[
        "database_design"
    ].version == 2


def test_latest_output_updated():
    state = create_state()

    save_module_output_version(
        state,
        "database_design",
        {"tables": ["patients"]},
    )

    save_module_output_version(
        state,
        "database_design",
        {"tables": ["patients", "appointments"]},
    )

    assert state.module_outputs[
        "database_design"
    ]["tables"] == [
        "patients",
        "appointments",
    ]
