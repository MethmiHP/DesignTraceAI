from evaluation.traceability.evaluate_traceability_p003 import (
    load_p003_project,
)

from modules.traceability.traceability_service import (
    TraceabilityService,
)


def main():

    print("TRACEABILITY SERVICE INTEGRATION TEST - P003")

    request = load_p003_project()

    service = TraceabilityService()

    response = service.analyze(
        request
    )

    print("\nPROJECT:")
    print(
        response.project_id
    )

    print("\nFINAL TRACE LINKS:")
    for link in response.trace_links:

        print(
            link.requirement_id,
            "->",
            link.artifact_id,
            link.artifact_type,
            "confidence=",
            link.confidence,
        )

    print("\nTRACEABILITY MATRIX:")
    for row in response.traceability_matrix:

        print(
            row.model_dump()
        )

    print("\nCOVERAGE SUMMARY:")
    print(
        response.coverage_summary.model_dump()
    )

    print("\nVALIDATION:")
    print(
        response.validation.model_dump()
    )


if __name__ == "__main__":
    main()