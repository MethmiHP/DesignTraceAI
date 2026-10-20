import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from database.connection import Base


def new_uuid():
    return uuid.uuid4()


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=new_uuid,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Original user input and context.
    input_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="created",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=new_uuid,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id"),
        nullable=False,
    )

    # Used to find the corresponding LangGraph checkpoint.
    thread_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )

    current_module: Mapped[str | None] = mapped_column(
        String(100),
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )


class ModuleExecution(Base):
    __tablename__ = "module_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=new_uuid,
    )

    workflow_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id"),
        nullable=False,
    )

    module_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    attempt_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )

    input_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
    )

    output_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
    )

    validation_result: Mapped[dict[str, Any] | None] = (
        mapped_column(JSONB)
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )


class ArtifactVersion(Base):
    __tablename__ = "artifact_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=new_uuid,
    )

    workflow_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id"),
        nullable=False,
    )

    module_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    artifact_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    artifact_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )

    approval_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        Index(
            "uq_artifact_version",
            "workflow_run_id",
            "artifact_key",
            "version_number",
            unique=True,
        ),
    )


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=new_uuid,
    )

    workflow_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id"),
        nullable=False,
    )

    artifact_version_id: Mapped[uuid.UUID | None] = (
        mapped_column(
            UUID(as_uuid=True),
            ForeignKey("artifact_versions.id"),
        )
    )

    module_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    feedback: Mapped[str | None] = mapped_column(
        Text,
    )

    reviewer: Mapped[str | None] = mapped_column(
        String(255),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=new_uuid,
    )

    workflow_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id"),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    module_name: Mapped[str | None] = mapped_column(
        String(100),
    )

    event_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
