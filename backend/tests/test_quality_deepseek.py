from unittest.mock import Mock
import httpx
import pytest
from modules.quality_evaluation.llm import provider
from modules.quality_evaluation.llm.structured_schemas import LLMQualityAssessment
from modules.quality_evaluation.llm.activity_logging import failure_reason


def test_only_deepseek_selected_even_when_old_settings_exist(monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-key')
    monkeypatch.setenv('QUALITY_LLM_PRIMARY_PROVIDER', 'gemini')
    gemini, groq = Mock(side_effect=AssertionError('Must not initialize')), Mock(side_effect=AssertionError('Must not initialize'))
    monkeypatch.setattr(provider, 'GeminiQualityLLMProvider', gemini)
    monkeypatch.setattr(provider, 'GroqQualityLLMProvider', groq)
    assert provider.build_default_quality_llm_provider().name == 'deepseek'
    gemini.assert_not_called()
    groq.assert_not_called()


def test_missing_key_does_not_fall_back(monkeypatch):
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    with pytest.raises(provider.QualityLLMUnavailableError, match='DEEPSEEK_API_KEY'):
        provider.build_default_quality_llm_provider()


@pytest.mark.parametrize('content,finish,valid', [
    ('{"status":"PASS","rationale":"Supported","evidence":[],"affected_nfr_ids":[]}', 'stop', True),
    ('not json', 'stop', False),
    ('{"status":"UNKNOWN"}', 'stop', False),
    ('', 'stop', False),
    ('{"status":"PASS","rationale":"Supported"}', 'length', False),
])
def test_deepseek_validates_output(monkeypatch, content, finish, valid):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-key')
    response = httpx.Response(200, request=httpx.Request('POST', 'https://api.deepseek.com/chat/completions'), json={'choices':[{'finish_reason':finish,'message':{'content':content}}]})
    post = Mock(return_value=response)
    monkeypatch.setattr(provider.httpx, 'post', post)
    client = provider.DeepSeekQualityLLMProvider()
    if valid:
        assert client.generate_structured('Evaluate evidence', LLMQualityAssessment).status == 'PASS'
    else:
        with pytest.raises(provider.QualityLLMUnavailableError):
            client.generate_structured('Evaluate evidence', LLMQualityAssessment)
    assert post.call_args.kwargs['json']['response_format'] == {'type':'json_object'}
    assert 'JSON Schema' in post.call_args.kwargs['json']['messages'][0]['content']


def test_http_error_is_safe():
    error = httpx.HTTPStatusError('private response', request=httpx.Request('POST','https://api.deepseek.com'), response=httpx.Response(402))
    assert failure_reason(error) == '402 insufficient balance'
