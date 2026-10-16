"""
DesignTrace AI - Workflow Models
================================

Purpose:
    This file defines the workflow states used by the Coordinator Agent.

What happens here:
    Every Module in DesignTrace AI has a current status.

    Example:
        Database Design Module
            PENDING
                ↓
            RUNNING
                ↓
            REVIEW_REQUIRED
                ↓
            APPROVED

    If a problem occurs:
        RUNNING
            ↓
        RETRYING

    If recovery is unsuccessful:
        FAILED

Why the Coordinator needs this:
    The Coordinator Agent uses these statuses to decide:
        - whether a Module can execute
        - whether an output requires human review
        - whether an output has been approved
        - whether execution should be retried
        - whether the workflow should stop because of failure

Important:
    Only APPROVED outputs should be passed to dependent Modules.
"""

from enum import Enum
from pydantic import BaseModel, Field
from shared.models.project import ProjectInput


class WorkflowStatus(str, Enum):
    """
    Defines all possible states of a DesignTrace AI Module.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"


class ModuleState(BaseModel):
    """
    Stores the current workflow information for one Module.

    Example:
        Database Design Module:
            status = REVIEW_REQUIRED
            version = 1
            retry_count = 0
            validation_passed = True
    """

    # Name of the Module.
    module_name: str

    # Current workflow status.
    status: WorkflowStatus = WorkflowStatus.PENDING

    # Current output version.
    # 0 means no output has been generated yet.
    version: int = 0

    # Number of retry attempts.
    retry_count: int = 0

    # Whether automatic output validation was successful.
    validation_passed: bool = False

    # Stores feedback provided during human review.
    human_feedback: list[str] = Field(default_factory=list)

    
class ProjectState(BaseModel):
    """
    Stores the shared workflow state for one project.

    The Coordinator Agent uses this to track:
    - Project information
    - Module statuses
    - Generated module outputs
    """

    # Basic project information.
    project: "ProjectInput"

    # Current state of each Module.
    module_states: dict[str, ModuleState] = Field(
        default_factory=dict
    )

    # Generated outputs from Modules.
    module_outputs: dict[str, dict] = Field(
        default_factory=dict
    )
