"""
Build ADR Significance Seed Dataset V2.

This version improves the first seed dataset by:
- adding a domain column
- reducing duplicate text
- adding realistic domain-specific variation
- keeping the dataset balanced
- keeping labels provisional for later human/expert review

The generated dataset contains:
- 100 decisions
- 50 significant
- 50 not significant
- 25 examples from each major source module
"""

import csv
from pathlib import Path


OUTPUT_PATH = (
    Path(__file__).resolve().parent
    / "raw"
    / "adr_significance_dataset.csv"
)


FIELDNAMES = [
    "decision_id",
    "source_module",
    "domain",
    "title",
    "context",
    "decision",
    "rationale",
    "alternatives",
    "trade_offs",
    "requirement_ids",
    "design_element_ids",
    "scenario_family",
    "difficulty",
    "label",
    "label_source",
    "review_status",
]


DOMAINS = [
    {
        "name": "banking",
        "system": "online banking platform",
        "entity": "transaction",
        "users": "bank customers",
        "data": "financial transaction data",
    },
    {
        "name": "healthcare",
        "system": "hospital management platform",
        "entity": "appointment",
        "users": "patients and clinical staff",
        "data": "patient and medical data",
    },
    {
        "name": "ecommerce",
        "system": "e-commerce platform",
        "entity": "order",
        "users": "online shoppers",
        "data": "order and payment data",
    },
    {
        "name": "logistics",
        "system": "logistics management platform",
        "entity": "shipment",
        "users": "dispatchers and drivers",
        "data": "shipment and delivery data",
    },
    {
        "name": "education",
        "system": "university learning platform",
        "entity": "course",
        "users": "students and lecturers",
        "data": "student and course data",
    },
]


CONTEXT_VARIANTS = [
    "during normal daily operation",
    "during peak workload periods",
    "for externally accessed workflows",
    "for future system expansion",
    "for high-volume production use",
]


def join_items(items):
    return "|".join(items)


def make_row(
    decision_id,
    source_module,
    domain,
    title,
    context,
    decision,
    rationale,
    alternatives,
    trade_offs,
    requirement_ids,
    design_element_ids,
    scenario_family,
    difficulty,
    label,
):
    return {
        "decision_id": decision_id,
        "source_module": source_module,
        "domain": domain,
        "title": title,
        "context": context,
        "decision": decision,
        "rationale": rationale,
        "alternatives": join_items(alternatives),
        "trade_offs": join_items(trade_offs),
        "requirement_ids": join_items(requirement_ids),
        "design_element_ids": join_items(design_element_ids),
        "scenario_family": scenario_family,
        "difficulty": difficulty,
        "label": label,
        "label_source": "developer_provisional",
        "review_status": "pending_review",
    }


# ---------------------------------------------------------------------
# Architecture Decision scenarios
# ---------------------------------------------------------------------


