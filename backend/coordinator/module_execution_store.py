"""
DesignTrace AI - Coordinator Module Execution Store

Persist Module executions, input/output payloads,
artifact versions and workflow events in Neon.

Mock Modules are used for the PP1 demonstration.
"""

from copy import deepcopy

from sqlalchemy import select

from database.connection import SessionLocal
from database.models import (
    ModuleExecution,
    WorkflowRun,
    ArtifactVersion,
    WorkflowEvent,
)


def save_module_executions(
    thread_id,
    project_state,
    module_execution_inputs=None,
    events=None,
):
    """
    Synchronize LangGraph Module execution records
    with Neon PostgreSQL.

    Repeated calls update existing Module attempts
    instead of intentionally creating new versions.
    """

    if project_state is None:
        return

    if module_execution_inputs is None:
        module_execution_inputs = {}

    with SessionLocal.begin() as session:

        run = session.scalar(
            select(WorkflowRun).where(
                WorkflowRun.thread_id == thread_id
            )
        )

        if run is None:
            raise ValueError(
                f"Workflow not found in Neon: {thread_id}"
            )

        for module_name, module_state in (
            project_state.module_states.items()
        ):

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

                existing = session.scalar(
                    select(ModuleExecution).where(
                        ModuleExecution.workflow_run_id == run.id,
                        ModuleExecution.module_name == module_name,
                        ModuleExecution.attempt_number == version,
                    )
                )

                if existing is None:
                    existing = ModuleExecution(
                        workflow_run_id=run.id,
                        module_name=module_name,
                        attempt_number=version,
                    )
                    session.add(existing)

                # Preserve complete output.
                existing.output_data = deepcopy(output)

                # Preserve exact captured execution input.
                captured_input = (
                    module_execution_inputs
                    .get(module_name, {})
                    .get(str(version))
                )

                if captured_input is not None:
                    existing.input_data = deepcopy(
                        captured_input
                    )

                # Save one artifact for each Module version.
                artifact = session.scalar(
                    select(ArtifactVersion).where(
                        ArtifactVersion.workflow_run_id == run.id,
                        ArtifactVersion.artifact_key == module_name,
                        ArtifactVersion.version_number == version,
                    )
                )

                if artifact is None:
                    artifact = ArtifactVersion(
                        workflow_run_id=run.id,
                        module_name=module_name,
                        artifact_type="module_output",
                        artifact_key=module_name,
                        version_number=version,
                        content=deepcopy(output),
                    )
                    session.add(artifact)
                else:
                    artifact.content = deepcopy(output)

                is_latest = (
                    version == module_state.version
                )

                if is_latest:
                    artifact.approval_status = (
                        module_state.status.value
                    )

                    existing.status = (
                        module_state.status.value
                    )

                    existing.validation_result = {
                        "passed": module_state.validation_passed
                    }

                else:
                    if artifact.approval_status not in (
                        "APPROVED",
                        "REJECTED",
                    ):
                        artifact.approval_status = "SUPERSEDED"

                    if existing.status not in (
                        "APPROVED",
                        "REJECTED",
                    ):
                        existing.status = "SUPERSEDED"

        # Synchronize workflow events.
        if events is not None:

            saved = session.scalars(
                select(WorkflowEvent).where(
                    WorkflowEvent.workflow_run_id == run.id
                )
            ).all()

            indexed = {
                row.event_data.get("event_index"): row
                for row in saved
                if isinstance(row.event_data, dict)
                and isinstance(
                    row.event_data.get("event_index"),
                    int,
                )
            }

            for index, event in enumerate(events):

                row = indexed.get(index)

                if row is None:
                    row = WorkflowEvent(
                        workflow_run_id=run.id
                    )
                    session.add(row)

                row.event_type = str(
                    event.get("event", "UNKNOWN")
                )

                row.module_name = (
                    event.get("module") or None
                )

                row.event_data = {
                    "event_index": index,
                    **deepcopy(event),
                }
