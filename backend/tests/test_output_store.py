import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app import app
from shared.utils import output_store
from test_api_component_design import get_base_request


def test_unique_runs_preserve_json_and_stay_in_output_directory(isolated_outputs, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    artifacts = {'response': {'project_id': '../../project', 'message': 'වෛද්‍ය', 'valid': False}}
    with ThreadPoolExecutor(max_workers=4) as pool:
        paths = list(pool.map(lambda _: output_store.save_outputs('../../project', artifacts), range(4)))
    assert len(set(paths)) == 4
    for path in paths:
        assert path.parent == isolated_outputs
        assert json.loads((path / 'response.json').read_text()) == artifacts['response']
    assert not list(isolated_outputs.glob('.pending-*'))


def test_serialization_failure_does_not_publish_a_run(isolated_outputs):
    with pytest.raises(TypeError):
        output_store.save_outputs('project', {'response': object()})
    assert not isolated_outputs.exists()


def test_write_failure_does_not_publish_partial_outputs(isolated_outputs, monkeypatch):
    def fail_write(*args, **kwargs):
        raise OSError('Disk full')

    monkeypatch.setattr(output_store.Path, 'write_text', fail_write)
    with pytest.raises(OSError, match='Disk full'):
        output_store.save_outputs('project', {'response': {'valid': True}})
    assert list(isolated_outputs.iterdir()) == []


@pytest.mark.parametrize('valid', [True, False])
def test_design_saves_complete_response_and_stages(isolated_outputs, valid):
    request = get_base_request()
    if not valid:
        request['architecture']['elements'] = []
    response = TestClient(app).post('/api-component/design', json=request)
    assert response.status_code == 200
    result = response.json()
    assert result['validation']['valid'] is valid
    runs = list(isolated_outputs.iterdir())
    assert len(runs) == 1
    files = {path.stem: json.loads(path.read_text()) for path in runs[0].glob('*.json')}
    from modules.api_component_design.schemas import APIComponentDesignRequest
    assert files['request'] == APIComponentDesignRequest(**request).model_dump(mode='json')
    assert files['response'] == result
    for name, value in result.items():
        if name != 'project_id':
            assert files[name] == value
    assert len(files['raw_semantic_extractions']) == 1
    assert isinstance(files['database_context'], list)
    assert isinstance(files['initial_api_operations'], list)
    assert 'initial_validation' in files
    assert 'refinement_issues' in files
