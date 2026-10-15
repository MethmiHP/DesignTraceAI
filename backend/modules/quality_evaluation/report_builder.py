from .schemas import (
    QualityFinding,
    QualityMetrics,
)


class QualityReportBuilder:

    def build_summary(
        self,
        metrics: QualityMetrics,
        findings: list[QualityFinding],
    ) -> str:

        if not findings:
            return (
                "No quality issues were detected by "
                "the applicable evaluation rules. "
                f"Quality Pass: "
                f"{metrics.quality_pass_percentage}%. "
                f"NFR Coverage: "
                f"{metrics.nfr_coverage_percentage}%."
            )

        severity_order = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4,
        }

        highest = max(
            findings,
            key=lambda finding: (
                severity_order[
                    finding.severity.value
                ]
            ),
        )

        return (
            f"{len(findings)} quality issue(s) "
            f"were detected. "
            f"Highest severity: "
            f"{highest.severity.value}. "
            f"Quality Pass: "
            f"{metrics.quality_pass_percentage}%. "
            f"NFR Coverage: "
            f"{metrics.nfr_coverage_percentage}%."
        )