"""
Tests for Coordinator dependency management.

These tests verify an important DesignTrace AI rule:

A downstream Module must not execute until all required upstream
outputs have been approved.
"""

from coordinator.dependency_manager import check_dependencies
from shared.models.workflow import ModuleState, WorkflowStatus


def test_database_allowed_when_dependencies_approved():

    states = {
        "requirement_analysis": ModuleState(
            module_name="requirement_analysis",
            status=WorkflowStatus.APPROVED,
        ),

        "architecture_design": ModuleState(
            module_name="architecture_design",
            status=WorkflowStatus.APPROVED,
        ),
    }

    allowed, problems = check_dependencies(
        "database_design",
        states,
    )

    assert allowed is True
    assert problems == []


def test_database_blocked_when_architecture_not_approved():

    states = {
        "requirement_analysis": ModuleState(
            module_name="requirement_analysis",
            status=WorkflowStatus.APPROVED,
        ),

        "architecture_design": ModuleState(
            module_name="architecture_design",
            status=WorkflowStatus.REVIEW_REQUIRED,
        ),
    }

    allowed, problems = check_dependencies(
        "database_design",
        states,
    )

    assert allowed is False

    assert "architecture_design" in problems

def test_adr_requires_all_six_modules():
    dependencies = [
        "requirement_analysis",
        "architecture_design",
        "database_design",
        "api_component_design",
        "traceability",
        "quality_evaluation",
    ]

    states = {
        name: ModuleState(
            module_name=name,
            status=WorkflowStatus.APPROVED,
        )
        for name in dependencies
    }

    allowed, missing = check_dependencies("adr", states)

    assert allowed is True
    assert missing == []

    states["quality_evaluation"].status = (
        WorkflowStatus.REVIEW_REQUIRED
    )

    allowed, missing = check_dependencies("adr", states)

    assert allowed is False
    assert "quality_evaluation" in missing