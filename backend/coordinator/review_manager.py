"""
DesignTrace AI - Human Review Manager

The Coordinator Agent manages approval,
retry requests, and human feedback.

Only approved outputs can be used
by dependent Modules.
"""

from coordinator.state_manager import ProjectState
from shared.models.workflow import WorkflowStatus


def request_human_review(
    state: ProjectState,
    module_name: str,
) -> ProjectState:
    """Mark a validated Module output for human review."""

    module = state.module_states[module_name]

    if not module.validation_passed:
        raise ValueError(
            "Cannot request approval for an invalid output."
        )

    if module.status not in (
        WorkflowStatus.RUNNING,
        WorkflowStatus.RETRYING,
    ):
        raise ValueError(
            "Module must be running or retrying."
        )

    if module_name not in state.module_outputs:
        raise ValueError(
            "No generated output available for review."
        )

    module.status = WorkflowStatus.REVIEW_REQUIRED

    return state


def approve_module_output(
    state: ProjectState,
    module_name: str,
) -> ProjectState:
    """Approve a validated Module output."""

    module = state.module_states[module_name]

    if module.status != WorkflowStatus.REVIEW_REQUIRED:
        raise ValueError(
            "Module is not waiting for human review."
        )

    if not module.validation_passed:
        raise ValueError(
            "Cannot approve an invalid output."
        )

    if module_name not in state.module_outputs:
        raise ValueError(
            "No output available for approval."
        )

    module.status = WorkflowStatus.APPROVED

    return state


def request_module_retry(
    state: ProjectState,
    module_name: str,
    feedback: str = "",
    max_retries: int = 3,
) -> ProjectState:
    """Request regeneration of a Module output."""

    module = state.module_states[module_name]

    if module.status != WorkflowStatus.REVIEW_REQUIRED:
        raise ValueError(
            "Retry is only allowed during human review."
        )

    if feedback.strip():
        module.human_feedback.append(feedback.strip())

    if module.retry_count >= max_retries:
        module.status = WorkflowStatus.FAILED
        return state

    module.retry_count += 1
    module.status = WorkflowStatus.RETRYING
    module.validation_passed = False

    # Keep previous output as a draft.
    # It must not be passed downstream.

    return state
