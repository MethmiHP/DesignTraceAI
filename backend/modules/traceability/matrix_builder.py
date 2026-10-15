# Builds the requirement-to-design traceability matrix
# from filtered traceability links.

from collections import defaultdict

from modules.traceability.schemas import (
    TraceabilityRequirement,
    TraceLink,
    TraceabilityMatrixRow,
)


class TraceabilityMatrixBuilder:

    def build_matrix(
        self,
        requirements: list[TraceabilityRequirement],
        links: list[TraceLink],
    ) -> list[TraceabilityMatrixRow]:
       
        # Creates one traceability matrix row per requirement.
    

        grouped_links = defaultdict(
            lambda: {
                "architecture": [],
                "database": [],
                "api": [],
                "component": [],
            }
        )

        for link in links:

            grouped_links[
                link.requirement_id
            ][
                link.artifact_type
            ].append(
                link.artifact_id
            )

        matrix = []

        for requirement in requirements:

            requirement_links = grouped_links[
                requirement.requirement_id
            ]

            architecture_links = sorted(
                set(
                    requirement_links[
                        "architecture"
                    ]
                )
            )

            database_links = sorted(
                set(
                    requirement_links[
                        "database"
                    ]
                )
            )

            api_links = sorted(
                set(
                    requirement_links[
                        "api"
                    ]
                )
            )

            component_links = sorted(
                set(
                    requirement_links[
                        "component"
                    ]
                )
            )

            linked_categories = sum(
                [
                    bool(architecture_links),
                    bool(database_links),
                    bool(api_links),
                    bool(component_links),
                ]
            )

            if linked_categories == 4:
                coverage_status = (
                    "FULLY_COVERED"
                )

            elif linked_categories > 0:
                coverage_status = (
                    "PARTIALLY_COVERED"
                )

            else:
                coverage_status = (
                    "UNCOVERED"
                )

            matrix.append(
                TraceabilityMatrixRow(
                    requirement_id=
                        requirement.requirement_id,

                    architecture_links=
                        architecture_links,

                    database_links=
                        database_links,

                    api_links=
                        api_links,

                    component_links=
                        component_links,

                    coverage_status=
                        coverage_status,
                )
            )

        return matrix