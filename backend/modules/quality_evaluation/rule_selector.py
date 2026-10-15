from .schemas import (
    QualityEvaluationRequest,
    QualityRule,
)


class ApplicableRuleSelector:

    def select(
        self,
        context: QualityEvaluationRequest,
        rules: list[QualityRule],
    ) -> list[QualityRule]:

        selected: list[QualityRule] = []

        available_categories = {
            nfr.category
            for nfr
            in context.non_functional_requirements
        }

        for rule in rules:

            if not self._required_artifacts_exist(
                context,
                rule,
            ):
                continue

            if rule.always_apply:
                selected.append(rule)
                continue

            if any(
                category in available_categories
                for category
                in rule.nfr_categories
            ):
                selected.append(rule)

        return selected

    def _required_artifacts_exist(
        self,
        context: QualityEvaluationRequest,
        rule: QualityRule,
    ) -> bool:

        return all(
            self._artifact_exists(
                context,
                artifact_type,
            )
            for artifact_type
            in rule.artifact_types
        )

    def _artifact_exists(
        self,
        context: QualityEvaluationRequest,
        artifact_type: str,
    ) -> bool:

        artifact_type = artifact_type.upper()

        if artifact_type == "FR":
            return bool(
                context.functional_requirements
            )

        if artifact_type == "NFR":
            return bool(
                context.non_functional_requirements
            )

        if artifact_type == "ARCHITECTURE":
            return bool(
                context.architecture.elements
            )

        if artifact_type == "DATABASE":
            return bool(
                context.database.entities
            )

        if artifact_type == "API":
            return bool(
                context
                .api_component_design
                .api_operations
                or context
                .api_component_design
                .openapi_document
            )

        if artifact_type == "COMPONENT":
            return bool(
                context
                .api_component_design
                .responsibilities
            )

        return False