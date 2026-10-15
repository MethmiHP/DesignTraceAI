from types import SimpleNamespace

from modules.api_component_design.schemas import APIOperation, APIParameter, SemanticExtraction
from modules.api_component_design.openapi_builder import OpenAPIBuilder
from modules.api_component_design.llm.llm_api_generator import LLMAPIGenerator
from modules.api_component_design.llm.structured_schemas import LLMAPIOperation
from modules.api_component_design.llm.stub_provider import StubLLMProvider
from modules.api_component_design.validator import APIDesignValidator


def test_parameters_survive_llm_conversion_and_openapi_export():
    parameters = [
        APIParameter(name='patient_id', location='path', type='uuid', required=True, description='Patient identifier'),
        APIParameter(name='status', location='query', description='Filter by prescription status'),
        APIParameter(name='X-Request-ID', location='header', description='Request correlation identifier'),
    ]
    candidate = LLMAPIOperation(
        operation_id='getPatientPrescriptions', requirement_id='FR-1', element_id='COMP-1',
        method='GET', path='/patients/{patient_id}/prescriptions', parameters=parameters,
    )
    provider = StubLLMProvider(candidate)
    operation = LLMAPIGenerator(provider).generate(
        requirement_statement='View prescriptions by status with an X-Request-ID header.',
        semantic=SemanticExtraction(requirement_id='FR-1', action='view', resource='Prescription'),
        architecture_element=SimpleNamespace(element_id='COMP-1', name='Prescriptions', type='Service', main_responsibility='Manage prescriptions'),
        database_context=[],
    )
    assert operation.parameters == parameters
    document = OpenAPIBuilder().build([operation])
    exported = document['paths'][operation.path]['get']['parameters']
    assert [item['in'] for item in exported] == ['path', 'query', 'header']
    assert exported[0]['schema'] == {'type': 'string', 'format': 'uuid'}
    assert exported[0]['required'] is True
    assert exported[1]['description'] == 'Filter by prescription status'
    assert exported[1]['required'] is False
    assert 'parameters as an array' in provider.last_prompt


def test_create_endpoint_does_not_invent_path_or_query_parameters():
    operation = APIOperation(operation_id='createPrescription', requirement_id='FR-1',
        element_id='COMP-1', method='POST', path='/prescriptions', request_schema={'patient_id': 'uuid'})
    spec = OpenAPIBuilder().build([operation])['paths']['/prescriptions']['post']
    assert 'parameters' not in spec
    assert 'application/json' in spec['requestBody']['content']
    assert spec['requestBody']['required'] is True


def test_explicit_path_type_and_query_types_are_preserved():
    operation = APIOperation(operation_id='getPrescription', requirement_id='FR-1',
        element_id='COMP-1', method='GET', path='/prescriptions/{prescription_id}', parameters=[
            APIParameter(name='prescription_id', location='path', type='integer', required=True),
            APIParameter(name='active', location='query', type='boolean'),
        ])
    spec = OpenAPIBuilder().build([operation])['paths'][operation.path]['get']
    assert len(spec['parameters']) == 2
    assert spec['parameters'][0]['schema'] == {'type': 'integer'}
    assert spec['parameters'][1]['schema'] == {'type': 'boolean'}


def test_invalid_parameter_metadata_is_reported():
    operation = APIOperation(operation_id='getPrescription', requirement_id='FR-1',
        element_id='COMP-1', method='GET', path='/prescriptions', parameters=[
            APIParameter(name='missing_id', location='path'),
            APIParameter(name='invented_filter', location='query'),
            APIParameter(name='Authorization', location='header'),
            APIParameter(name='X-Request-ID', location='header'),
            APIParameter(name='x-request-id', location='header'),
        ])
    issues = []
    APIDesignValidator._validate_parameters(operation, {'patient_id'}, issues)
    assert {item.code for item in issues} == {
        'INVALID_PATH_PARAMETER', 'UNGROUNDED_QUERY_PARAMETER',
        'RESERVED_HEADER_PARAMETER', 'DUPLICATE_PARAMETER',
    }
