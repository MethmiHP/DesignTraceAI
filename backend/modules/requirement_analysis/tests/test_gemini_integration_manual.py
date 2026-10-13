# Demonstrates the complete Requirement Analysis pipeline using a sample
# healthcare project. The script sends the project description through the
# full service, including trained classifiers, rule-based checks, Gemini-based
# analysis, validation, and structured output generation.

import asyncio

from modules.requirement_analysis.schemas import (
    RequirementAnalysisRequest,
    ProjectContext,
)

from modules.requirement_analysis.service import (
    RequirementAnalysisService
)


async def main():

    service = RequirementAnalysisService()

    request = RequirementAnalysisRequest(
        project_id="DEMO-001",

        raw_description=(
            "Patients should be able to book appointments online. "
            "The system shall encrypt all patient information. "
            "The system should respond within 2 seconds."
        ),

        project_context=ProjectContext(
            domain="Healthcare",
            project_type="Web Application",
            description="Hospital appointment management system"
        )
    )

    print("Running full Requirement Analysis pipeline with Gemini...")

    result = await service.analyze(
        request
    )

    print("\nAnalysis completed.\n")

    print(
        result.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )