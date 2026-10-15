from .schemas import (
    QualityRule,
    RuleEvaluationResult,
)


class RecommendationGenerator:

    def generate(
        self,
        rule: QualityRule,
        result: RuleEvaluationResult,
        semantic_recommendation: str | None = None,
    ) -> str:

        if (
            semantic_recommendation
            and semantic_recommendation.strip()
        ):
            return (
                semantic_recommendation.strip()
            )

        return (
            rule
            .recommendation_template
            .strip()
        )