def architecture_significant(domain, variant, index):
    scenarios = [
        {
            "family": "architecture_style_selection",
            "difficulty": "easy",
            "title": "Select Primary Architecture Style",
            "decision": "Adopt Microservices as the primary architecture style.",
            "rationale": (
                "Independent services can scale and deploy separately "
                "while improving fault isolation."
            ),
            "alternatives": [
                "Layered Architecture",
                "Modular Monolith",
            ],
            "trade_offs": [
                "Higher operational complexity for greater scalability."
            ],
        },
        {
            "family": "event_driven_architecture",
            "difficulty": "medium",
            "title": "Introduce Event-Driven Communication",
            "decision": (
                "Use event-driven communication for asynchronous workflows."
            ),
            "rationale": (
                "Event-based communication reduces direct coupling "
                "between major components."
            ),
            "alternatives": [
                "Synchronous REST communication only",
            ],
            "trade_offs": [
                "Improved decoupling introduces event-management complexity."
            ],
        },
        {
            "family": "service_boundary",
            "difficulty": "medium",
            "title": "Create Independent Business Service",
            "decision": (
                f"Implement the {domain['entity']} capability as "
                "an independently deployable service."
            ),
            "rationale": (
                "The capability has independent scaling and deployment needs."
            ),
            "alternatives": [
                "Keep the capability inside the main application",
            ],
            "trade_offs": [
                "Independent deployment introduces network communication."
            ],
        },
        {
            "family": "api_gateway",
            "difficulty": "medium",
            "title": "Introduce API Gateway",
            "decision": (
                "Use an API Gateway as the single external service entry point."
            ),
            "rationale": (
                "The gateway centralises routing, authentication "
                "and cross-cutting concerns."
            ),
            "alternatives": [
                "Expose services directly",
            ],
            "trade_offs": [
                "Centralised control introduces another infrastructure component."
            ],
        },
        {
            "family": "deployment_topology",
            "difficulty": "hard",
            "title": "Use Multi-Zone Deployment",
            "decision": (
                "Deploy critical application components across multiple zones."
            ),
            "rationale": (
                "Redundant deployment reduces the effect of infrastructure failure."
            ),
            "alternatives": [
                "Single-zone deployment",
            ],
            "trade_offs": [
                "Higher infrastructure cost for increased availability."
            ],
        },
    ]

    scenario = scenarios[index % len(scenarios)]

    context = (
        f"The {domain['system']} requires architectural support "
        f"for {domain['entity']} processing {variant}."
    )

    return scenario, context


def architecture_minor(domain, variant, index):
    scenarios = [
        {
            "family": "component_naming",
            "difficulty": "easy",
            "title": "Rename Internal Component",
            "decision": (
                f"Rename the internal {domain['entity']} helper component."
            ),
            "rationale": "The new name follows the current naming convention.",
        },
        {
            "family": "diagram_layout",
            "difficulty": "easy",
            "title": "Rearrange Architecture Diagram",
            "decision": (
                f"Move the {domain['entity']} component to a clearer "
                "position in the architecture diagram."
            ),
            "rationale": "The change improves visual readability only.",
        },
        {
            "family": "package_name",
            "difficulty": "easy",
            "title": "Rename Internal Package",
            "decision": (
                f"Rename the package containing {domain['entity']} "
                "helper classes."
            ),
            "rationale": "The rename improves code organisation.",
        },
        {
            "family": "documentation_text",
            "difficulty": "medium",
            "title": "Update Architecture Description",
            "decision": (
                f"Rewrite the documentation describing the "
                f"{domain['entity']} component."
            ),
            "rationale": "Only the documentation wording is changed.",
        },
        {
            "family": "diagram_styling",
            "difficulty": "easy",
            "title": "Change Architecture Diagram Styling",
            "decision": (
                f"Change the visual style of the {domain['entity']} "
                "element in the architecture diagram."
            ),
            "rationale": "The design behaviour is unchanged.",
        },
    ]

    scenario = scenarios[index % len(scenarios)]

    context = (
        f"The {domain['system']} architecture documentation needs "
        f"a minor presentation or naming improvement {variant}."
    )

    return scenario, context


# ---------------------------------------------------------------------
# Database Design scenarios
# ---------------------------------------------------------------------


