"""
Persistent Architecture Decision Record repository.

The repository keeps ADRs available in memory during application
execution and can optionally persist them as JSON files on disk.

Persistence is enabled when a storage directory is supplied.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from modules.adr.schemas import (
    ADRRecord,
    ADRStatus,
)


class ADRRepository:
    """
    Stores ADRs and manages their lifecycle.

    When ``storage_dir`` is supplied, ADRs are persisted to disk and
    automatically restored when the repository is created again.
    """

    ALLOWED_TRANSITIONS = {
        ADRStatus.PROPOSED: {
            ADRStatus.ACCEPTED,
            ADRStatus.DEPRECATED,
        },
        ADRStatus.ACCEPTED: {
            ADRStatus.SUPERSEDED,
            ADRStatus.DEPRECATED,
        },
        ADRStatus.SUPERSEDED: set(),
        ADRStatus.DEPRECATED: set(),
    }

    def __init__(
        self,
        storage_dir: str | Path | None = None,
    ):
        self._records: dict[str, ADRRecord] = {}

        self.storage_dir = (
            Path(storage_dir)
            if storage_dir is not None
            else None
        )

        if self.storage_dir is not None:
            self.storage_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            self._load_existing_records()

    # ------------------------------------------------------------------
    # Basic repository operations
    # ------------------------------------------------------------------

    def save(
        self,
        adr: ADRRecord,
    ) -> ADRRecord:
        """
        Store a new ADR.

        Duplicate ADR identifiers are rejected.
        """

        if adr.adr_id in self._records:
            raise ValueError(
                f"ADR '{adr.adr_id}' already exists."
            )

        self._records[adr.adr_id] = adr

        self._persist(
            adr
        )

        return adr

    def get(
        self,
        adr_id: str,
    ) -> ADRRecord:
        """
        Retrieve one ADR by its identifier.
        """

        if adr_id not in self._records:
            raise KeyError(
                f"ADR '{adr_id}' was not found."
            )

        return self._records[adr_id]

    def list_by_project(
        self,
        project_id: str,
    ) -> list[ADRRecord]:
        """
        Return all ADRs belonging to a project.
        """

        return [
            adr
            for adr in self._records.values()
            if adr.project_id == project_id
        ]

    def find_by_source_decision_id(
        self,
        decision_id: str,
    ) -> ADRRecord | None:
        """
        Find the ADR created from a particular source decision.
        """

        for adr in self._records.values():
            if (
                decision_id
                in adr.traceability.source_decision_ids
            ):
                return adr

        return None

    # ------------------------------------------------------------------
    # Lifecycle management
    # ------------------------------------------------------------------

    def change_status(
        self,
        adr_id: str,
        new_status: ADRStatus,
    ) -> ADRRecord:
        """
        Change an ADR lifecycle status using controlled transitions.
        """

        adr = self.get(
            adr_id
        )

        if new_status == adr.status:
            return adr

        allowed = self.ALLOWED_TRANSITIONS.get(
            adr.status,
            set(),
        )

        if new_status not in allowed:
            raise ValueError(
                "Invalid ADR lifecycle transition: "
                f"{adr.status.value} -> "
                f"{new_status.value}"
            )

        updated_adr = adr.model_copy(
            update={
                "status": new_status,
                "updated_at": datetime.now(
                    timezone.utc
                ),
            }
        )

        self._records[adr_id] = updated_adr

        self._persist(
            updated_adr
        )

        return updated_adr

    def supersede(
        self,
        old_adr_id: str,
        new_adr_id: str,
    ) -> tuple[ADRRecord, ADRRecord]:
        """
        Mark one accepted ADR as superseded by another ADR.
        """

        if old_adr_id == new_adr_id:
            raise ValueError(
                "An ADR cannot supersede itself."
            )

        old_adr = self.get(
            old_adr_id
        )

        new_adr = self.get(
            new_adr_id
        )

        if (
            old_adr.project_id
            != new_adr.project_id
        ):
            raise ValueError(
                "ADRs from different projects "
                "cannot supersede each other."
            )

        if old_adr.status != ADRStatus.ACCEPTED:
            raise ValueError(
                "Only an accepted ADR can be superseded."
            )

        now = datetime.now(
            timezone.utc
        )

        updated_old = old_adr.model_copy(
            update={
                "status": ADRStatus.SUPERSEDED,
                "superseded_by": new_adr_id,
                "updated_at": now,
            }
        )

        updated_new = new_adr.model_copy(
            update={
                "supersedes": old_adr_id,
                "updated_at": now,
            }
        )

        self._records[
            old_adr_id
        ] = updated_old

        self._records[
            new_adr_id
        ] = updated_new

        self._persist(
            updated_old
        )

        self._persist(
            updated_new
        )

        return (
            updated_old,
            updated_new,
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist(
        self,
        adr: ADRRecord,
    ) -> None:
        """
        Persist an ADR as a formatted JSON document.

        No file is written when the repository is operating in
        memory-only mode.
        """

        if self.storage_dir is None:
            return

        project_directory = (
            self.storage_dir
            / adr.project_id
        )

        project_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        adr_file = (
            project_directory
            / f"{adr.adr_id}.json"
        )

        temporary_file = adr_file.with_suffix(
            ".json.tmp"
        )

        data = adr.model_dump(
            mode="json"
        )

        with temporary_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

        temporary_file.replace(
            adr_file
        )

    def _load_existing_records(
        self,
    ) -> None:
        """
        Restore previously persisted ADRs into memory.
        """

        if self.storage_dir is None:
            return

        for adr_file in self.storage_dir.rglob(
            "*.json"
        ):
            try:
                content = adr_file.read_text(
                    encoding="utf-8"
                )

                adr = ADRRecord.model_validate_json(
                    content
                )

                self._records[
                    adr.adr_id
                ] = adr

            except Exception as exc:
                raise ValueError(
                    "Failed to load ADR repository file "
                    f"'{adr_file}': {exc}"
                ) from exc