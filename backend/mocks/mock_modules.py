"""
DesignTrace AI - PP1 Mock Module Outputs

These are simulated outputs, NOT real AI-generated results.
All Modules use the same Library Management requirements.
"""

from copy import deepcopy

REQUIREMENTS = [
    {
        "requirement_id": "REQ-001",
        "requirement_text": "The system shall store book details.",
    },
    {
        "requirement_id": "REQ-002",
        "requirement_text": "Members shall borrow books.",
    },
    {
        "requirement_id": "REQ-003",
        "requirement_text": (
            "Each borrowing record shall reference "
            "a book and a member."
        ),
    },
]

MOCK_OUTPUTS = {
    "requirement_analysis": {
        "requirements": [
            {"id": "REQ-001", "type": "FR", "priority": "HIGH"},
            {"id": "REQ-002", "type": "FR", "priority": "HIGH"},
            {"id": "REQ-003", "type": "FR", "priority": "HIGH"},
        ],
        "summary": "Three functional requirements identified.",
    },

    "architecture_design": {
        "architecture_style": "Layered Architecture",
        "database_type": "PostgreSQL",
        "constraints": [
            "Use relational database tables",
            "Enforce foreign key relationships",
        ],
        "components": [
            "Presentation Layer",
            "Business Layer",
            "Data Access Layer",
        ],
    },

    "database_design": {
        "tables": [
            {"name": "books", "primary_key": "book_id"},
            {"name": "members", "primary_key": "member_id"},
            {
                "name": "borrowing_records",
                "primary_key": "borrowing_id",
            },
        ],
        "relationships": [
            {
                "from": "books",
                "to": "borrowing_records",
                "foreign_key": "book_id",
            },
            {
                "from": "members",
                "to": "borrowing_records",
                "foreign_key": "member_id",
            },
        ],
        "requirement_mappings": {
            "REQ-001": ["books"],
            "REQ-002": ["borrowing_records"],
            "REQ-003": [
                "borrowing_records",
                "books",
                "members",
            ],
        },
    },

    "api_component_design": {
        "components": [
            "BookService",
            "MemberService",
            "BorrowingService",
        ],
        "endpoints": [
            {"method": "GET", "path": "/books"},
            {"method": "POST", "path": "/borrowings"},
            {"method": "GET", "path": "/members"},
        ],
    },

    "traceability": {
        "mappings": [
            {
                "requirement_id": "REQ-001",
                "database": ["books"],
                "component": "BookService",
                "endpoint": "GET /books",
            },
            {
                "requirement_id": "REQ-002",
                "database": ["borrowing_records"],
                "component": "BorrowingService",
                "endpoint": "POST /borrowings",
            },
            {
                "requirement_id": "REQ-003",
                "database": ["books", "members", "borrowing_records"],
                "component": "BorrowingService",
                "endpoint": "POST /borrowings",
            },
        ],
    },

    "quality_evaluation": {
        "mock_scores": {
            "requirement_coverage_percent": 100,
            "structural_consistency_percent": 100,
        },
        "findings": [
            "All three mock requirements have design mappings.",
            "Database relationships match the mock architecture.",
        ],
        "note": "Illustrative scores, not measured research results.",
    },

    "adr": {
        "records": [
            {
                "id": "ADR-001",
                "decision": "Use PostgreSQL",
                "reason": "Relational integrity requirements",
            },
            {
                "id": "ADR-002",
                "decision": "Use Layered Architecture",
                "reason": "Separation of responsibilities",
            },
        ],
    },
}


def execute_mock_module(
    module_name,
    project,
    approved_outputs,
    version=1,
    module_input=None,
):
    """
    Simulate Module execution for PP1.

    Requirement Analysis consumes its structured
    Coordinator input adapter.

    Other Modules continue using mock outputs until
    their contracts are integrated.
    """

    if module_name not in MOCK_OUTPUTS:
        raise ValueError(
            f"Unknown mock Module: {module_name}"
        )

    output = deepcopy(MOCK_OUTPUTS[module_name])

    # Phase 3C: Consume Requirement Analysis input.
    if module_name == "requirement_analysis":

        if not isinstance(module_input, dict):
            raise ValueError(
                "Requirement Analysis input must be a dictionary."
            )

        required_fields = (
            "project_id",
            "raw_description",
            "project_context",
        )

        for field in required_fields:
            if field not in module_input:
                raise ValueError(
                    f"Requirement Analysis input missing: {field}"
                )

        if module_input["project_id"] != project.project_id:
            raise ValueError(
                "Requirement Analysis project ID mismatch."
            )

        description = module_input["raw_description"]

        if (
            not isinstance(description, str)
            or not description.strip()
        ):
            raise ValueError(
                "Requirement Analysis description is required."
            )

        if not isinstance(
            module_input["project_context"], dict
        ):
            raise ValueError(
                "Requirement Analysis project_context must be a dictionary."
            )

        # The mock still returns fixed demonstration
        # requirements. It is not real AI extraction.
        output["input_summary"] = {
            "project_id": module_input["project_id"],
            "description_received": description,
            "project_context_received": deepcopy(
                module_input["project_context"]
            ),
        }

    # Demonstrate feedback and retry.
    # First database version intentionally lacks
    # one relationship.
    if module_name == "database_design" and version == 1:
        output["relationships"] = (
            output["relationships"][:1]
        )

    return {
        "project_id": project.project_id,
        "module_name": module_name,
        "version": version,
        "mock": True,
        "source_requirements": [
            req.requirement_id
            for req in project.requirements
        ],
        "input_artifacts": sorted(
            approved_outputs.keys()
        ),
        "data": output,
    }
