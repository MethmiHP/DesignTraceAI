"""
Deterministic significance detection for design decisions.

The detector identifies whether a design decision is important enough
to be documented as an Architecture Decision Record (ADR).

The rules are intentionally transparent so that each result can be
explained and evaluated against human-reviewed significance labels.
"""

from modules.adr.schemas import (
    DesignDecision,
    DecisionSource,
    SignificanceCriteria,
    SignificanceResult,
)


class ADRSignificanceDetector:
    """
    Evaluates the architectural significance of a design decision.

    The detector uses explicit criteria derived from the ADR research
    methodology rather than treating every design output as an ADR.
    """

    SIGNIFICANCE_THRESHOLD = 0.40

    CRITERIA_WEIGHTS = {
        "architecture_impact": 0.20,
        "quality_attribute_impact": 0.15,
        "cross_component_impact": 0.15,
        "long_term_impact": 0.15,
        "difficult_to_reverse": 0.15,
        "contains_trade_offs": 0.10,
        "security_or_compliance_impact": 0.10,
    }

    ARCHITECTURE_KEYWORDS = {
        "architecture",
        "microservices",
        "microservice",
        "monolith",
        "modular monolith",
        "layered",
        "event-driven",
        "event driven",
        "service boundary",
        "component boundary",
        "deployment",
        "database",
        "data model",
        "api style",
        "rest",
        "graphql",
        "grpc",
    }

    QUALITY_KEYWORDS = {
        "security",
        "scalability",
        "scalable",
        "performance",
        "reliability",
        "availability",
        "maintainability",
        "latency",
        "fault isolation",
        "consistency",
        "integrity",
        "throughput",
        "resilience",
    }

    LONG_TERM_KEYWORDS = {
        "architecture",
        "database",
        "schema",
        "data model",
        "api",
        "authentication",
        "authorization",
        "deployment",
        "protocol",
        "framework",
        "technology",
        "service boundary",
        "component boundary",
    }

    DIFFICULT_TO_REVERSE_KEYWORDS = {
        "architecture",
        "database",
        "schema",
        "data model",
        "microservices",
        "monolith",
        "rest",
        "graphql",
        "grpc",
        "authentication",
        "authorization",
        "protocol",
        "deployment",
    }

    SECURITY_KEYWORDS = {
        "security",
        "authentication",
        "authorization",
        "token",
        "encryption",
        "privacy",
        "compliance",
        "access control",
        "credential",
        "sensitive",
    }

    def evaluate(
        self,
        decision: DesignDecision,
    ) -> SignificanceResult:
        """
        Evaluate one design decision and return an explainable
        significance result.
        """

        combined_text = self._build_combined_text(decision)

        architecture_impact = self._has_architecture_impact(
            decision,
            combined_text,
        )

        quality_attribute_impact = self._contains_keyword(
            combined_text,
            self.QUALITY_KEYWORDS,
        )

        cross_component_impact = self._has_cross_component_impact(
            decision,
            combined_text,
        )

        long_term_impact = self._contains_keyword(
            combined_text,
            self.LONG_TERM_KEYWORDS,
        )

        difficult_to_reverse = self._contains_keyword(
            combined_text,
            self.DIFFICULT_TO_REVERSE_KEYWORDS,
        )

        contains_trade_offs = bool(
            decision.trade_offs
            or len(decision.alternatives) >= 2
            or decision.rejected_alternative_reasons
        )

        security_or_compliance_impact = self._contains_keyword(
            combined_text,
            self.SECURITY_KEYWORDS,
        )

        criteria = SignificanceCriteria(
            architecture_impact=architecture_impact,
            quality_attribute_impact=quality_attribute_impact,
            cross_component_impact=cross_component_impact,
            long_term_impact=long_term_impact,
            difficult_to_reverse=difficult_to_reverse,
            contains_trade_offs=contains_trade_offs,
            security_or_compliance_impact=security_or_compliance_impact,
        )

        score = self._calculate_score(criteria)

        significant = score >= self.SIGNIFICANCE_THRESHOLD

        reasons = self._build_reasons(criteria)

        if significant:
            reasons.append(
                f"Significance score {score:.2f} meets the "
                f"{self.SIGNIFICANCE_THRESHOLD:.2f} ADR threshold."
            )
        else:
            reasons.append(
                f"Significance score {score:.2f} is below the "
                f"{self.SIGNIFICANCE_THRESHOLD:.2f} ADR threshold."
            )

        return SignificanceResult(
            decision_id=decision.decision_id,
            significant=significant,
            score=round(score, 4),
            criteria=criteria,
            reasons=reasons,
        )

    def _has_architecture_impact(
        self,
        decision: DesignDecision,
        text: str,
    ) -> bool:
        """
        Detect whether the decision has architectural impact.
        """

        architecture_sources = {
            DecisionSource.ARCHITECTURE_DECISION,
            DecisionSource.DATABASE_DESIGN,
            DecisionSource.API_COMPONENT_DESIGN,
        }

        if decision.source_module in architecture_sources:
            return True

        return self._contains_keyword(
            text,
            self.ARCHITECTURE_KEYWORDS,
        )

    def _has_cross_component_impact(
        self,
        decision: DesignDecision,
        text: str,
    ) -> bool:
        """
        Detect whether multiple design elements or components
        are affected by the decision.
        """

        if len(set(decision.design_element_ids)) >= 2:
            return True

        cross_component_keywords = {
            "multiple components",
            "multiple services",
            "all services",
            "system-wide",
            "system wide",
            "cross-component",
            "cross component",
            "shared service",
            "independent services",
        }

        return self._contains_keyword(
            text,
            cross_component_keywords,
        )

    def _calculate_score(
        self,
        criteria: SignificanceCriteria,
    ) -> float:
        """
        Calculate weighted significance score between 0 and 1.
        """

        score = 0.0

        for criterion_name, weight in self.CRITERIA_WEIGHTS.items():
            if getattr(criteria, criterion_name):
                score += weight

        return score

    @staticmethod
    def _contains_keyword(
        text: str,
        keywords: set[str],
    ) -> bool:
        """
        Check whether the decision text contains any relevant keyword.
        """

        normalized_text = text.lower()

        return any(
            keyword.lower() in normalized_text
            for keyword in keywords
        )

    @staticmethod
    def _build_combined_text(
        decision: DesignDecision,
    ) -> str:
        """
        Combine available decision evidence for rule evaluation.
        """

        values = [
            decision.title,
            decision.decision,
            decision.context,
            decision.rationale or "",
            *decision.decision_criteria,
            *decision.benefits,
            *decision.risks,
            *decision.consequences,
            *decision.trade_offs,
            *decision.alternatives,
            *decision.rejected_alternative_reasons,
            *decision.evidence,
        ]

        return " ".join(values).lower()

    @staticmethod
    def _build_reasons(
        criteria: SignificanceCriteria,
    ) -> list[str]:
        """
        Produce human-readable explanations for triggered criteria.
        """

        reasons = []

        if criteria.architecture_impact:
            reasons.append(
                "The decision has an architectural or structural impact."
            )

        if criteria.quality_attribute_impact:
            reasons.append(
                "The decision affects one or more important quality attributes."
            )

        if criteria.cross_component_impact:
            reasons.append(
                "The decision affects multiple components or design elements."
            )

        if criteria.long_term_impact:
            reasons.append(
                "The decision can have long-term effects on the system design."
            )

        if criteria.difficult_to_reverse:
            reasons.append(
                "The decision may require significant effort to reverse later."
            )

        if criteria.contains_trade_offs:
            reasons.append(
                "The decision contains alternatives, rejection reasons, or trade-offs."
            )

        if criteria.security_or_compliance_impact:
            reasons.append(
                "The decision affects security or compliance concerns."
            )

        return reasons