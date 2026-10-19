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

        quality_pass = (
            f"{metrics.quality_pass_percentage}%"
            if metrics.quality_pass_percentage is not None
            else "Not applicable"
        )
        coverage = (
            f"{metrics.nfr_coverage_percentage}%"
            if metrics.nfr_coverage_percentage is not None
            else "Not applicable"
        )

        if not findings:
            return (
                "No quality issues were detected by "
                "the applicable evaluation rules. "
                f"Quality Pass: "
                f"{quality_pass}. "
                f"NFR Coverage: "
                f"{coverage}."
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
            f"{quality_pass}. "
            f"NFR Coverage: "
            f"{coverage}."
        )