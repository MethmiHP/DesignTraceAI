import logging
import pytest

from modules.quality_evaluation.llm.activity_logging import evaluation_log_context, log_provider_call, failure_reason
from modules.quality_evaluation.llm.provider import FallbackQualityLLMProvider


def test_provider_success_failure_and_fallback_logs_without_sensitive_content(caplog):
    class Provider:
        def __init__(self, name, model, fails=False):
            self.name, self.model_name, self.fails = name, model, fails

        @log_provider_call
        def generate_structured(self, prompt, schema):
            if self.fails:
                raise RuntimeError('secret-token-do-not-log')
            return {'status': 'PASS'}

    provider = FallbackQualityLLMProvider([
        Provider('gemini', 'test-gemini', True),
        Provider('groq', 'openai/gpt-oss-20b'),
    ])
    with caplog.at_level(logging.INFO), evaluation_log_context('PROJECT-1', 'SEC-001'):
        assert provider.generate_structured('private-requirement-text', dict) == {'status': 'PASS'}
    assert '[SEC-001] gemini started' in caplog.text
    assert '[SEC-001] gemini failed' in caplog.text
    assert '[SEC-001] gemini -> groq' in caplog.text
    assert '[SEC-001] groq OK (' in caplog.text
    assert 'PROJECT-1' not in caplog.text
    assert 'model=' not in caplog.text
    assert 'secret-token-do-not-log' not in caplog.text
    assert 'private-requirement-text' not in caplog.text
    assert provider.last_provider_name == 'groq'


@pytest.mark.parametrize('attribute,status,expected', [
    ('code', 429, '429 rate limit or quota'),
    ('code', 504, '504 timeout'),
    ('status_code', 401, '401 authentication rejected'),
    ('status_code', 400, '400 invalid request'),
])
def test_failure_reason_unwraps_provider_error(attribute, status, expected):
    cause = RuntimeError('private response with secret API key')
    setattr(cause, attribute, status)
    wrapper = RuntimeError('Provider failed')
    wrapper.__cause__ = cause
    assert failure_reason(wrapper) == expected


def test_failure_reason_does_not_log_exception_messages():
    assert failure_reason(TimeoutError('private URL')) == 'timeout'
    assert failure_reason(RuntimeError('secret API key')) == 'RuntimeError'
