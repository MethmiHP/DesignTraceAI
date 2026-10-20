import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from modules.quality_evaluation.schemas import (
    ArchitectureDesign, DatabaseDesign, QualityEvaluationRequest,
)
from modules.quality_evaluation.service import QualityEvaluationService
from modules.quality_evaluation.semantic_evaluator import SemanticEvaluator
from modules.quality_evaluation.rule_repository import QualityRuleRepository
from test_quality_service_integration import build_request

FIXTURES = Path(__file__).parent / 'fixtures' / 'module_outputs'


def artifact(name):
    return json.loads((FIXTURES / f'{name}.json').read_text())


def test_architecture_output_maps_only_relevant_design():
    raw = artifact('architecture')
    model = ArchitectureDesign.model_validate(raw)
    assert model.selected_architecture == 'Microservices'
    assert len(model.elements) == 4
    assert model.elements[0].element_id == 'ARCH-COMP-001'
    assert 'Apply shared security policies' in model.elements[0].main_responsibility
    saved = model.model_dump(mode='json')
    assert saved['relationships'] == raw['high_level_design']['relationships']
    assert saved['elements'][0]['requirement_ids'] == raw['high_level_design']['components'][0]['requirement_ids']
    assert not {'traceability', 'high_level_design', 'architecture_decisions_for_adr', 'quality_attribute_profile', 'metadata'} & saved.keys()


def test_database_output_retains_columns_and_maps_foreign_keys():
    raw = artifact('database')
    model = DatabaseDesign.model_validate(raw)
    assert len(model.entities) == 4
    assert model.entities[2].foreign_keys == ['customer_id -> customers.customer_id', 'vehicle_id -> vehicles.vehicle_id']
    assert model.entities[0].primary_key == 'customer_id'
    assert 'UNIQUE (email)' in model.entities[0].constraints
    saved = model.model_dump(mode='json')
    assert saved['entities'][0]['columns'] == raw['design']['tables'][0]['columns']
    assert not {'design', 'schema_validation', 'mapping_validation', 'artifacts', 'overall_valid'} & saved.keys()
    payload = build_request().model_dump(mode='json')
    payload['project_id'] = raw['project_id']
    payload['database'] = raw
    result = QualityEvaluationService(enable_llm=False).evaluate(QualityEvaluationRequest.model_validate(payload))
    assert next(r for r in result.rule_results if r.rule_id == 'OPS-002').status == 'PASS'


def test_api_output_preserves_security_parameters_and_metadata_in_prompt():
    payload = build_request().model_dump(mode='json')
    api = payload['api_component_design']
    api['project_id'] = payload['project_id']
    api['semantic_extractions'] = [{'requirement_id': 'FR-001', 'actor': 'Customer', 'action': 'submit', 'resource': 'Transfer', 'confidence': None}]
    api['requirement_to_api_mapping'] = [{'requirement_id': 'FR-001', 'operation_id': 'submitTransfer'}]
    api['validation'] = {'valid': True, 'issues': []}
    operation = api['api_operations'][0]
    operation['security'] = {'authentication': 'bearer', 'roles': ['customer'], 'access_rules': ['Own accounts only']}
    operation['parameters'] = [{'name': 'bank_account_id', 'location': 'path', 'type': 'string', 'required': True}]
    operation['generation_source'] = 'groq'
    request = QualityEvaluationRequest.model_validate(payload)
    saved = request.api_component_design.model_dump(mode='json')
    for key in ['security', 'parameters']:
        assert saved['api_operations'][0][key] == operation[key]
    assert 'semantic_extractions' not in saved
    assert 'validation' not in saved
    assert 'generation_source' not in saved['api_operations'][0]
    # Large architecture output must not truncate away the API evidence.
    request.architecture.elements[0].main_responsibility = 'x' * 21000
    rule = next(r for r in QualityRuleRepository().load_rules() if r.rule_id == 'SEC-001')
    prompt = SemanticEvaluator(provider=None)._build_prompt(rule, request)
    assert 'Own accounts only' in prompt
    assert 'generation_source' not in prompt
    assert 'semantic_extractions' not in prompt


@pytest.mark.parametrize('name', ['architecture', 'database'])
def test_mixed_project_outputs_rejected(name):
    payload = build_request().model_dump(mode='json')
    payload[name] = artifact(name)
    with pytest.raises(ValidationError, match=f'{name}.project_id must match'):
        QualityEvaluationRequest.model_validate(payload)


def test_malformed_upstream_columns_rejected():
    raw = artifact('database')
    del raw['design']['tables'][0]['columns'][0]['name']
    with pytest.raises(ValidationError):
        DatabaseDesign.model_validate(raw)
