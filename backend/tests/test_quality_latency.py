from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock

from modules.quality_evaluation.llm.provider import FallbackQualityLLMProvider
from modules.quality_evaluation.llm.structured_schemas import LLMQualityAssessment
from modules.quality_evaluation.service import QualityEvaluationService
from test_quality_service_integration import build_request


def test_unavailable_primary_is_not_retried_when_fallback_is_healthy():
    primary, fallback = Mock(name='primary'), Mock(name='fallback')
    primary.name, fallback.name = 'gemini', 'groq'
    error = RuntimeError('provider unavailable')
    error.code = 503
    primary.generate_structured.side_effect = error
    fallback.generate_structured.return_value = 'assessment'
    provider = FallbackQualityLLMProvider([primary, fallback])
    assert provider.generate_structured('one', dict) == 'assessment'
    assert provider.generate_structured('two', dict) == 'assessment'
    assert primary.generate_structured.call_count == 1
    assert fallback.generate_structured.call_count == 2


def test_parallel_calls_keep_separate_provider_attribution():
    barrier = Barrier(2)
    class Gemini:
        name = 'gemini'
        def generate_structured(self, prompt, schema):
            if prompt == 'fallback':
                raise ValueError('fallback requested')
            barrier.wait(timeout=3)
            return 'gemini'
    class Groq:
        name = 'groq'
        def generate_structured(self, prompt, schema):
            barrier.wait(timeout=3)
            return 'groq'
    provider = FallbackQualityLLMProvider([Gemini(), Groq()])
    def call(prompt):
        value = provider.generate_structured(prompt, dict)
        return value, provider.last_provider_name
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(call, ['primary', 'fallback'])) == [('gemini', 'gemini'), ('groq', 'groq')]


def test_parallel_checks_preserve_results_and_progress(monkeypatch):
    class Provider:
        name = 'test'
        def generate_structured(self, prompt, schema):
            return LLMQualityAssessment(status='PASS', rationale='Supported', evidence=['test'])
    service = QualityEvaluationService(llm_provider=Provider(), enable_llm=True)
    expected = service.evaluate(build_request())
    service.semantic_workers = 2
    # Force the first two semantic checks to overlap without timing assertions.
    original = service.semantic_evaluator.evaluate
    barrier = Barrier(2)
    first = [r.rule_id for r in expected.rule_results if r.check_type.value == 'semantic'][:2]
    def evaluate(rule, context):
        if rule.rule_id in first:
            barrier.wait(timeout=3)
        return original(rule, context)
    monkeypatch.setattr(service.semantic_evaluator, 'evaluate', evaluate)
    progress = []
    actual = service.evaluate(build_request(), on_progress=lambda completed, total, current: progress.append(completed))
    assert actual.rule_results == expected.rule_results
    assert actual.metrics == expected.metrics
    assert actual.findings == expected.findings
    assert progress == sorted(progress)
    assert progress[-1] == len(actual.rule_results)
