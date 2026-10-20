"""
DesignTrace AI - Coordinator Module Execution Store

Phase 3A and Phase 3B:
- Persist Module execution records in Neon PostgreSQL.
- Store complete Module outputs.
- Store Module inputs captured during execution.
- Store validation results and Module status.
- Preserve separate records for retry versions.
- Avoid duplicate records for the same Module attempt.

This implementation supports mock Modules for PP1.
"""

from copy import deepcopy

from sqlalchemy import select

from database.connection import SessionLocal
from database.models import ModuleExecution, WorkflowRun


def save_module_executions(
    thread_id,
    project_state,
    module_execution_inputs=None,
):
    """
    Synchronize Module execution records from LangGraph
    state into Neon PostgreSQL.

    Args:
        thread_id:
            LangGraph workflow thread ID.

        project_state:
            Coordinator ProjectState containing Module
            states, outputs and output history.

        module_execution_inputs:
            Dictionary of Module input payloads captured
            at execution time.

            Expected structure:
            {
                "requirement_analysis": {
                    "1": {...}
                },
                "architecture_design": {
                    "1": {...}
                }
            }

    Existing records are updated rather than duplicated.
    """

    if project_state is None:
        return

    if module_execution_inputs is None:
        module_execution_inputs = {}

    with SessionLocal.begin() as session:

        # Find the workflow in Neon.
        run = session.scalar(
            select(WorkflowRun).where(
                WorkflowRun.thread_id == thread_id
            )
        )

        if run is None:
            raise ValueError(
                f"Workflow not found in Neon: {thread_id}"
            )

        # Process each Module in the Coordinator state.
        for module_name, module_state in (
            project_state.module_states.items()
        ):

            # Retrieve all saved output versions.
            history = (
                project_state.module_output_history.get(
                    module_name,
                    [],
                )
            )

            if not history:
                continue

            for output in history:

                version = output.get("version")

                if not isinstance(version, int):
                    continue

                # Check whether this Module attempt
                # already exists in Neon.
                existing = session.scalar(
                    select(ModuleExecution).where(
                        ModuleExecution.workflow_run_id
                        == run.id,
                        ModuleExecution.module_name
                        == module_name,
                        ModuleExecution.attempt_number
                        == version,
                    )
                )

                # Create a new record if necessary.
                if existing is None:
                    existing = ModuleExecution(
                        workflow_run_id=run.id,
                        module_name=module_name,
                        attempt_number=version,
                    )

                    session.add(existing)

                # Save the complete Module output.
                existing.output_data = deepcopy(output)

                # Get the input captured at execution time.
                # This is outside any dependency loop.
                captured_input = (
                    module_execution_inputs
                    .get(module_name, {})
                    .get(str(version))
                )

                # Save the input only when available.
                # Older checkpoints may not contain it.
                if captured_input is not None:
                    existing.input_data = deepcopy(
                        captured_input
                    )

                # Check whether this is the current
                # version of the Module.
                is_latest = (
                    version == module_state.version
                )

                if is_latest:

                    # Save the current Module status.
                    existing.status = (
                        module_state.status.value
                    )

                    # Save the validation result.
                    existing.validation_result = {
                        "passed": (
                            module_state.validation_passed
                        )
                    }

                else:

                    # Preserve finalized decisions for
                    # historical Module versions.
                    if existing.status not in (
                        "APPROVED",
                        "REJECTED",
                    ):
                        existing.status = "SUPERSEDED"
