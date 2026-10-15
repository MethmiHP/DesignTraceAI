"""Persist process artifacts under backend/outputs, independently of the cwd."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs"


def save_outputs(project_id: str, artifacts: dict) -> Path:
    """Write a complete, unique run directory; never publish partial JSON files.

    Serialization and filesystem failures propagate to the caller so a run is
    not reported as successfully saved when persistence failed.
    """
    project = re.sub(r"[^A-Za-z0-9_-]+", "-", project_id).strip("-")[:80]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_name = f"{project or 'project'}_{timestamp}_{uuid4().hex}"
    destination = DEFAULT_OUTPUT_DIR / run_name

    # Serialize first, before creating any files.
    documents = {}
    for name, value in artifacts.items():
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            raise ValueError(f"Invalid artifact name: {name!r}")
        documents[name] = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)

    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".pending-", dir=DEFAULT_OUTPUT_DIR) as temporary:
        staging = Path(temporary)
        for name, document in documents.items():
            (staging / f"{name}.json").write_text(document + "\n", encoding="utf-8")
        staging.rename(destination)

    return destination
