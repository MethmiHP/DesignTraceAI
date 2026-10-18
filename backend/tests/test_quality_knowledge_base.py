import pytest

from modules.quality_evaluation.knowledge_base_validator import (
    QualityKnowledgeBaseValidationError,
    QualityKnowledgeBaseValidator,
)
from modules.quality_evaluation.rule_repository import (
    QualityRuleRepository,
)
from modules.quality_evaluation.schemas import (
    CheckType,
    NFRCategory,
)


def load_rules():
    repository = QualityRuleRepository()

    return repository.load_rules()


def test_real_quality_knowledge_base_is_valid():
    rules = load_rules()

    validator = (
        QualityKnowledgeBaseValidator()
    )

    validator.validate(
        rules
    )


def test_all_nfr_categories_have_rule_coverage():
    rules = load_rules()

    covered_categories = {
        category
        for rule in rules
        for category in rule.nfr_categories
    }

    for category in NFRCategory:
        assert (
            category
            in covered_categories
        ), (
            f"No rule covers "
            f"{category.value}"
        )


def test_rule_ids_are_unique():
    rules = load_rules()

    rule_ids = [
        rule.rule_id
        for rule in rules
    ]

    assert len(rule_ids) == len(
        set(rule_ids)
    )


def test_deterministic_rules_have_handlers():
    rules = load_rules()

    for rule in rules:

        if (
            rule.check_type
            == CheckType.DETERMINISTIC
        ):
            assert rule.handler is not None
            assert rule.handler.strip()


def test_semantic_rules_have_instructions():
    rules = load_rules()

    for rule in rules:

        if (
            rule.check_type
            == CheckType.SEMANTIC
        ):
            assert (
                rule.semantic_instruction
                is not None
            )

            assert (
                rule.semantic_instruction
                .strip()
            )


def test_every_rule_has_source():
    rules = load_rules()

    for rule in rules:
        assert rule.source.strip()


def test_every_rule_has_recommendation():
    rules = load_rules()

    for rule in rules:
        assert (
            rule
            .recommendation_template
            .strip()
        )


def test_invalid_deterministic_handler_is_rejected():
    rules = load_rules()

    target_rule = next(
        rule
        for rule in rules
        if (
            rule.check_type
            == CheckType.DETERMINISTIC
        )
    )

    original_handler = (
        target_rule.handler
    )

    target_rule.handler = (
        "invalid_test_handler"
    )

    validator = (
        QualityKnowledgeBaseValidator()
    )

    with pytest.raises(
        QualityKnowledgeBaseValidationError
    ):
        validator.validate(
            rules
        )

    target_rule.handler = (
        original_handler
    )


def test_invalid_applicability_handler_is_rejected():
    rules = load_rules()

    target_rule = rules[0]

    original_handler = (
        target_rule
        .applicability_handler
    )

    target_rule.applicability_handler = (
        "invalid_applicability_handler"
    )

    validator = (
        QualityKnowledgeBaseValidator()
    )

    with pytest.raises(
        QualityKnowledgeBaseValidationError
    ):
        validator.validate(
            rules
        )

    target_rule.applicability_handler = (
        original_handler
    )