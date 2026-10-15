from shared.models.project import ProjectInput

from coordinator.database_integration import (
    prepare_database_design,
)


def test_database_integration():
    project = ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment system.",
    )

    result = prepare_database_design(project)

    assert result["project_id"] == "P001"
    assert result["module_name"] == "database_design"
    assert result["status"] == "REVIEW_REQUIRED"

    assert result["artifacts"]["validation_report"]["passed"]
    assert result["artifacts"]["er_diagram"] is not None
    assert result["artifacts"]["sql_schema"] is not None
