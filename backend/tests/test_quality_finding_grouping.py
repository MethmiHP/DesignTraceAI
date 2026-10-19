from modules.quality_evaluation.finding_grouper import (
    QualityFindingGrouper,
)
from modules.quality_evaluation.rule_repository import (
    QualityRuleRepository,
)
from modules.quality_evaluation.schemas import (
    CheckType,
    QualityFinding,
    Severity,
)


def load_rules():
    repository = (
        QualityRuleRepository()
    )

    return repository.load_rules()


def build_security_findings():
    return [
        QualityFinding(
            finding_id="QF-001",
            rule_id="SEC-001",
            artifact_type="MULTI",
            quality_attribute="Security",
            check_type=(
                CheckType.SEMANTIC
            ),
            severity=Severity.HIGH,
            affected_nfr_ids=[
                "NFR-SEC-001"
            ],
            evidence=[
                (
                    "A security-sensitive "
                    "operation has no explicit "
                    "security requirement."
                )
            ],
            rationale=(
                "The operation requires "
                "explicit protection."
            ),
            recommendation=(
                "Define explicit authentication "
                "and authorization requirements."
            ),
        ),
        QualityFinding(
            finding_id="QF-002",
            rule_id="SEC-002",
            artifact_type="MULTI",
            quality_attribute="Security",
            check_type=(
                CheckType.DETERMINISTIC
            ),
            severity=Severity.HIGH,
            affected_nfr_ids=[
                "NFR-SEC-001"
            ],
            evidence=[
                (
                    "OpenAPI security declaration "
                    "is missing."
                )
            ],
            rationale=(
                "The API contract does not "
                "represent the security NFR."
            ),
            recommendation=(
                "Define and apply an explicit "
                "API security scheme."
            ),
        ),
    ]


def test_related_security_findings_are_grouped():
    grouper = (
        QualityFindingGrouper()
    )

    groups = grouper.group(
        build_security_findings(),
        load_rules(),
    )

    assert len(groups) == 1

    group = groups[0]

    assert (
        group.group_key
        == "API_ACCESS_CONTROL"
    )

    assert (
        group.quality_attribute
        == "Security"
    )

    assert (
        group.severity
        == Severity.HIGH
    )

    assert set(
        group.rule_ids
    ) == {
        "SEC-001",
        "SEC-002",
    }

    assert set(
        group.finding_ids
    ) == {
        "QF-001",
        "QF-002",
    }


def test_group_keeps_affected_nfr():
    grouper = (
        QualityFindingGrouper()
    )

    groups = grouper.group(
        build_security_findings(),
        load_rules(),
    )

    assert (
        groups[0]
        .affected_nfr_ids
        == [
            "NFR-SEC-001"
        ]
    )


def test_group_keeps_both_recommendations():
    grouper = (
        QualityFindingGrouper()
    )

    groups = grouper.group(
        build_security_findings(),
        load_rules(),
    )

    recommendations = (
        groups[0]
        .recommendations
    )

    assert len(
        recommendations
    ) == 2

    assert (
        "Define explicit authentication "
        "and authorization requirements."
        in recommendations
    )

    assert (
        "Define and apply an explicit "
        "API security scheme."
        in recommendations
    )


def test_group_summary_is_created():
    grouper = (
        QualityFindingGrouper()
    )

    groups = grouper.group(
        build_security_findings(),
        load_rules(),
    )

    group = groups[0]

    assert (
        group.title
        == "Api Access Control"
    )

    assert (
        group.summary
        == (
            "2 related Security findings "
            "were detected for "
            "Api Access Control."
        )
    )


def test_single_grouped_finding_is_not_grouped():
    grouper = (
        QualityFindingGrouper()
    )

    findings = (
        build_security_findings()
    )

    groups = grouper.group(
        [
            findings[0]
        ],
        load_rules(),
    )

    assert groups == []