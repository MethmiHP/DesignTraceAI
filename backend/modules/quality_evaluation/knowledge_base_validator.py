from collections import Counter

from .schemas import (
    CheckType,
    NFRCategory,
    QualityRule,
)


class QualityKnowledgeBaseValidationError(
    ValueError
):
    pass


class QualityKnowledgeBaseValidator:

    # Deterministic handlers currently supported
    # by DeterministicEvaluator
    SUPPORTED_DETERMINISTIC_HANDLERS = {
        "openapi_version_is_3",
        "unique_operation_ids",
        "database_foreign_keys_resolve",
        "operation_ids_are_camel_case",
        "api_has_error_responses",
        "collection_get_has_pagination",
        "security_declaration_present",
    }

    # Applicability handlers currently supported
    # by ApplicableRuleSelector
    SUPPORTED_APPLICABILITY_HANDLERS = {
        "database_has_foreign_keys",
        "api_has_collection_get",
        "api_has_state_changing_operation",
        "security_nfr_requires_api_access_control",
    }

    # Validates the complete quality-rule knowledge base
    def validate(
        self,
        rules: list[QualityRule],
    ) -> None:

        errors: list[str] = []

        if not rules:
            raise QualityKnowledgeBaseValidationError(
                "The quality-rule knowledge base is empty."
            )

        errors.extend(
            self._validate_unique_rule_ids(
                rules
            )
        )

        errors.extend(
            self._validate_rule_configuration(
                rules
            )
        )

        errors.extend(
            self._validate_nfr_category_coverage(
                rules
            )
        )

        if errors:
            message = (
                "Quality-rule knowledge base validation failed:\n"
                + "\n".join(
                    f"- {error}"
                    for error in errors
                )
            )

            raise QualityKnowledgeBaseValidationError(
                message
            )

    # Ensures every rule ID is unique
    def _validate_unique_rule_ids(
        self,
        rules: list[QualityRule],
    ) -> list[str]:

        rule_ids = [
            rule.rule_id
            for rule in rules
        ]

        duplicates = [
            rule_id
            for rule_id, count
            in Counter(rule_ids).items()
            if count > 1
        ]

        return [
            (
                "Duplicate rule_id found: "
                f"{rule_id}"
            )
            for rule_id in duplicates
        ]

    # Validates required configuration
    # for every deterministic and semantic rule
    def _validate_rule_configuration(
        self,
        rules: list[QualityRule],
    ) -> list[str]:

        errors: list[str] = []

        for rule in rules:

            if not rule.rule_id.strip():
                errors.append(
                    "A rule has an empty rule_id."
                )

            if not rule.title.strip():
                errors.append(
                    (
                        f"{rule.rule_id}: "
                        "title is empty."
                    )
                )

            if not rule.source.strip():
                errors.append(
                    (
                        f"{rule.rule_id}: "
                        "source is empty."
                    )
                )

            if not rule.artifact_types:
                errors.append(
                    (
                        f"{rule.rule_id}: "
                        "artifact_types is empty."
                    )
                )

            if not rule.recommendation_template.strip():
                errors.append(
                    (
                        f"{rule.rule_id}: "
                        "recommendation_template "
                        "is empty."
                    )
                )

            if (
                rule.check_type
                == CheckType.DETERMINISTIC
            ):
                errors.extend(
                    self._validate_deterministic_rule(
                        rule
                    )
                )

            if (
                rule.check_type
                == CheckType.SEMANTIC
            ):
                errors.extend(
                    self._validate_semantic_rule(
                        rule
                    )
                )

            errors.extend(
                self._validate_applicability_handler(
                    rule
                )
            )

        return errors

    # Checks deterministic rule configuration
    def _validate_deterministic_rule(
        self,
        rule: QualityRule,
    ) -> list[str]:

        errors: list[str] = []

        if not rule.handler:
            errors.append(
                (
                    f"{rule.rule_id}: "
                    "deterministic rule has no handler."
                )
            )

            return errors

        if (
            rule.handler
            not in
            self.SUPPORTED_DETERMINISTIC_HANDLERS
        ):
            errors.append(
                (
                    f"{rule.rule_id}: "
                    "unsupported deterministic handler "
                    f"'{rule.handler}'."
                )
            )

        return errors

    # Checks semantic rule configuration
    def _validate_semantic_rule(
        self,
        rule: QualityRule,
    ) -> list[str]:

        errors: list[str] = []

        if not rule.semantic_instruction:
            errors.append(
                (
                    f"{rule.rule_id}: "
                    "semantic rule has no "
                    "semantic_instruction."
                )
            )

            return errors

        if not rule.semantic_instruction.strip():
            errors.append(
                (
                    f"{rule.rule_id}: "
                    "semantic_instruction is empty."
                )
            )

        return errors

    # Checks whether an applicability handler
    # is supported by the selector
    def _validate_applicability_handler(
        self,
        rule: QualityRule,
    ) -> list[str]:

        if not rule.applicability_handler:
            return []

        if (
            rule.applicability_handler
            in self.SUPPORTED_APPLICABILITY_HANDLERS
        ):
            return []

        return [
            (
                f"{rule.rule_id}: "
                "unsupported applicability handler "
                f"'{rule.applicability_handler}'."
            )
        ]

    # Ensures all 11 project-defined NFR
    # categories have at least one rule
    def _validate_nfr_category_coverage(
        self,
        rules: list[QualityRule],
    ) -> list[str]:

        covered_categories = {
            category
            for rule in rules
            for category in rule.nfr_categories
        }

        missing_categories = [
            category
            for category in NFRCategory
            if category not in covered_categories
        ]

        return [
            (
                "No quality rule exists for NFR "
                f"category '{category.value}'."
            )
            for category in missing_categories
        ]