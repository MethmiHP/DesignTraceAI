from collections import defaultdict

from .schemas import (
    QualityFinding,
    QualityFindingGroup,
    QualityRule,
    Severity,
)


class QualityFindingGrouper:

    # Severity order used when a group contains
    # findings with different severity levels
    SEVERITY_ORDER = {
        Severity.LOW: 1,
        Severity.MEDIUM: 2,
        Severity.HIGH: 3,
        Severity.CRITICAL: 4,
    }

    def group(
        self,
        findings: list[QualityFinding],
        rules: list[QualityRule],
    ) -> list[QualityFindingGroup]:

        # Create rule lookup
        rules_by_id = {
            rule.rule_id: rule
            for rule in rules
        }

        grouped_findings: dict[
            str,
            list[QualityFinding],
        ] = defaultdict(list)

        # Put findings into a group only when
        # their rule explicitly defines a group key
        for finding in findings:

            rule = rules_by_id.get(
                finding.rule_id
            )

            if rule is None:
                continue

            if not rule.finding_group:
                continue

            grouped_findings[
                rule.finding_group
            ].append(
                finding
            )

        result: list[
            QualityFindingGroup
        ] = []

        group_number = 1

        for (
            group_key,
            related_findings,
        ) in grouped_findings.items():

            # A single finding does not need grouping
            if len(related_findings) < 2:
                continue

            severity = self._highest_severity(
                related_findings
            )

            quality_attribute = (
                self._quality_attribute(
                    related_findings
                )
            )

            affected_nfr_ids = (
                self._unique_values(
                    [
                        nfr_id
                        for finding
                        in related_findings
                        for nfr_id
                        in finding.affected_nfr_ids
                    ]
                )
            )

            rule_ids = (
                self._unique_values(
                    [
                        finding.rule_id
                        for finding
                        in related_findings
                    ]
                )
            )

            finding_ids = [
                finding.finding_id
                for finding
                in related_findings
            ]

            recommendations = (
                self._unique_values(
                    [
                        finding.recommendation
                        for finding
                        in related_findings
                        if finding.recommendation
                    ]
                )
            )

            title = self._build_title(
                group_key
            )

            summary = (
                self._build_summary(
                    title,
                    quality_attribute,
                    related_findings,
                )
            )

            result.append(
                QualityFindingGroup(
                    group_id=(
                        f"QG-{group_number:03d}"
                    ),
                    group_key=group_key,
                    title=title,
                    quality_attribute=(
                        quality_attribute
                    ),
                    severity=severity,
                    finding_ids=finding_ids,
                    rule_ids=rule_ids,
                    affected_nfr_ids=(
                        affected_nfr_ids
                    ),
                    recommendations=(
                        recommendations
                    ),
                    summary=summary,
                )
            )

            group_number += 1

        return result

    # Returns the highest severity
    # from all findings in the group
    def _highest_severity(
        self,
        findings: list[QualityFinding],
    ) -> Severity:

        return max(
            (
                finding.severity
                for finding in findings
            ),
            key=lambda severity: (
                self.SEVERITY_ORDER[
                    severity
                ]
            ),
        )

    # Uses a common quality attribute
    # when all findings belong to the same one
    def _quality_attribute(
        self,
        findings: list[QualityFinding],
    ) -> str:

        attributes = {
            finding.quality_attribute.value
            for finding in findings
        }

        if len(attributes) == 1:
            return next(
                iter(attributes)
            )

        return "Cross-category"

    # Removes duplicate values while
    # preserving their original order
    def _unique_values(
        self,
        values: list[str],
    ) -> list[str]:

        return list(
            dict.fromkeys(
                values
            )
        )

    # Converts the internal group key
    # into a readable frontend title
    def _build_title(
        self,
        group_key: str,
    ) -> str:

        return (
            group_key
            .replace("_", " ")
            .strip()
            .title()
        )

    # Creates a deterministic group summary
    def _build_summary(
        self,
        title: str,
        quality_attribute: str,
        findings: list[QualityFinding],
    ) -> str:

        return (
            f"{len(findings)} related "
            f"{quality_attribute} findings "
            f"were detected for "
            f"{title}."
        )
