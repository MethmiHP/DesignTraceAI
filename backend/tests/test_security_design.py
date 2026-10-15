import asyncio

import pytest

from modules.api_component_design.schemas import APIComponentDesignRequest, APIOperation, SecurityPolicy
from modules.api_component_design.service import APIComponentDesignService
from modules.api_component_design.security import apply_security, validate_security
from modules.api_component_design.openapi_builder import OpenAPIBuilder
from modules.api_component_design.llm.stub_provider import StubLLMProvider
from modules.api_component_design.llm.structured_schemas import LLMAPIOperation
from test_api_component_design import get_base_request


def operation():
    return APIOperation(operation_id='createAppointment', requirement_id='FR-003', element_id='COMP-APPOINTMENT', method='POST', path='/appointments')


@pytest.mark.parametrize('authentication', ['bearer', 'basic', 'api_key'])
def test_protected_endpoint_exports_security_and_access_rules(authentication):
    policy = SecurityPolicy(authentication=authentication, roles=['patient'], access_rules=['Patients may access only their own appointments.'])
    op = operation()
    apply_security(op, policy)
    document = OpenAPIBuilder().build([op])
    spec = document['paths']['/appointments']['post']
    scheme_name = next(iter(spec['security'][0]))
    scheme = document['components']['securitySchemes'][scheme_name]
    assert scheme['type'] == ('apiKey' if authentication == 'api_key' else 'http')
    assert spec['security'][0][scheme_name] == []
    assert spec['x-required-roles'] == ['patient']
    assert spec['x-access-rules'] == policy.access_rules
    assert {'401', '403'} <= set(spec['responses'])
    assert 'parameters' not in spec  # Authorization is a security scheme, not a header parameter.


def test_public_and_unspecified_are_distinct():
    op = operation()
    builder = OpenAPIBuilder()
    assert 'security' not in builder.build([op])['paths']['/appointments']['post']
    apply_security(op, SecurityPolicy(authentication='none'))
    document = builder.build([op])
    assert document['paths']['/appointments']['post']['security'] == []
    assert 'components' not in document
    assert not op.error_responses


def test_validation_reports_missing_scheme_and_mismatch():
    request = APIComponentDesignRequest(**get_base_request())
    request.non_functional_requirements = []
    request.functional_requirements[0].statement = 'An authenticated patient shall book an appointment.'
    op = operation()
    issues = []
    validate_security(request, op, issues)
    assert 'SECURITY_CONFIGURATION_REQUIRED' in {issue.code for issue in issues}
    request.security = SecurityPolicy(authentication='bearer')
    issues = []
    validate_security(request, op, issues)
    assert 'SECURITY_POLICY_MISMATCH' in {issue.code for issue in issues}


def test_api_key_schemes_do_not_collide():
    first, second = operation(), operation()
    second.path = '/other'
    apply_security(first, SecurityPolicy(authentication='api_key', api_key_name='X-First'))
    apply_security(second, SecurityPolicy(authentication='api_key', api_key_name='X-Second', api_key_location='query'))
    schemes = OpenAPIBuilder().build([first, second])['components']['securitySchemes']
    assert len(schemes) == 2
    assert {scheme['name'] for scheme in schemes.values()} == {'X-First', 'X-Second'}


@pytest.mark.parametrize('use_llm', [False, True])
def test_policy_flows_through_generation_and_saved_response(use_llm, isolated_outputs):
    request = APIComponentDesignRequest(**get_base_request())
    request.security = SecurityPolicy(authentication='bearer', roles=['patient'], access_rules=['Only their own appointments.'])
    stub = StubLLMProvider(LLMAPIOperation(operation_id='createAppointment', requirement_id='FR-003', element_id='COMP-APPOINTMENT', method='POST', path='/appointments'))
    service = APIComponentDesignService(enable_llm=use_llm, llm_provider=stub)
    result = asyncio.run(service.design(request))
    assert result.validation.valid
    assert result.api_operations[0].security == request.security
    assert result.openapi_document['paths']['/appointments']['post']['security'] == [{'bearerAuth': []}]
    assert list(isolated_outputs.glob('*/response.json'))
    if use_llm:
        assert 'Only their own appointments.' in stub.last_prompt
        assert 'SECURITY POLICY' in stub.last_prompt


def test_requirement_policy_can_override_project_default():
    request = APIComponentDesignRequest(**get_base_request())
    request.security = SecurityPolicy(authentication='bearer')
    request.functional_requirements[0].security = SecurityPolicy(authentication='none')
    service = APIComponentDesignService(enable_llm=False)
    result = asyncio.run(service.design(request))
    assert result.api_operations[0].security.authentication == 'none'
    assert result.openapi_document['paths']['/appointments']['post']['security'] == []


def test_missing_mechanism_blocks_generation_until_user_resolves(monkeypatch, isolated_outputs):
    request = APIComponentDesignRequest(**get_base_request())
    request.functional_requirements[0].statement = 'An authenticated patient shall book an appointment.'
    service = APIComponentDesignService(enable_llm=False)
    original_extract = service.semantic_extractor.extract
    def unexpected_extract(*args):
        pytest.fail('Generation must wait for a security decision')
    monkeypatch.setattr(service.semantic_extractor, 'extract', unexpected_extract)
    blocked = asyncio.run(service.design(request))
    assert not blocked.validation.valid
    assert blocked.api_operations == []
    gap = next(issue for issue in blocked.validation.issues if issue.code == 'SECURITY_CONFIGURATION_REQUIRED')
    assert gap.field == 'functional_requirements.0.security.authentication'
    assert request.security.authentication == 'unspecified'
    monkeypatch.setattr(service.semantic_extractor, 'extract', original_extract)
    request.functional_requirements[0].security = SecurityPolicy(authentication='basic')
    resolved = asyncio.run(service.design(request))
    assert resolved.api_operations[0].security.authentication == 'basic'
    assert not any(issue.code == 'SECURITY_CONFIGURATION_REQUIRED' for issue in resolved.validation.issues)
    import json
    saved = [json.loads(path.read_text()) for path in isolated_outputs.glob('*/request.json')]
    assert any(item['functional_requirements'][0]['security']['authentication'] == 'basic' for item in saved)
