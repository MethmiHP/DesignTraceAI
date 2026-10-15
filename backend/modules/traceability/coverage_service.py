# Calculates traceability coverage statistics.

# Two forms of coverage are reported:

# 1. Requirement coverage
#    - A requirement is considered covered if it has at least
#      one valid requirement-to-design trace link.

# 2. Artifact-category coverage
#    - Measures how many of the four design artifact categories
#      are represented:
#        architecture
#        database
#        api
#        component

from modules.traceability.schemas import (
    TraceabilityMatrixRow,
    CoverageSummary,
)


class TraceabilityCoverageService:

    def calculate_coverage(
        self,
        matrix: list[TraceabilityMatrixRow],
    ) -> CoverageSummary:
    
        # Calculates requirement-level coverage and
        # artifact-category coverage.
        

        total_requirements = len(
            matrix
        )


        # EMPTY MATRIX

        if total_requirements == 0:

            return CoverageSummary(
                total_requirements=0,

                requirements_with_links=0,

                requirements_without_links=0,

                requirement_coverage_percentage=0.0,

                fully_covered=0,

                partially_covered=0,

                uncovered=0,

                average_artifact_category_coverage_percentage=0.0,
            )



        # REQUIREMENT COVERAGE

        requirements_with_links = sum(
            1
            for row in matrix
            if self._count_linked_categories(
                row
            ) > 0
        )

        requirements_without_links = (
            total_requirements
            - requirements_with_links
        )

        requirement_coverage_percentage = (
            requirements_with_links
            / total_requirements
        ) * 100


        # MATRIX STATUS COUNTS

        fully_covered = sum(
            1
            for row in matrix
            if (
                row.coverage_status
                == "FULLY_COVERED"
            )
        )

        partially_covered = sum(
            1
            for row in matrix
            if (
                row.coverage_status
                == "PARTIALLY_COVERED"
            )
        )

        uncovered = sum(
            1
            for row in matrix
            if (
                row.coverage_status
                == "UNCOVERED"
            )
        )


        # ARTIFACT-CATEGORY COVERAGE

        total_possible_categories = (
            total_requirements
            * 4
        )

        total_linked_categories = sum(
            self._count_linked_categories(
                row
            )
            for row in matrix
        )

        average_artifact_category_coverage_percentage = (
            total_linked_categories
            / total_possible_categories
        ) * 100


        # RETURN SUMMARY
        return CoverageSummary(
            total_requirements=
                total_requirements,

            requirements_with_links=
                requirements_with_links,

            requirements_without_links=
                requirements_without_links,

            requirement_coverage_percentage=
                round(
                    requirement_coverage_percentage,
                    2,
                ),

            fully_covered=
                fully_covered,

            partially_covered=
                partially_covered,

            uncovered=
                uncovered,

            average_artifact_category_coverage_percentage=
                round(
                    average_artifact_category_coverage_percentage,
                    2,
                ),
        )


    # HELPER

    def _count_linked_categories(
        self,
        row: TraceabilityMatrixRow,
    ) -> int:
        
        # Counts how many artifact categories contain at least
        # one valid trace link for one requirement.

        # Maximum = 4.
        

        return sum(
            [
                bool(
                    row.architecture_links
                ),

                bool(
                    row.database_links
                ),

                bool(
                    row.api_links
                ),

                bool(
                    row.component_links
                ),
            ]
        )