from threading import Event
from pydantic import BaseModel
from modules.api_component_design.jobs import DesignJobs


class Payload(BaseModel):
    text: str


def test_slow_generation_returns_job_and_preserves_result():
    started, finish = Event(), Event()

    async def design(request):
        started.set()
        assert finish.wait(5)
        return request

    jobs = DesignJobs(design)
    try:
        record = jobs.submit(Payload(text='result'))
        assert record['status'] == 'queued'
        assert started.wait(2)
        assert jobs.get(record['job_id'])['status'] == 'running'
        finish.set()
        jobs.executor.shutdown(wait=True)
        completed = jobs.get(record['job_id'])
        assert completed['status'] == 'completed'
        assert completed['result'] == {'text': 'result'}
        assert jobs.get('unknown') is None
    finally:
        finish.set()
        jobs.executor.shutdown(wait=True)


def test_failed_job_has_safe_error():
    async def design(request):
        raise RuntimeError('private provider data')

    jobs = DesignJobs(design)
    record = jobs.submit(Payload(text='test'))
    jobs.executor.shutdown(wait=True)
    failed = jobs.get(record['job_id'])
    assert failed['status'] == 'failed'
    assert 'private' not in failed['error']
