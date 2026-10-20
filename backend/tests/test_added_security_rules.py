import pytest

from modules.quality_evaluation.rule_repository import QualityRuleRepository
from modules.quality_evaluation.rule_selector import ApplicableRuleSelector
from modules.quality_evaluation.semantic_evaluator import SemanticEvaluator
from test_quality_service_integration import build_request


@pytest.mark.parametrize('rule_id', [f'SEC-{n:03}' for n in range(3, 9)])
def test_added_security_rules_selected_and_skipped_without_provider(rule_id):
    rules = QualityRuleRepository().load_rules()
    context = build_request()
    selected = ApplicableRuleSelector().select(context, rules)
    rule = next(rule for rule in selected if rule.rule_id == rule_id)
    assert rule.check_type == 'semantic'
    assert 'Return SKIPPED' in rule.semantic_instruction
    assert SemanticEvaluator(provider=None).evaluate(rule, context).status == 'SKIPPED'
    context.non_functional_requirements = []
    assert rule_id not in {r.rule_id for r in ApplicableRuleSelector().select(context, rules)}
