from threading import Event
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.quality_evaluation import router, jobs as jobs_module, output_store
from modules.quality_evaluation.jobs import EvaluationJobs
from modules.quality_evaluation.service import QualityEvaluationService
from test_quality_service_integration import build_request


def test_job_returns_before_evaluation_finishes_and_saves_result(tmp_path, monkeypatch):
    entered, release = Event(), Event()
    class SlowService:
        def evaluate(self, request, on_progress):
            on_progress(0, 6, 'SEC-001')
            entered.set()
            assert release.wait(5)
            return QualityEvaluationService(enable_llm=False).evaluate(request, on_progress=on_progress)
    store = EvaluationJobs(workers=1, capacity=1, service_factory=SlowService)
    monkeypatch.setattr(router, 'jobs', store)
    monkeypatch.setattr(output_store, 'OUTPUT_DIR', tmp_path)
    app = FastAPI(); app.include_router(router.router)
    client = TestClient(app)
    try:
        response = client.post('/quality-evaluation/jobs', json=build_request().model_dump(mode='json'))
        assert response.status_code == 202
        job_id = response.json()['job_id']
        assert entered.wait(2)
        running = client.get(f'/quality-evaluation/jobs/{job_id}').json()
        assert running['status'] == 'running'
        assert running['current_rule'] == 'SEC-001'
        assert client.post('/quality-evaluation/jobs', json=build_request().model_dump(mode='json')).status_code == 429
    finally:
        release.set()
        store.executor.shutdown(wait=True)
    completed = client.get(f'/quality-evaluation/jobs/{job_id}').json()
    assert completed['status'] == 'completed'
    assert completed['completed_rules'] == completed['total_rules']
    result = completed['result']
    assert json.loads((tmp_path / f"{result['evaluation_id']}.json").read_text()) == result
    assert client.get('/quality-evaluation/jobs/unknown').status_code == 404


def test_save_failure_marks_job_failed(monkeypatch):
    def fail_save(result):
        raise OSError('disk failure')
    monkeypatch.setattr(jobs_module, 'save_report', fail_save)
    store = EvaluationJobs(service_factory=lambda: QualityEvaluationService(enable_llm=False))
    job = store.submit(build_request())
    store.executor.shutdown(wait=True)
    status = store.get(job['job_id'])
    assert status['status'] == 'failed'
    assert status['result'] is None
    assert 'report saving failed' in status['error']