def database_significant(domain, variant, index):
    scenarios = [
        {
            "family": "database_technology",
            "difficulty": "easy",
            "title": "Select Primary Database Technology",
            "decision": "Use PostgreSQL as the primary transactional database.",
            "rationale": (
                "Relational integrity and ACID transactions support "
                "consistent persistent data."
            ),
            "alternatives": [
                "MongoDB",
                "Cassandra",
            ],
            "trade_offs": [
                "Strong consistency is prioritised over schema flexibility."
            ],
        },
        {
            "family": "database_partitioning",
            "difficulty": "hard",
            "title": "Partition High-Volume Records",
            "decision": (
                f"Partition {domain['entity']} records using business "
                "identifier and time ranges."
            ),
            "rationale": (
                "Partitioning supports growth and reduces query scope."
            ),
            "alternatives": [
                "Use one unpartitioned table",
            ],
            "trade_offs": [
                "Better scalability introduces partition-management complexity."
            ],
        },
        {
            "family": "database_replication",
            "difficulty": "medium",
            "title": "Introduce Database Replication",
            "decision": (
                "Use a primary-replica database deployment model."
            ),
            "rationale": (
                "Replication improves redundancy and read availability."
            ),
            "alternatives": [
                "Single database instance",
            ],
            "trade_offs": [
                "Higher availability requires replication management."
            ],
        },
        {
            "family": "data_ownership",
            "difficulty": "medium",
            "title": "Define Independent Data Ownership",
            "decision": (
                f"Give the {domain['entity']} service ownership "
                "of its persistent data."
            ),
            "rationale": (
                "Clear ownership reduces coupling between services."
            ),
            "alternatives": [
                "Shared tables across services",
            ],
            "trade_offs": [
                "Reduced coupling makes cross-service queries more complex."
            ],
        },
        {
            "family": "audit_storage",
            "difficulty": "hard",
            "title": "Use Immutable Audit Storage",
            "decision": (
                f"Store sensitive {domain['entity']} audit records "
                "using append-only persistence."
            ),
            "rationale": (
                "Immutable records improve auditability and accountability."
            ),
            "alternatives": [
                "Overwrite previous records",
            ],
            "trade_offs": [
                "Auditability increases storage requirements."
            ],
        },
    ]

    scenario = scenarios[index % len(scenarios)]

    context = (
        f"The {domain['system']} must manage {domain['data']} "
        f"reliably {variant}."
    )

    return scenario, context


def database_minor(domain, variant, index):
    scenarios = [
        {
            "family": "column_name",
            "difficulty": "easy",
            "title": "Rename Internal Database Column",
            "decision": (
                f"Rename a development-only {domain['entity']} metadata column."
            ),
            "rationale": "The change improves schema readability.",
        },
        {
            "family": "seed_data",
            "difficulty": "easy",
            "title": "Update Development Seed Data",
            "decision": (
                f"Replace sample {domain['entity']} data used "
                "for local development."
            ),
            "rationale": "Only development sample data is affected.",
        },
        {
            "family": "sql_formatting",
            "difficulty": "easy",
            "title": "Reformat SQL Script",
            "decision": (
                f"Reformat the SQL script used for {domain['entity']} data."
            ),
            "rationale": "The SQL behaviour remains unchanged.",
        },
        {
            "family": "index_name",
            "difficulty": "medium",
            "title": "Rename Existing Database Index",
            "decision": (
                f"Rename the existing {domain['entity']} index "
                "without changing indexed fields."
            ),
            "rationale": "The change improves naming consistency.",
        },
        {
            "family": "database_comment",
            "difficulty": "easy",
            "title": "Add Database Documentation Comment",
            "decision": (
                f"Add a descriptive comment to the {domain['entity']} table."
            ),
            "rationale": "The change affects documentation only.",
        },
    ]

    scenario = scenarios[index % len(scenarios)]

    context = (
        f"The {domain['system']} database requires a minor maintenance "
        f"improvement {variant}."
    )

    return scenario, context


# ---------------------------------------------------------------------
# API / Component Design scenarios
# ---------------------------------------------------------------------


