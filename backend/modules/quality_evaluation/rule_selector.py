import re

from .schemas import (
    NFRCategory,
    QualityEvaluationRequest,
    QualityRule,
)


class ApplicableRuleSelector:

    # Selects only rules that have enough relevant evidence to evaluate
    def select(
        self,
        context: QualityEvaluationRequest,
        rules: list[QualityRule],
    ) -> list[QualityRule]:

        selected_rules: list[QualityRule] = []

        available_categories = {
            nfr.category
            for nfr in context.non_functional_requirements
        }

        for rule in rules:

            # Required artifacts must exist before the rule can run
            if not self._required_artifacts_exist(
                rule,
                context,
            ):
                continue

            # Rules that are not always applicable require
            # at least one matching NFR category
            if not rule.always_apply:

                required_categories = set(
                    rule.nfr_categories
                )

                if (
                    required_categories
                    and not (
                        required_categories
                        & available_categories
                    )
                ):
                    continue

            # Apply the rule-specific applicability condition
            if not self._passes_applicability_handler(
                rule,
                context,
            ):
                continue

            selected_rules.append(
                rule
            )

        return selected_rules

    # Checks whether every artifact required by a rule exists
    def _required_artifacts_exist(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> bool:

        return all(
            self._artifact_exists(
                artifact_type,
                context,
            )
            for artifact_type
            in rule.artifact_types
        )

    # Checks whether a specific artifact type is available
    def _artifact_exists(
        self,
        artifact_type: str,
        context: QualityEvaluationRequest,
    ) -> bool:

        artifact_type = (
            artifact_type
            .strip()
            .upper()
        )

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
                context.api_component_design.api_operations
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

    # Routes rule-specific applicability conditions
    def _passes_applicability_handler(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> bool:

        if not rule.applicability_handler:
            return True

        handlers = {
            "database_has_foreign_keys":
                self._database_has_foreign_keys,

            "api_has_collection_get":
                self._api_has_collection_get,

            "api_has_state_changing_operation":
                self._api_has_state_changing_operation,

            "security_nfr_requires_api_access_control":
                self._security_nfr_requires_api_access_control,
        }

        handler = handlers.get(
            rule.applicability_handler
        )

        # Unknown applicability handlers should not make
        # a rule appear applicable
        if handler is None:
            return False

        return handler(
            context
        )

    # Checks whether at least one database entity
    # declares a foreign key
    def _database_has_foreign_keys(
        self,
        context: QualityEvaluationRequest,
    ) -> bool:

        return any(
            bool(entity.foreign_keys)
            for entity in context.database.entities
        )

    # Checks whether the OpenAPI document contains
    # at least one collection GET endpoint
    def _api_has_collection_get(
        self,
        context: QualityEvaluationRequest,
    ) -> bool:

        document = (
            context
            .api_component_design
            .openapi_document
        )

        paths = document.get(
            "paths",
            {},
        )

        if not isinstance(
            paths,
            dict,
        ):
            return False

        for path, path_item in paths.items():

            if not isinstance(
                path_item,
                dict,
            ):
                continue

            # Paths with path parameters normally
            # represent individual resources
            if "{" in path:
                continue

            operation = path_item.get(
                "get"
            )

            if isinstance(
                operation,
                dict,
            ):
                return True

        return False

    # Checks whether the API contains an operation
    # that changes server-side state
    def _api_has_state_changing_operation(
        self,
        context: QualityEvaluationRequest,
    ) -> bool:

        document = (
            context
            .api_component_design
            .openapi_document
        )

        paths = document.get(
            "paths",
            {},
        )

        if not isinstance(
            paths,
            dict,
        ):
            return False

        changing_methods = {
            "post",
            "put",
            "patch",
            "delete",
        }

        for path_item in paths.values():

            if not isinstance(
                path_item,
                dict,
            ):
                continue

            for method in changing_methods:

                operation = path_item.get(
                    method
                )

                if isinstance(
                    operation,
                    dict,
                ):
                    return True

        return False

    # Checks whether a Security NFR explicitly requires
    # authentication, authorization, or access control
    def _security_nfr_requires_api_access_control(
        self,
        context: QualityEvaluationRequest,
    ) -> bool:

        security_nfrs = [
            nfr
            for nfr
            in context.non_functional_requirements
            if nfr.category == NFRCategory.SECURITY
        ]

        if not security_nfrs:
            return False

        patterns = [
            r"\bauthentication\b",
            r"\bauthenticate\b",
            r"\bauthenticated\b",
            r"\bauthorization\b",
            r"\bauthorisation\b",
            r"\bauthorize\b",
            r"\bauthorise\b",
            r"\bauthorized\b",
            r"\bauthorised\b",
            r"\baccess control\b",
            r"\baccess-controlled\b",
            r"\brole-based access\b",
            r"\brbac\b",
            r"\bprotected api\b",
            r"\bprotected endpoint\b",
            r"\bprotected operation\b",
            r"\bprotected resource\b",
        ]

        combined_pattern = re.compile(
            "|".join(patterns),
            re.IGNORECASE,
        )

        for nfr in security_nfrs:

            statement = (
                nfr.statement
                or ""
            )

            if combined_pattern.search(
                statement
            ):
                return True

        return False