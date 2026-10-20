from coordinator.module_adapters import build_module_input
from coordinator.dependency_manager import MODULE_DEPENDENCIES
from mocks.mock_modules import execute_mock_module, REQUIREMENTS
from shared.models.project import ProjectInput, Requirement


def test_all_seven_mock_adapters():
    project = ProjectInput(
        project_id="PP1-TEST", project_name="Library",
        project_description="Manage books and members",
        requirements=[Requirement(**item) for item in REQUIREMENTS],
    )
    approved = {}
    for module in MODULE_DEPENDENCIES:
        payload = build_module_input(module, project, approved)
        output = execute_mock_module(module, project, approved, 1, payload)
        assert output["project_id"] == project.project_id
        assert output["mock"] is True
        if module == "requirement_analysis":
            assert output["data"]["input_summary"]["project_id"] == project.project_id
        else:
            assert output["data"]["consumed_upstream_modules"] == sorted(MODULE_DEPENDENCIES[module])
        approved[module] = output
