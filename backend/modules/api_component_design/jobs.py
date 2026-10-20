"""Process-local jobs keep slow generation out of HTTP requests."""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Lock
from uuid import uuid4

logger = logging.getLogger(__name__)


class DesignJobs:
    def __init__(self, design):
        self.design = design
        # Serialize access to the shared model/service.
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="api-design")
        self.lock = Lock()
        self.records = {}

    def submit(self, request):
        with self.lock:
            if sum(r["status"] in {"queued", "running"} for r in self.records.values()) >= 4:
                raise ValueError("Generation queue is full. Try again shortly.")
            for key in list(self.records):
                if len(self.records) < 100:
                    break
                if self.records[key]["status"] in {"completed", "failed"}:
                    del self.records[key]
            job_id = uuid4().hex
            record = {"job_id": job_id, "status": "queued", "result": None, "error": None}
            self.records[job_id] = record
            initial = deepcopy(record)
        self.executor.submit(self._run, job_id, request.model_copy(deep=True))
        return initial

    def get(self, job_id):
        with self.lock:
            return deepcopy(self.records.get(job_id))

    def _run(self, job_id, request):
        with self.lock:
            self.records[job_id]["status"] = "running"
        try:
            result = asyncio.run(self.design(request)).model_dump(mode="json")
            with self.lock:
                self.records[job_id].update(status="completed", result=result)
        except Exception as exc:
            logger.error("[API job] failed: %s", type(exc).__name__)
            with self.lock:
                self.records[job_id].update(
                    status="failed", error="API generation failed. Check the backend logs.",
                )
