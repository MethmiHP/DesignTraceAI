import asyncio
import json
from unittest.mock import Mock

import httpx
import pytest
from pydantic import BaseModel, ValidationError

from modules.api_component_design.llm import fallback_provider, groq_provider
from modules.api_component_design.llm.fallback_provider import FallbackLLMProvider
from modules.api_component_design.llm.provider import LLMUnavailableError
from modules.api_component_design.llm.structured_schemas import LLMAPIOperation
from modules.api_component_design.schemas import APIComponentDesignRequest
from modules.api_component_design.service import APIComponentDesignService
from test_api_component_design import get_base_request


class Answer(BaseModel):
    text: str


def test_gemini_success_does_not_initialize_groq():
    gemini = Mock()
    gemini.generate_structured.return_value = Answer(text='Gemini')
    groq = Mock(side_effect=AssertionError('Must not initialize Groq'))
    chain = FallbackLLMProvider([('Gemini', lambda: gemini), ('Groq', groq)])
    answer, source = chain.generate_structured_with_source('prompt', Answer)
    assert answer.text == 'Gemini'
    assert source == 'gemini'
    groq.assert_not_called()
    gemini.close.assert_called_once()


@pytest.mark.parametrize('invalid', [False, True])
def test_gemini_failure_or_invalid_schema_tries_groq(invalid):
    calls = []
    gemini, groq = Mock(), Mock()
    if invalid:
        gemini.generate_structured.return_value = {'wrong': 'schema'}
    else:
        gemini.generate_structured.side_effect = RuntimeError('503')
    groq.generate_structured.return_value = Answer(text='Groq')
    def factory(name, provider):
        calls.append(name)
        return provider
    chain = FallbackLLMProvider([
        ('Gemini', lambda: factory('Gemini', gemini)),
        ('Groq', lambda: factory('Groq', groq)),
    ])
    assert chain.generate_structured('prompt', Answer).text == 'Groq'
    assert calls == ['Gemini', 'Groq']


def test_missing_primary_key_does_not_block_fallback():
    def missing_key():
        raise ValueError('Missing key')
    groq = Mock()
    groq.generate_structured.return_value = Answer(text='Groq')
    chain = FallbackLLMProvider([('Gemini', missing_key), ('Groq', lambda: groq)])
    assert chain.generate_structured('prompt', Answer).text == 'Groq'


@pytest.mark.parametrize('groq_succeeds', [True, False])
def test_default_service_chain_reaches_groq_then_baseline(monkeypatch, groq_succeeds):
    gemini, groq = Mock(), Mock()
    gemini.generate_structured.side_effect = RuntimeError('Gemini quota exhausted')
    if groq_succeeds:
        groq.generate_structured.return_value = LLMAPIOperation(
            operation_id='bookAppointmentViaGroq', requirement_id='FR-003',
            element_id='COMP-APPOINTMENT', method='POST', path='/appointments',
        )
    else:
        groq.generate_structured.return_value = {'invalid': True}
    monkeypatch.setattr(fallback_provider, 'GeminiLLMProvider', lambda: gemini)
    monkeypatch.setattr(fallback_provider, 'GroqLLMProvider', lambda: groq)
    service = APIComponentDesignService(enable_llm=True)
    result = asyncio.run(service.design(APIComponentDesignRequest(**get_base_request())))
    assert result.api_operations[0].generation_source == ('groq' if groq_succeeds else 'rule-based')
    assert result.api_operations[0].operation_id == ('bookAppointmentViaGroq' if groq_succeeds else 'createAppointment')
    assert ('LLM_API_GENERATION_FAILED' in {issue.code for issue in result.validation.issues}) is not groq_succeeds
    gemini.generate_structured.assert_called_once()
    groq.generate_structured.assert_called_once()


def test_all_initialization_failures_are_sanitized():
    def fail():
        raise ValueError('secret-key-must-not-appear')
    with pytest.raises(LLMUnavailableError) as caught:
        FallbackLLMProvider([('Gemini', fail), ('Groq', fail)]).generate_structured('prompt', Answer)
    assert 'secret-key' not in str(caught.value)
    assert 'Gemini' in str(caught.value) and 'Groq' in str(caught.value)


def test_groq_request_and_schema(monkeypatch):
    response = httpx.Response(200, request=httpx.Request('POST', 'https://api.groq.com'), json={
        'choices': [{'finish_reason': 'stop', 'message': {'content': '{"text":"ok"}'}}],
    })
    post = Mock(return_value=response)
    monkeypatch.setattr(groq_provider.httpx, 'post', post)
    provider = groq_provider.GroqLLMProvider(api_key='test-key')
    assert provider.generate_structured('prompt', Answer).text == 'ok'
    payload = post.call_args.kwargs['json']
    assert payload['model'] == 'openai/gpt-oss-120b'
    schema = payload['response_format']['json_schema']
    assert schema['strict'] is True
    assert schema['schema']['additionalProperties'] is False
    assert schema['schema']['required'] == ['text']
    full_schema = groq_provider.strict_schema(LLMAPIOperation.model_json_schema())
    assert full_schema['required'] == list(full_schema['properties'])
    for definition in full_schema['$defs'].values():
        assert definition['additionalProperties'] is False


@pytest.mark.parametrize('content,finish_reason', [('', 'stop'), ('not-json', 'stop'), ('{}', 'stop'), ('{"text":"ok"}', 'length')])
def test_groq_rejects_empty_invalid_or_truncated_output(monkeypatch, content, finish_reason):
    response = httpx.Response(200, request=httpx.Request('POST', 'https://api.groq.com'), json={
        'choices': [{'finish_reason': finish_reason, 'message': {'content': content}}],
    })
    monkeypatch.setattr(groq_provider.httpx, 'post', Mock(return_value=response))
    with pytest.raises((ValueError, ValidationError)):
        groq_provider.GroqLLMProvider(api_key='test-key').generate_structured('prompt', Answer)


def test_source_is_local_to_each_generation():
    gemini, groq = Mock(), Mock()
    gemini.generate_structured.side_effect = [RuntimeError('unavailable'), Answer(text='Gemini')]
    groq.generate_structured.return_value = Answer(text='Groq')
    chain = FallbackLLMProvider([('Gemini', lambda: gemini), ('Groq', lambda: groq)])
    assert chain.generate_structured_with_source('first', Answer)[1] == 'groq'
    assert chain.generate_structured_with_source('second', Answer)[1] == 'gemini'
