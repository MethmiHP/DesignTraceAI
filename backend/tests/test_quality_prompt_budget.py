import json
import pytest
from modules.quality_evaluation.semantic_evaluator import SemanticEvaluator


def test_large_evidence_is_bounded_and_preserved():
    operations = [{'operation_id': f'operation{i}', 'security': {'access_rules': ['Owner access only']}, 'description': 'example ' * 100} for i in range(50)]
    prompt = 'Evaluate security.\nProject artifacts:\n' + json.dumps({'operations': operations})
    parts = SemanticEvaluator._bounded_prompts(prompt)
    assert len(parts) > 1
    assert all(len(part.encode('utf-8')) <= 12000 for part in parts)
    records = [record for part in parts for record in json.loads(part.split('\n', 2)[2])]
    assert [record['value'] for record in records] == operations
    assert all('Do not infer missing controls' in part for part in parts)


def test_small_prompt_unchanged():
    prompt = 'Project artifacts:\n{}'
    assert SemanticEvaluator._bounded_prompts(prompt) == [prompt]


def test_indivisible_large_value_is_not_truncated():
    prompt = 'Project artifacts:\n' + json.dumps({'description': 'x' * 15000})
    with pytest.raises(ValueError, match='individual evidence'):
        SemanticEvaluator._bounded_prompts(prompt)


def test_partial_passes_never_become_whole_design_pass(monkeypatch):
    from test_quality_service_integration import build_request
    from modules.quality_evaluation.rule_repository import QualityRuleRepository
    from modules.quality_evaluation.llm.structured_schemas import LLMQualityAssessment

    class Provider:
        name = 'test'
        def generate_structured(self, prompt, schema):
            return LLMQualityAssessment(status='PASS', rationale='Partial evidence looks correct.')

    evaluator = SemanticEvaluator(Provider())
    monkeypatch.setattr(evaluator, '_bounded_prompts', lambda prompt: ['part one', 'part two'])
    rule = next(r for r in QualityRuleRepository().load_rules() if r.rule_id == 'SEC-001')
    result = evaluator.evaluate(rule, build_request())
    assert result.status.value == 'SKIPPED'
