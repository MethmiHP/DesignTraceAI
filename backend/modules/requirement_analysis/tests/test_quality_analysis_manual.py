# Manually tests the Requirement Analysis service for requirement-quality issues
# such as ambiguity, incompleteness, conflicts, and potentially missing requirements.
# Each test case is processed through the full analysis pipeline and the detected
# classification, ASR status, quality issues, and issue details are printed.
import asyncio

from modules.requirement_analysis.schemas import (
    RequirementAnalysisRequest,
    ProjectContext,
)

from modules.requirement_analysis.service import (
    RequirementAnalysisService
)


TEST_CASES = [
    {
        "name": "Ambiguity",
        "text": "The system should be fast."
    },
    {
        "name": "Incompleteness",
        "text": "The system shall respond within 2 seconds."
    },
    {
        "name": "Conflict",
        "text": (
            "The system shall allow all users to access patient records. "
            "The system shall restrict patient records to authorized users only."
        )
    },
    {
        "name": "Potentially Missing",
        "text": (
            "Patients shall be able to book appointments online. "
            "Patients shall be able to cancel appointments."
        )
    },
]


async def main():

    service = RequirementAnalysisService()

    for case in TEST_CASES:

        print("\n" + "=" * 70)
        print(case["name"])
        print("=" * 70)

        request = RequirementAnalysisRequest(
            project_id=f"TEST-{case['name'].upper().replace(' ', '-')}",

            raw_description=case["text"],

            project_context=ProjectContext(
                domain="Healthcare",
                project_type="Web Application",
                description="Hospital appointment management system"
            )
        )

        result = await service.analyze(
            request
        )

        for requirement in result.requirements:

            print(
                "\nRequirement ID:",
                requirement.requirement_id
            )

            print(
                "Original:",
                requirement.original_text
            )

            print(
                "Normalized:",
                requirement.normalized_statement
            )

            print(
                "Type:",
                requirement.requirement_type
            )

            print(
                "Quality Attribute:",
                requirement.quality_attribute
            )

            print(
                "ASR:",
                requirement.asr
            )

            print(
                "Quality Issues:",
                requirement.quality_issues.model_dump()
            )

            print(
                "Issue Details:"
            )

            for issue in requirement.issue_details:
                print(
                    issue.model_dump()
                )


if __name__ == "__main__":
    asyncio.run(
        main()
    )