def api_significant(domain, variant, index):
    scenarios = [
        {
            "family": "api_style",
            "difficulty": "easy",
            "title": "Select External API Style",
            "decision": (
                "Use REST APIs for external client communication."
            ),
            "rationale": (
                "REST provides broadly supported HTTP-based interoperability."
            ),
            "alternatives": [
                "GraphQL",
                "gRPC",
            ],
            "trade_offs": [
                "Compatibility is prioritised over specialised RPC performance."
            ],
        },
        {
            "family": "api_versioning",
            "difficulty": "medium",
            "title": "Introduce API Versioning",
            "decision": (
                "Use explicit version identifiers for externally consumed APIs."
            ),
            "rationale": (
                "Versioning supports backward-compatible API evolution."
            ),
            "alternatives": [
                "Unversioned API evolution",
            ],
            "trade_offs": [
                "Compatibility increases maintenance effort."
            ],
        },
        {
            "family": "pagination_contract",
            "difficulty": "hard",
            "title": "Require Pagination for Large Collections",
            "decision": (
                f"Require pagination for {domain['entity']} collection endpoints."
            ),
            "rationale": (
                "Pagination limits response size and improves performance."
            ),
            "alternatives": [
                "Return all records",
            ],
            "trade_offs": [
                "Smaller responses require client-side pagination handling."
            ],
        },
        {
            "family": "service_contract",
            "difficulty": "medium",
            "title": "Introduce Versioned Service Contracts",
            "decision": (
                f"Use versioned contracts when exchanging {domain['entity']} "
                "data between services."
            ),
            "rationale": (
                "Versioned contracts reduce accidental integration breakage."
            ),
            "alternatives": [
                "Unversioned internal payloads",
            ],
            "trade_offs": [
                "Stronger compatibility requires additional governance."
            ],
        },
        {
            "family": "idempotency",
            "difficulty": "hard",
            "title": "Require Idempotency for Critical Commands",
            "decision": (
                f"Require idempotency keys for critical "
                f"{domain['entity']} command endpoints."
            ),
            "rationale": (
                "Idempotency prevents duplicate processing after retries."
            ),
            "alternatives": [
                "Allow unrestricted retries",
            ],
            "trade_offs": [
                "Duplicate protection requires additional state management."
            ],
        },
    ]

    scenario = scenarios[index % len(scenarios)]

    context = (
        f"The {domain['system']} exposes {domain['entity']} functionality "
        f"to {domain['users']} {variant}."
    )

    return scenario, context


def api_minor(domain, variant, index):
    scenarios = [
        {
            "family": "parameter_name",
            "difficulty": "easy",
            "title": "Rename Internal Request Variable",
            "decision": (
                f"Rename a local {domain['entity']} request variable."
            ),
            "rationale": "The public API contract is unchanged.",
        },
        {
            "family": "swagger_description",
            "difficulty": "easy",
            "title": "Improve API Documentation Description",
            "decision": (
                f"Rewrite the Swagger description for the "
                f"{domain['entity']} endpoint."
            ),
            "rationale": "Only API documentation is changed.",
        },
        {
            "family": "controller_method_name",
            "difficulty": "easy",
            "title": "Rename Controller Method",
            "decision": (
                f"Rename the private controller method handling "
                f"{domain['entity']} requests."
            ),
            "rationale": "The route and behaviour remain unchanged.",
        },
        {
            "family": "example_payload",
            "difficulty": "medium",
            "title": "Update Example API Payload",
            "decision": (
                f"Replace the example {domain['entity']} payload "
                "shown in Swagger."
            ),
            "rationale": "Runtime behaviour is unchanged.",
        },
        {
            "family": "response_message",
            "difficulty": "medium",
            "title": "Improve Development Response Message",
            "decision": (
                f"Rewrite the development-only success message "
                f"for {domain['entity']} requests."
            ),
            "rationale": "The API architecture is unaffected.",
        },
    ]

    scenario = scenarios[index % len(scenarios)]

    context = (
        f"The {domain['system']} API requires a minor developer-facing "
        f"improvement {variant}."
    )

    return scenario, context


# ---------------------------------------------------------------------
# Quality Evaluation scenarios
# ---------------------------------------------------------------------


def quality_significant(domain, variant, index):
    scenarios = [
        {
            "family": "authentication_strategy",
            "difficulty": "easy",
            "title": "Adopt Token-Based Authentication",
            "decision": (
                "Use token-based authentication with role-based authorization."
            ),
            "rationale": (
                "The approach supports stateless protection of distributed APIs."
            ),
            "alternatives": [
                "Server-side sessions",
            ],
            "trade_offs": [
                "Stateless authentication requires secure token management."
            ],
        },
        {
            "family": "encryption_strategy",
            "difficulty": "medium",
            "title": "Require Encryption for Sensitive Data",
            "decision": (
                f"Encrypt sensitive {domain['data']} both in transit and at rest."
            ),
            "rationale": (
                "Encryption reduces the exposure of confidential information."
            ),
            "alternatives": [
                "Transport encryption only",
            ],
            "trade_offs": [
                "Stronger protection increases key-management responsibility."
            ],
        },
        {
            "family": "availability_strategy",
            "difficulty": "medium",
            "title": "Introduce Automatic Failover",
            "decision": (
                "Use health monitoring and automatic failover "
                "for critical services."
            ),
            "rationale": (
                "Automatic failover reduces service interruption."
            ),
            "alternatives": [
                "Manual recovery",
            ],
            "trade_offs": [
                "Improved availability increases infrastructure complexity."
            ],
        },
        {
            "family": "rate_limiting",
            "difficulty": "hard",
            "title": "Apply Platform-Wide Rate Limiting",
            "decision": (
                f"Apply central rate limiting to public "
                f"{domain['entity']} APIs."
            ),
            "rationale": (
                "Rate limiting protects shared resources from excessive traffic."
            ),
            "alternatives": [
                "No central rate limiting",
            ],
            "trade_offs": [
                "Protection may reject legitimate burst traffic."
            ],
        },
        {
            "family": "observability_strategy",
            "difficulty": "hard",
            "title": "Adopt Centralised Observability",
            "decision": (
                "Use centralised logging, metrics and distributed tracing."
            ),
            "rationale": (
                "Unified observability improves diagnosis of distributed failures."
            ),
            "alternatives": [
                "Local service logs only",
            ],
            "trade_offs": [
                "Improved diagnosis requires additional infrastructure."
            ],
        },
    ]

    scenario = scenarios[index % len(scenarios)]

    context = (
        f"The {domain['system']} has important quality requirements "
        f"for protecting and operating {domain['data']} {variant}."
    )

    return scenario, context


def quality_minor(domain, variant, index):
    scenarios = [
        {
            "family": "log_wording",
            "difficulty": "easy",
            "title": "Rewrite Debug Log Message",
            "decision": (
                f"Rewrite a debug log related to {domain['entity']} processing."
            ),
            "rationale": "Runtime quality behaviour is unchanged.",
        },
        {
            "family": "test_name",
            "difficulty": "easy",
            "title": "Rename Quality Test",
            "decision": (
                f"Rename a test covering {domain['entity']} behaviour."
            ),
            "rationale": "The assertion and quality requirement remain unchanged.",
        },
        {
            "family": "dashboard_label",
            "difficulty": "easy",
            "title": "Change Monitoring Dashboard Label",
            "decision": (
                f"Rename the dashboard label showing "
                f"{domain['entity']} activity."
            ),
            "rationale": "Monitoring behaviour remains unchanged.",
        },
        {
            "family": "threshold_description",
            "difficulty": "medium",
            "title": "Clarify Performance Threshold Documentation",
            "decision": (
                f"Rewrite the description of the {domain['entity']} "
                "performance threshold."
            ),
            "rationale": "The actual threshold is not changed.",
        },
        {
            "family": "security_comment",
            "difficulty": "medium",
            "title": "Update Security Code Comment",
            "decision": (
                f"Update a comment describing security handling "
                f"for {domain['entity']} operations."
            ),
            "rationale": "The security mechanism itself is unchanged.",
        },
    ]

    scenario = scenarios[index % len(scenarios)]

    context = (
        f"The {domain['system']} requires a minor quality-related "
        f"documentation improvement {variant}."
    )

    return scenario, context


# ---------------------------------------------------------------------
# Dataset construction
# ---------------------------------------------------------------------


