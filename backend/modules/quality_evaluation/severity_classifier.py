from .schemas import (
    QualityRule,
    RuleEvaluationResult,
    RuleStatus,
    Severity,
)


class SeverityClassifier:

    def classify(
        self,
        rule: QualityRule,
        result: RuleEvaluationResult,
    ) -> Severity | None:

        if result.status != RuleStatus.FAIL:
            return None

        return rule.severity_default