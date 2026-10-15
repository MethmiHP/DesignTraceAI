from .schemas import (
    CategoryQualitySummary,
    NFRCategory,
    QualityEvaluationRequest,
    QualityMetrics,
    QualityRule,
    RuleEvaluationResult,
    RuleStatus,
)


class QualityMetricsCalculator:

    def calculate(
        self,
        context: QualityEvaluationRequest,
        rules: list[QualityRule],
        results: list[
            RuleEvaluationResult
        ],
    ) -> QualityMetrics:

        result_by_rule = {
            result.rule_id: result
            for result in results
        }

        passed = sum(
            1
            for result in results
            if result.status
            == RuleStatus.PASS
        )

        failed = sum(
            1
            for result in results
            if result.status
            == RuleStatus.FAIL
        )

        skipped = sum(
            1
            for result in results
            if result.status
            == RuleStatus.SKIPPED
        )

        total_applicable = len(
            rules
        )

        if total_applicable:
            quality_pass_percentage = (
                passed
                / total_applicable
                * 100
            )
        else:
            quality_pass_percentage = 100.0

        applicable_nfr_ids = (
            self._applicable_nfr_ids(
                context,
                rules,
            )
        )

        evaluated_nfr_ids = set()

        for result in results:

            if (
                result.status
                == RuleStatus.SKIPPED
            ):
                continue

            evaluated_nfr_ids.update(
                result.affected_nfr_ids
            )

        evaluated_nfr_ids &= (
            applicable_nfr_ids
        )

        if applicable_nfr_ids:
            nfr_coverage_percentage = (
                len(
                    evaluated_nfr_ids
                )
                / len(
                    applicable_nfr_ids
                )
                * 100
            )
        else:
            nfr_coverage_percentage = 100.0

        category_summaries = []

        for category in NFRCategory:

            category_rules = [
                rule
                for rule in rules
                if (
                    rule.quality_attribute
                    == category
                )
            ]

            category_results = [
                result_by_rule[
                    rule.rule_id
                ]
                for rule
                in category_rules
                if rule.rule_id
                in result_by_rule
            ]

            category_passed = sum(
                1
                for result
                in category_results
                if result.status
                == RuleStatus.PASS
            )

            category_failed = sum(
                1
                for result
                in category_results
                if result.status
                == RuleStatus.FAIL
            )

            category_skipped = sum(
                1
                for result
                in category_results
                if result.status
                == RuleStatus.SKIPPED
            )

            category_applicable = len(
                category_rules
            )

            if category_applicable:
                category_pass = (
                    category_passed
                    / category_applicable
                    * 100
                )
            else:
                category_pass = None

            category_nfr_ids = {
                nfr.requirement_id
                for nfr
                in (
                    context
                    .non_functional_requirements
                )
                if nfr.category
                == category
            }

            category_evaluated = (
                category_nfr_ids
                & evaluated_nfr_ids
            )

            if category_nfr_ids:
                category_coverage = (
                    len(
                        category_evaluated
                    )
                    / len(
                        category_nfr_ids
                    )
                    * 100
                )
            else:
                category_coverage = None

            category_summaries.append(
                CategoryQualitySummary(
                    category=category,

                    applicable_rules=(
                        category_applicable
                    ),

                    passed_rules=(
                        category_passed
                    ),

                    failed_rules=(
                        category_failed
                    ),

                    skipped_rules=(
                        category_skipped
                    ),

                    pass_percentage=(
                        round(
                            category_pass,
                            2,
                        )
                        if category_pass
                        is not None
                        else None
                    ),

                    applicable_nfrs=len(
                        category_nfr_ids
                    ),

                    evaluated_nfrs=len(
                        category_evaluated
                    ),

                    nfr_coverage_percentage=(
                        round(
                            category_coverage,
                            2,
                        )
                        if category_coverage
                        is not None
                        else None
                    ),
                )
            )

        return QualityMetrics(
            total_applicable_rules=(
                total_applicable
            ),

            passed_rules=passed,
            failed_rules=failed,
            skipped_rules=skipped,

            quality_pass_percentage=round(
                quality_pass_percentage,
                2,
            ),

            applicable_nfrs=len(
                applicable_nfr_ids
            ),

            evaluated_nfrs=len(
                evaluated_nfr_ids
            ),

            nfr_coverage_percentage=round(
                nfr_coverage_percentage,
                2,
            ),

            category_summaries=(
                category_summaries
            ),
        )

    def _applicable_nfr_ids(
        self,
        context: QualityEvaluationRequest,
        rules: list[QualityRule],
    ) -> set[str]:

        supported_categories = {
            category
            for rule in rules
            for category
            in rule.nfr_categories
        }

        return {
            nfr.requirement_id
            for nfr
            in context.non_functional_requirements
            if nfr.category
            in supported_categories
        }