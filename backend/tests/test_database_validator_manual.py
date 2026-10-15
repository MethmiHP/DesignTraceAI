"""
DesignTrace AI - Manual Database Validator Test
================================================

Purpose:
    Test the Database Design Module and its rule-based validator.

Steps:
    1. Create a sample project.
    2. Generate a mock database design.
    3. Validate primary keys and foreign keys.
    4. Print the validation result.
"""

from shared.models.project import ProjectInput

from modules.database_design.database_module import generate_database_design

from modules.database_design.validator import validate_database_design


def main():
    # Step 1: Create a sample project.
    project = ProjectInput(
        project_id="P001",
        project_name="Hospital Management System",
        project_description="Hospital appointment system.",
    )

    # Step 2: Generate the sample database design.
    design = generate_database_design(project)

    # Step 3: Validate the generated design.
    validation = validate_database_design(design)

    # Step 4: Display the validation result.
    print(validation.model_dump_json(indent=2))


if __name__ == "__main__":
    main()