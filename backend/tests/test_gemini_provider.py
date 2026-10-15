from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google import genai
from google.genai.errors import ClientError, ServerError
from pydantic import BaseModel

from modules.api_component_design.llm.provider import (
    GeminiLLMProvider,
    LLMUnavailableError,
)


class ResponseSchema(BaseModel):
    name: str


@pytest.fixture
def provider(monkeypatch):
    client = Mock()
    constructor = Mock(return_value=client)
    monkeypatch.setattr(genai, 'Client', constructor)
    provider = GeminiLLMProvider(api_key='test-key')
    return provider, client, constructor


def test_retry_configuration_and_successful_response(provider):
    provider, client, constructor = provider
    retry = constructor.call_args.kwargs['http_options'].retry_options
    assert retry.attempts == 4
    assert retry.initial_delay == 2.0
    assert retry.max_delay == 8.0
    assert 503 in retry.http_status_codes
    assert 404 not in retry.http_status_codes
    client.models.generate_content.return_value = SimpleNamespace(text='{"name":"certificate"}')
    assert provider.generate_structured('test prompt', ResponseSchema).name == 'certificate'


@pytest.mark.parametrize('status', [429, 500, 502, 503, 504])
def test_exhausted_transient_error_is_actionable(provider, status):
    provider, client, _ = provider
    error_class = ClientError if status == 429 else ServerError
    original = error_class(status, {'error': {'message': 'Unavailable'}})
    client.models.generate_content.side_effect = original
    with pytest.raises(LLMUnavailableError, match=f'HTTP {status}') as caught:
        provider.generate_structured('test prompt', ResponseSchema)
    assert caught.value.__cause__ is original


def test_non_transient_error_is_preserved(provider):
    provider, client, _ = provider
    original = ClientError(404, {'error': {'message': 'Model not found'}})
    client.models.generate_content.side_effect = original
    with pytest.raises(ClientError) as caught:
        provider.generate_structured('test prompt', ResponseSchema)
    assert caught.value is original