def build_module_rows(
    source_module,
    significant_builder,
    minor_builder,
    significant_count,
    minor_count,
    starting_id,
):
    rows = []
    current_id = starting_id

    for index in range(significant_count):
        domain = DOMAINS[index % len(DOMAINS)]
        variant = CONTEXT_VARIANTS[
            (index // len(DOMAINS))
            % len(CONTEXT_VARIANTS)
        ]

        scenario, context = significant_builder(
            domain,
            variant,
            index,
        )

        rows.append(
            make_row(
                decision_id=f"ADR-DATA-{current_id:03d}",
                source_module=source_module,
                domain=domain["name"],
                title=(
                    f"{scenario['title']} - "
                    f"{domain['name'].title()}"
                ),
                context=context,
                decision=scenario["decision"],
                rationale=scenario["rationale"],
                alternatives=scenario["alternatives"],
                trade_offs=scenario["trade_offs"],
                requirement_ids=[
                    f"REQ-{current_id:03d}",
                    f"NFR-{current_id:03d}",
                ],
                design_element_ids=[
                    f"DESIGN-{current_id:03d}",
                ],
                scenario_family=scenario["family"],
                difficulty=scenario["difficulty"],
                label=1,
            )
        )

        current_id += 1

    for index in range(minor_count):
        domain = DOMAINS[index % len(DOMAINS)]
        variant = CONTEXT_VARIANTS[
            (index // len(DOMAINS))
            % len(CONTEXT_VARIANTS)
        ]

        scenario, context = minor_builder(
            domain,
            variant,
            index,
        )

        rows.append(
            make_row(
                decision_id=f"ADR-DATA-{current_id:03d}",
                source_module=source_module,
                domain=domain["name"],
                title=(
                    f"{scenario['title']} - "
                    f"{domain['name'].title()}"
                ),
                context=context,
                decision=scenario["decision"],
                rationale=scenario["rationale"],
                alternatives=[],
                trade_offs=[],
                requirement_ids=[],
                design_element_ids=[
                    f"DESIGN-{current_id:03d}",
                ],
                scenario_family=scenario["family"],
                difficulty=scenario["difficulty"],
                label=0,
            )
        )

        current_id += 1

    return rows, current_id


def build_dataset():
    rows = []
    next_id = 1

    configurations = [
        (
            "architecture_decision",
            architecture_significant,
            architecture_minor,
            13,
            12,
        ),
        (
            "database_design",
            database_significant,
            database_minor,
            13,
            12,
        ),
        (
            "api_component_design",
            api_significant,
            api_minor,
            12,
            13,
        ),
        (
            "quality_evaluation",
            quality_significant,
            quality_minor,
            12,
            13,
        ),
    ]

    for configuration in configurations:
        module_rows, next_id = build_module_rows(
            source_module=configuration[0],
            significant_builder=configuration[1],
            minor_builder=configuration[2],
            significant_count=configuration[3],
            minor_count=configuration[4],
            starting_id=next_id,
        )

        rows.extend(module_rows)

    return rows


def save_dataset(rows):
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows):
    significant = sum(
        int(row["label"]) == 1
        for row in rows
    )

    not_significant = sum(
        int(row["label"]) == 0
        for row in rows
    )

    print()
    print("ADR significance seed dataset V2 created.")
    print("----------------------------------------")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Total records: {len(rows)}")
    print(f"Significant: {significant}")
    print(f"Not significant: {not_significant}")

    print()
    print("By source module:")

    for source in sorted(
        set(row["source_module"] for row in rows)
    ):
        count = sum(
            row["source_module"] == source
            for row in rows
        )

        print(f"  {source}: {count}")

    print()
    print("Labels remain provisional.")
    print(
        "Human/expert review is required before "
        "creating the final benchmark."
    )


if __name__ == "__main__":
    dataset = build_dataset()
    save_dataset(dataset)
    print_summary(dataset)