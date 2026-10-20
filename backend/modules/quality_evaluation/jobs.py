"""Bounded, process-local background evaluations for the interactive frontend."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Lock
from uuid import uuid4
import logging

from .output_store import save_report
from .service import QualityEvaluationService

logger = logging.getLogger(__name__)


class QueueFullError(Exception):
    pass


class EvaluationJobs:
    def __init__(self, workers=2, capacity=4, retention=100, service_factory=QualityEvaluationService):
        self.executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='quality')
        self.capacity = capacity
        self.retention = retention
        self.service_factory = service_factory
        self.lock = Lock()
        self.jobs = {}

    def submit(self, request):
        with self.lock:
            active = sum(j['status'] in {'queued', 'running'} for j in self.jobs.values())
            if active >= self.capacity:
                raise QueueFullError('Evaluation queue is full. Please retry after a running evaluation finishes.')
            for key in list(self.jobs):
                if len(self.jobs) < self.retention:
                    break
                if self.jobs[key]['status'] in {'completed', 'failed'}:
                    del self.jobs[key]
            job_id = uuid4().hex
            self.jobs[job_id] = {
                'job_id': job_id, 'project_id': request.project_id,
                'status': 'queued', 'completed_rules': 0, 'total_rules': 0,
                'current_rule': None, 'result': None, 'error': None,
            }
            initial = deepcopy(self.jobs[job_id])
        self.executor.submit(self._run, job_id, request.model_copy(deep=True))
        return initial

    def get(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            return deepcopy(job) if job else None

    def _update(self, job_id, **changes):
        with self.lock:
            self.jobs[job_id].update(changes)

    def _run(self, job_id, request):
        self._update(job_id, status='running')
        try:
            # Each job owns its provider state, including fallback attribution.
            service = self.service_factory()
            result = service.evaluate(request, on_progress=lambda completed, total, current:
                self._update(job_id, completed_rules=completed, total_rules=total, current_rule=current))
            save_report(result)
            self._update(job_id, status='completed', current_rule=None, result=result.model_dump(mode='json'))
        except Exception:
            logger.exception('Quality evaluation job %s failed', job_id)
            self._update(job_id, status='failed', current_rule=None,
                         error='Evaluation or report saving failed. Check the backend logs and retry.')
