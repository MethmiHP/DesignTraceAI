import json
import logging

from .llm.activity_logging import evaluation_log_context

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
            logger.info("[%s] skipped: LLM unavailable", rule.rule_id)
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
            prompts = self._bounded_prompts(prompt)
        except ValueError:
            logger.warning('[%s] skipped: evidence value exceeds request budget', rule.rule_id)
            return RuleEvaluationResult(
                rule_id=rule.rule_id, quality_attribute=rule.quality_attribute,
                check_type=CheckType.SEMANTIC, status=RuleStatus.SKIPPED,
                evidence=[], affected_nfr_ids=[],
                rationale='An individual evidence value exceeds the safe request budget; shorten that value before retrying.',
            )
        if len(prompts) > 1:
            logger.info('[%s] evaluating %s evidence parts', rule.rule_id, len(prompts))
        try:
            with evaluation_log_context(context.project_id, rule.rule_id):
                assessments = [self.provider.generate_structured(part, LLMQualityAssessment) for part in prompts]
                assessment = assessments[0]
                if len(assessments) > 1:
                    # Partial context cannot establish that a whole-design rule passes.
                    failures = [item for item in assessments if item.status == 'FAIL']
                    assessment = LLMQualityAssessment(
                        status='FAIL' if failures else 'SKIPPED',
                        evidence=[e for item in failures for e in item.evidence],
                        rationale='; '.join(item.rationale for item in failures) if failures else 'Evidence was evaluated in parts; a whole-design pass could not be established.',
                        recommendation='; '.join(item.recommendation for item in failures if item.recommendation) or None,
                        affected_nfr_ids=sorted({n for item in failures for n in item.affected_nfr_ids}),
                    )

        except Exception:
            logger.warning('[%s] skipped: providers failed', rule.rule_id)

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

            recommendation=assessment.recommendation,

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

        data = context.model_dump(mode='json', exclude_none=True)
        relevant = {'project_id': data['project_id']}
        for artifact, field in [('FR', 'functional_requirements'), ('ARCHITECTURE', 'architecture'), ('DATABASE', 'database')]:
            if artifact in rule.artifact_types:
                relevant[field] = data[field]
        relevant['non_functional_requirements'] = [n for n in data['non_functional_requirements'] if n['category'] in {c.value for c in rule.nfr_categories}]
        api = data['api_component_design']
        if 'API' in rule.artifact_types:
            relevant['api_component_design'] = {k: v for k, v in api.items() if k != 'responsibilities'}
        if 'COMPONENT' in rule.artifact_types:
            relevant.setdefault('api_component_design', {})['responsibilities'] = api['responsibilities']
        context_json = json.dumps(relevant, separators=(',', ':'), ensure_ascii=False)

        return f"""
You are evaluating one software-design quality rule for DesignTrace AI.

Evaluate ONLY the supplied rule.

Important constraints:

- Use only the supplied artifacts and requirements.
- Upstream scores, validation flags, recommendations, and retrieved general evidence are context, not proof that the actual design satisfies this rule.
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

    @staticmethod
    def _bounded_prompts(prompt, max_bytes=12000):
        """Bound input conservatively; retain all evidence, never silently truncate."""
        if len(prompt.encode('utf-8')) <= max_bytes:
            return [prompt]
        header, raw = prompt.split('Project artifacts:\n', 1)
        header += ('Partial project evidence follows as JSON path/value records. '
                   'Other evidence is in separate requests. Do not infer missing controls from omission. '
                   'Return FAIL only for a defect explicitly demonstrated within this part. '
                   'Otherwise return SKIPPED; a partial view cannot establish a whole-design PASS.\n')
        limit = max_bytes - len(header.encode('utf-8')) - 2
        records = []

        def visit(value, path):
            record = json.dumps({'path': path, 'value': value}, ensure_ascii=False, separators=(',', ':'))
            if len(record.encode('utf-8')) <= limit:
                records.append(record)
            elif isinstance(value, dict) and value:
                for key, child in value.items():
                    visit(child, path + [key])
            elif isinstance(value, list) and value:
                for index, child in enumerate(value):
                    visit(child, path + [index])
            else:
                raise ValueError('An individual evidence value exceeds the safe request budget.')

        visit(json.loads(raw), [])
        prompts, batch = [], []
        for record in records:
            if batch and len((','.join(batch + [record])).encode('utf-8')) > limit:
                prompts.append(header + '[' + ','.join(batch) + ']')
                batch = []
            batch.append(record)
        if batch:
            prompts.append(header + '[' + ','.join(batch) + ']')
        return prompts
