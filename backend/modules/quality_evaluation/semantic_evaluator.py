import json
import logging

from .llm.provider import (
    BaseQualityLLMProvider,
)
from .llm.structured_schemas import (
    LLMQualityAssessment,
)
from .schemas import (
    CheckType,
    QualityEvaluationRequest,
    QualityRule,
    RuleEvaluationResult,
    RuleStatus,
)


logger = logging.getLogger(__name__)


class SemanticEvaluator:

    def __init__(
        self,
        provider: (
            BaseQualityLLMProvider
            | None
        ),
    ):
        self.provider = provider

    def evaluate(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> RuleEvaluationResult:

        matching_nfr_ids = {
            nfr.requirement_id
            for nfr
            in context.non_functional_requirements
            if nfr.category
            in rule.nfr_categories
        }

        if self.provider is None:
            return RuleEvaluationResult(
                rule_id=rule.rule_id,
                quality_attribute=(
                    rule.quality_attribute
                ),
                check_type=(
                    CheckType.SEMANTIC
                ),
                status=(
                    RuleStatus.SKIPPED
                ),
                evidence=[],
                rationale=(
                    "Semantic evaluation was not "
                    "available for this run."
                ),
                affected_nfr_ids=[],
            )

        prompt = self._build_prompt(
            rule,
            context,
        )

        try:
            assessment = (
                self.provider
                .generate_structured(
                    prompt,
                    LLMQualityAssessment,
                )
            )

        except Exception:
            logger.exception(
                (
                    "Semantic quality evaluation "
                    "failed for rule %s."
                ),
                rule.rule_id,
            )

            return RuleEvaluationResult(
                rule_id=rule.rule_id,
                quality_attribute=(
                    rule.quality_attribute
                ),
                check_type=(
                    CheckType.SEMANTIC
                ),
                status=(
                    RuleStatus.SKIPPED
                ),
                evidence=[],
                rationale=(
                    "Semantic evaluation could not "
                    "be completed because the LLM "
                    "provider was unavailable."
                ),
                affected_nfr_ids=[],
            )

        valid_nfr_ids = {
            nfr.requirement_id
            for nfr
            in context.non_functional_requirements
        }

        affected_nfr_ids = [
            nfr_id
            for nfr_id
            in assessment.affected_nfr_ids
            if nfr_id in valid_nfr_ids
        ]

        if (
            not affected_nfr_ids
            and matching_nfr_ids
            and assessment.status
            != "SKIPPED"
        ):
            affected_nfr_ids = sorted(
                matching_nfr_ids
            )

        provider_name = getattr(
            self.provider,
            "last_provider_name",
            None,
        )

        if not provider_name:
            provider_name = getattr(
                self.provider,
                "name",
                None,
            )

        return RuleEvaluationResult(
            rule_id=rule.rule_id,

            quality_attribute=(
                rule.quality_attribute
            ),

            check_type=(
                CheckType.SEMANTIC
            ),

            status=RuleStatus(
                assessment.status
            ),

            evidence=(
                assessment.evidence
            ),

            rationale=(
                assessment.rationale
            ),

            affected_nfr_ids=(
                affected_nfr_ids
            ),

            confidence=(
                assessment.confidence
            ),

            provider=provider_name,
        )

    def _build_prompt(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> str:

        context_json = json.dumps(
            context.model_dump(
                mode="json"
            ),
            indent=2,
        )

        if len(context_json) > 20000:
            context_json = (
                context_json[:20000]
                + "\n[context truncated]"
            )

        return f"""
You are evaluating one software-design quality rule for DesignTrace AI.

Evaluate ONLY the supplied rule.

Important constraints:

- Use only the supplied artifacts and requirements.
- Do not invent missing architecture, database, API, UI, infrastructure, legal, authentication or deployment details.
- Return PASS only when the supplied evidence supports the rule.
- Return FAIL when the supplied evidence clearly shows a quality problem.
- Return SKIPPED when the available artifacts are insufficient to make a justified judgement.
- Legal evaluation means design-evidence traceability only. Do not provide legal advice.
- Security evaluation must not invent JWT, OAuth2, API keys, roles or authentication mechanisms.
- affected_nfr_ids must contain only IDs that exist in the supplied input.
- Evidence must refer to the supplied artifacts.
- Recommendation should be concise and actionable when status is FAIL.
- Do not return Markdown.
- Do not return explanatory text outside the structured response.

Rule ID:
{rule.rule_id}

Quality category:
{rule.quality_attribute.value}

Rule title:
{rule.title}

Applicability:
{rule.applicability}

Semantic instruction:
{rule.semantic_instruction}

Default recommendation:
{rule.recommendation_template}

Project artifacts:
{context_json}
""".strip()