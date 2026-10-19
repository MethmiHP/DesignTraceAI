import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.quality_evaluation import output_store, router
from modules.quality_evaluation.service import QualityEvaluationService
from test_quality_service_integration import build_request


def test_frontend_endpoint_saves_each_response(tmp_path, monkeypatch):
    monkeypatch.setattr(output_store, 'OUTPUT_DIR', tmp_path / 'output')
    monkeypatch.setattr(router, 'service', QualityEvaluationService(enable_llm=False))
    app = FastAPI()
    app.include_router(router.router)
    client = TestClient(app)
    for _ in range(2):
        response = client.post('/quality-evaluation/evaluate', json=build_request().model_dump(mode='json'))
        assert response.status_code == 200
        body = response.json()
        saved = output_store.OUTPUT_DIR / f"{body['evaluation_id']}.json"
        assert json.loads(saved.read_text()) == body
    assert len(list(output_store.OUTPUT_DIR.glob('*.json'))) == 2
    assert not list(output_store.OUTPUT_DIR.glob('*.tmp'))


def test_endpoint_reports_save_failure(monkeypatch):
    monkeypatch.setattr(router, 'service', QualityEvaluationService(enable_llm=False))
    def fail_save(response):
        raise OSError('Disk unavailable')
    monkeypatch.setattr(router, 'save_report', fail_save)
    app = FastAPI()
    app.include_router(router.router)
    response = TestClient(app).post('/quality-evaluation/evaluate', json=build_request().model_dump(mode='json'))
    assert response.status_code == 500
    assert 'could not be saved' in response.json()['detail']
