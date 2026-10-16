"""
Build the diversified ADR significance candidate dataset.

Dataset design:
- 600 total decisions
- 300 significant
- 300 non-significant
- 150 decisions per major source module
- 120 decisions per domain
- 15 significant + 15 non-significant scenario families per module
- each scenario family instantiated across five application domains

IMPORTANT:
This is a synthetic/developer-assisted candidate dataset.
Labels remain provisional until human/expert review.
"""

import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

OUTPUT_PATH = (
    BASE_DIR
    / "raw"
    / "adr_significance_candidates.csv"
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
        "resource": "financial account",
        "users": "bank customers",
        "data": "financial transaction data",
        "critical_action": "money transfer",
    },
    {
        "name": "healthcare",
        "system": "hospital management platform",
        "entity": "appointment",
        "resource": "patient record",
        "users": "patients and clinical staff",
        "data": "patient and medical data",
        "critical_action": "clinical appointment update",
    },
    {
        "name": "ecommerce",
        "system": "e-commerce platform",
        "entity": "order",
        "resource": "customer order",
        "users": "online shoppers",
        "data": "order and payment data",
        "critical_action": "order placement",
    },
    {
        "name": "logistics",
        "system": "logistics management platform",
        "entity": "shipment",
        "resource": "delivery record",
        "users": "dispatchers and drivers",
        "data": "shipment and delivery data",
        "critical_action": "delivery confirmation",
    },
    {
        "name": "education",
        "system": "university learning platform",
        "entity": "course",
        "resource": "student record",
        "users": "students and lecturers",
        "data": "student and course data",
        "critical_action": "course registration",
    },
]


def pipe(items):
    return "|".join(items)


def format_text(text, domain):
    return text.format(**domain)


def make_row(
    decision_id,
    source_module,
    domain,
    scenario,
    label,
):
    return {
        "decision_id": decision_id,
        "source_module": source_module,
        "domain": domain["name"],
        "title": (
            f"{format_text(scenario['title'], domain)} "
            f"- {domain['name'].title()}"
        ),
        "context": format_text(
            scenario["context"],
            domain,
        ),
        "decision": format_text(
            scenario["decision"],
            domain,
        ),
        "rationale": format_text(
            scenario["rationale"],
            domain,
        ),
        "alternatives": pipe(
            [
                format_text(item, domain)
                for item in scenario.get(
                    "alternatives",
                    [],
                )
            ]
        ),
        "trade_offs": pipe(
            [
                format_text(item, domain)
                for item in scenario.get(
                    "trade_offs",
                    [],
                )
            ]
        ),
        "requirement_ids": (
            pipe(
                [
                    f"REQ-{decision_id[-4:]}",
                    f"NFR-{decision_id[-4:]}",
                ]
            )
            if label == 1
            else ""
        ),
        "design_element_ids": pipe(
            [
                f"DESIGN-{decision_id[-4:]}"
            ]
        ),
        "scenario_family": scenario["family"],
        "difficulty": scenario["difficulty"],
        "label": label,
        "label_source": "developer_provisional",
        "review_status": "pending_review",
    }


# ================================================================
# Architecture Decision scenarios
# ================================================================

ARCHITECTURE_SIGNIFICANT = [
    {
        "family": "architecture_style_selection",
        "difficulty": "easy",
        "title": "Select Primary Architecture Style",
        "context": (
            "The {system} requires independent scalability, "
            "fault isolation and independent deployment."
        ),
        "decision": (
            "Adopt Microservices as the primary architecture style."
        ),
        "rationale": (
            "Independent services support isolated deployment and scaling."
        ),
        "alternatives": [
            "Modular Monolith",
            "Layered Architecture",
        ],
        "trade_offs": [
            "Greater scalability introduces distributed-system complexity."
        ],
    },
    {
        "family": "modular_monolith_selection",
        "difficulty": "hard",
        "title": "Adopt Modular Monolith",
        "context": (
            "The {system} needs strong internal modularity but the team "
            "does not yet require independently deployed services."
        ),
        "decision": (
            "Use a Modular Monolith with explicit internal module boundaries."
        ),
        "rationale": (
            "The architecture preserves modularity while maintaining "
            "a simpler deployment model."
        ),
        "alternatives": [
            "Microservices",
            "Traditional Layered Monolith",
        ],
        "trade_offs": [
            "Simpler operations limit independent module scaling."
        ],
    },
    {
        "family": "event_driven_architecture",
        "difficulty": "medium",
        "title": "Introduce Event-Driven Communication",
        "context": (
            "The {system} performs asynchronous workflows involving "
            "{entity} processing across multiple components."
        ),
        "decision": (
            "Use event-driven communication for asynchronous business workflows."
        ),
        "rationale": (
            "Events reduce temporal coupling between producers and consumers."
        ),
        "alternatives": [
            "Synchronous REST communication only",
        ],
        "trade_offs": [
            "Loose coupling increases event tracing and schema complexity."
        ],
    },
    {
        "family": "service_boundary",
        "difficulty": "medium",
        "title": "Separate Core Capability",
        "context": (
            "The {entity} capability has scaling and release needs "
            "different from other parts of the {system}."
        ),
        "decision": (
            "Extract {entity} processing into an independently deployable service."
        ),
        "rationale": (
            "Independent ownership allows isolated evolution and scaling."
        ),
        "alternatives": [
            "Keep {entity} processing in the main application",
        ],
        "trade_offs": [
            "Service independence introduces remote communication overhead."
        ],
    },
    {
        "family": "api_gateway",
        "difficulty": "medium",
        "title": "Introduce API Gateway",
        "context": (
            "Multiple external clients access several backend services "
            "within the {system}."
        ),
        "decision": (
            "Use an API Gateway as the controlled external entry point."
        ),
        "rationale": (
            "The gateway centralises routing and cross-cutting policies."
        ),
        "alternatives": [
            "Expose every backend service directly",
        ],
        "trade_offs": [
            "Centralised control introduces an additional critical component."
        ],
    },
    {
        "family": "message_broker",
        "difficulty": "medium",
        "title": "Introduce Message Broker",
        "context": (
            "The {system} requires reliable asynchronous delivery of "
            "{entity}-related events."
        ),
        "decision": (
            "Introduce a message broker for asynchronous service communication."
        ),
        "rationale": (
            "A broker supports buffering, retries and decoupled communication."
        ),
        "alternatives": [
            "Direct synchronous calls",
        ],
        "trade_offs": [
            "Improved resilience requires broker operation and monitoring."
        ],
    },
    {
        "family": "multi_zone_deployment",
        "difficulty": "hard",
        "title": "Use Multi-Zone Deployment",
        "context": (
            "The {system} must remain available after a single "
            "infrastructure-zone failure."
        ),
        "decision": (
            "Deploy critical services across multiple availability zones."
        ),
        "rationale": (
            "Geographic redundancy reduces single-zone failure impact."
        ),
        "alternatives": [
            "Single-zone deployment",
        ],
        "trade_offs": [
            "Higher infrastructure cost provides improved availability."
        ],
    },
    {
        "family": "cache_layer",
        "difficulty": "hard",
        "title": "Introduce Distributed Cache",
        "context": (
            "Frequently requested {resource} data creates repeated "
            "database load in the {system}."
        ),
        "decision": (
            "Introduce a distributed cache for frequently accessed read data."
        ),
        "rationale": (
            "Caching reduces database load and request latency."
        ),
        "alternatives": [
            "Database access for every request",
        ],
        "trade_offs": [
            "Lower latency introduces cache invalidation complexity."
        ],
    },
    {
        "family": "read_write_separation",
        "difficulty": "hard",
        "title": "Separate Read and Write Workloads",
        "context": (
            "Read traffic and modification traffic have substantially "
            "different performance characteristics."
        ),
        "decision": (
            "Separate read-oriented and write-oriented processing paths."
        ),
        "rationale": (
            "Independent optimisation supports different workload characteristics."
        ),
        "alternatives": [
            "Single processing path",
        ],
        "trade_offs": [
            "Independent paths improve scalability but increase design complexity."
        ],
    },
    {
        "family": "external_identity_provider",
        "difficulty": "medium",
        "title": "Centralise Identity Management",
        "context": (
            "Multiple components in the {system} require consistent "
            "authentication and identity information."
        ),
        "decision": (
            "Use a central identity service for authentication and identity management."
        ),
        "rationale": (
            "Central identity management avoids duplicated authentication logic."
        ),
        "alternatives": [
            "Independent authentication inside every component",
        ],
        "trade_offs": [
            "Consistency increases dependency on the identity service."
        ],
    },
    {
        "family": "container_orchestration",
        "difficulty": "hard",
        "title": "Adopt Container Orchestration",
        "context": (
            "The {system} contains multiple independently deployed "
            "services requiring scaling and recovery."
        ),
        "decision": (
            "Use container orchestration for deployment and service recovery."
        ),
        "rationale": (
            "Orchestration supports automated scheduling, scaling and restart."
        ),
        "alternatives": [
            "Manually managed service deployments",
        ],
        "trade_offs": [
            "Automation introduces platform administration complexity."
        ],
    },
    {
        "family": "backend_for_frontend",
        "difficulty": "hard",
        "title": "Introduce Client-Specific Backend Layer",
        "context": (
            "{users} use different client applications with substantially "
            "different interaction requirements."
        ),
        "decision": (
            "Introduce client-specific backend interfaces for major client types."
        ),
        "rationale": (
            "Client-specific APIs reduce unnecessary client-side orchestration."
        ),
        "alternatives": [
            "One identical API surface for all clients",
        ],
        "trade_offs": [
            "Improved client optimisation creates additional backend components."
        ],
    },
    {
        "family": "fault_isolation_boundary",
        "difficulty": "medium",
        "title": "Create Fault Isolation Boundary",
        "context": (
            "Failure in {entity} processing can currently interrupt "
            "unrelated workflows."
        ),
        "decision": (
            "Isolate {entity} processing behind an independent failure boundary."
        ),
        "rationale": (
            "Isolation limits cascading failures across the {system}."
        ),
        "alternatives": [
            "Shared failure boundary",
        ],
        "trade_offs": [
            "Fault containment introduces additional communication boundaries."
        ],
    },
    {
        "family": "edge_proxy",
        "difficulty": "medium",
        "title": "Introduce Reverse Proxy Layer",
        "context": (
            "External traffic requires central TLS termination, routing "
            "and protection before reaching application services."
        ),
        "decision": (
            "Use a reverse proxy in front of externally exposed services."
        ),
        "rationale": (
            "The proxy centralises edge networking responsibilities."
        ),
        "alternatives": [
            "Expose application services directly",
        ],
        "trade_offs": [
            "Central networking simplifies services but adds another infrastructure layer."
        ],
    },
    {
        "family": "background_worker_architecture",
        "difficulty": "hard",
        "title": "Separate Long-Running Background Work",
        "context": (
            "Some {entity} operations continue long after the user request "
            "has completed."
        ),
        "decision": (
            "Execute long-running work through dedicated background workers."
        ),
        "rationale": (
            "Background workers prevent lengthy operations from blocking request handling."
        ),
        "alternatives": [
            "Execute all work synchronously",
        ],
        "trade_offs": [
            "Responsive requests require queue and worker management."
        ],
    },
]


ARCHITECTURE_MINOR = [
    ("component_naming", "easy", "Rename Internal Component",
     "An internal {entity} component name is inconsistent.",
     "Rename the internal {entity} helper component.",
     "The change improves naming consistency."),
    ("diagram_layout", "easy", "Rearrange Architecture Diagram",
     "Architecture elements overlap in documentation.",
     "Move the {entity} component to a clearer diagram position.",
     "Only diagram presentation changes."),
    ("package_naming", "easy", "Rename Internal Package",
     "A helper package uses an outdated name.",
     "Rename the package containing {entity} helper classes.",
     "Runtime behaviour is unchanged."),
    ("diagram_colour", "easy", "Change Diagram Colour",
     "A diagram element has poor visual contrast.",
     "Change the colour of the {entity} diagram element.",
     "Only visual styling changes."),
    ("component_description", "medium", "Rewrite Component Description",
     "Documentation uses outdated wording.",
     "Rewrite the documentation for the {entity} component.",
     "The architecture itself is unchanged."),
    ("plantuml_spacing", "easy", "Adjust PlantUML Spacing",
     "Generated diagrams contain crowded elements.",
     "Adjust spacing directives in the architecture diagram.",
     "Only diagram readability changes."),
    ("diagram_alias", "easy", "Rename Diagram Alias",
     "A PlantUML alias is difficult to understand.",
     "Rename the internal alias for the {entity} component.",
     "The generated architecture semantics remain unchanged."),
    ("documentation_typo", "easy", "Correct Architecture Typo",
     "Architecture documentation contains a spelling error.",
     "Correct the typo in the {entity} description.",
     "The correction has no design impact."),
    ("folder_reorganisation", "medium", "Move Diagram Source File",
     "Architecture diagram files are stored inconsistently.",
     "Move the {entity} diagram source into the documentation folder.",
     "Only repository organisation changes."),
    ("comment_update", "easy", "Update Architecture Code Comment",
     "A source comment uses old terminology.",
     "Update the comment describing the {entity} component.",
     "Executable behaviour is unchanged."),
    ("legend_update", "easy", "Update Diagram Legend",
     "The architecture diagram legend is incomplete.",
     "Add the {entity} symbol description to the legend.",
     "Only documentation clarity changes."),
    ("title_format", "easy", "Change Architecture Diagram Title",
     "The diagram title does not follow report formatting.",
     "Rename the diagram title for the {system}.",
     "No architectural decision changes."),
    ("file_name", "easy", "Rename Architecture File",
     "The architecture source filename is inconsistent.",
     "Rename the {entity} architecture file.",
     "The file content remains unchanged."),
    ("documentation_order", "medium", "Reorder Architecture Documentation",
     "Architecture sections are difficult to navigate.",
     "Move the {entity} documentation section earlier in the document.",
     "Only presentation order changes."),
    ("whitespace_cleanup", "easy", "Clean Architecture Configuration Formatting",
     "Architecture configuration contains unnecessary whitespace.",
     "Reformat the configuration without changing values.",
     "Runtime architecture remains identical."),
]


# ================================================================
# Database scenarios
# ================================================================

DATABASE_SIGNIFICANT = [
    {
        "family": "database_technology",
        "difficulty": "easy",
        "title": "Select Transactional Database",
        "context": (
            "The {system} requires consistent storage for {data}."
        ),
        "decision": (
            "Use PostgreSQL as the primary transactional database."
        ),
        "rationale": (
            "ACID transactions and relational integrity suit the workload."
        ),
        "alternatives": ["MongoDB", "Cassandra"],
        "trade_offs": [
            "Consistency is prioritised over schema flexibility."
        ],
    },
    {
        "family": "document_database",
        "difficulty": "hard",
        "title": "Use Document Database for Flexible Records",
        "context": (
            "Some {entity} metadata changes frequently and varies across records."
        ),
        "decision": (
            "Use a document database for flexible {entity} metadata."
        ),
        "rationale": (
            "Document storage accommodates evolving semi-structured data."
        ),
        "alternatives": ["Relational table with many nullable columns"],
        "trade_offs": [
            "Schema flexibility reduces relational enforcement."
        ],
    },
    {
        "family": "database_partitioning",
        "difficulty": "hard",
        "title": "Partition High-Volume Records",
        "context": (
            "{data} is expected to grow beyond efficient single-table operation."
        ),
        "decision": (
            "Partition {entity} records by business identifier and time."
        ),
        "rationale": (
            "Partitioning limits query scope and supports growth."
        ),
        "alternatives": ["Single unpartitioned table"],
        "trade_offs": [
            "Scalability introduces partition management."
        ],
    },
    {
        "family": "database_replication",
        "difficulty": "medium",
        "title": "Introduce Database Replication",
        "context": (
            "The {system} requires improved read availability and recovery."
        ),
        "decision": (
            "Use primary-replica database deployment."
        ),
        "rationale": (
            "Replication provides redundancy and read capacity."
        ),
        "alternatives": ["Single database instance"],
        "trade_offs": [
            "Availability requires replication management."
        ],
    },
    {
        "family": "service_data_ownership",
        "difficulty": "medium",
        "title": "Assign Service Data Ownership",
        "context": (
            "Multiple services currently access shared {entity} tables directly."
        ),
        "decision": (
            "Give the {entity} service exclusive ownership of its persistent data."
        ),
        "rationale": (
            "Explicit ownership reduces cross-service coupling."
        ),
        "alternatives": ["Shared database tables"],
        "trade_offs": [
            "Reduced coupling makes distributed queries harder."
        ],
    },
    {
        "family": "audit_storage",
        "difficulty": "hard",
        "title": "Use Immutable Audit Records",
        "context": (
            "Changes to {data} require durable historical auditing."
        ),
        "decision": (
            "Store audit events using append-only persistence."
        ),
        "rationale": (
            "Immutable records preserve historical evidence."
        ),
        "alternatives": ["Overwrite current records only"],
        "trade_offs": [
            "Auditability increases storage consumption."
        ],
    },
    {
        "family": "database_encryption",
        "difficulty": "medium",
        "title": "Encrypt Sensitive Database Fields",
        "context": (
            "{data} contains information requiring additional protection."
        ),
        "decision": (
            "Encrypt sensitive database fields before persistent storage."
        ),
        "rationale": (
            "Field-level encryption reduces exposure after storage compromise."
        ),
        "alternatives": ["Storage-volume encryption only"],
        "trade_offs": [
            "Additional protection increases key-management complexity."
        ],
    },
    {
        "family": "soft_delete_strategy",
        "difficulty": "hard",
        "title": "Adopt Soft Deletion for Regulated Records",
        "context": (
            "{resource} records require historical retention after user removal."
        ),
        "decision": (
            "Use soft deletion with retention metadata for regulated records."
        ),
        "rationale": (
            "Historical records remain auditable while being hidden operationally."
        ),
        "alternatives": ["Immediate physical deletion"],
        "trade_offs": [
            "Retention improves auditability but requires lifecycle management."
        ],
    },
    {
        "family": "read_replica",
        "difficulty": "medium",
        "title": "Route Reporting Queries to Read Replica",
        "context": (
            "Reporting queries compete with operational {entity} transactions."
        ),
        "decision": (
            "Use read replicas for reporting and analytical queries."
        ),
        "rationale": (
            "Separating read workload protects transactional performance."
        ),
        "alternatives": ["Run all queries on primary database"],
        "trade_offs": [
            "Read scalability introduces possible replication lag."
        ],
    },
    {
        "family": "database_backup_strategy",
        "difficulty": "medium",
        "title": "Adopt Point-in-Time Recovery",
        "context": (
            "The {system} requires recovery of {data} after accidental corruption."
        ),
        "decision": (
            "Enable automated backups with point-in-time recovery."
        ),
        "rationale": (
            "Point-in-time recovery limits permanent data loss."
        ),
        "alternatives": ["Periodic manual backup only"],
        "trade_offs": [
            "Stronger recovery guarantees increase storage and operational cost."
        ],
    },
    {
        "family": "distributed_database",
        "difficulty": "hard",
        "title": "Distribute Data Across Regions",
        "context": (
            "The {system} serves geographically distributed users "
            "with strict availability needs."
        ),
        "decision": (
            "Use a multi-region database deployment for critical records."
        ),
        "rationale": (
            "Regional distribution improves locality and disaster resilience."
        ),
        "alternatives": ["Single-region database"],
        "trade_offs": [
            "Regional resilience introduces consistency and replication complexity."
        ],
    },
    {
        "family": "schema_migration_strategy",
        "difficulty": "hard",
        "title": "Adopt Backward-Compatible Schema Migration",
        "context": (
            "Services cannot all be deployed simultaneously during schema changes."
        ),
        "decision": (
            "Use backward-compatible expand-and-contract database migrations."
        ),
        "rationale": (
            "Compatibility allows old and new application versions to coexist."
        ),
        "alternatives": ["Breaking schema replacement"],
        "trade_offs": [
            "Safer deployments require multi-stage migrations."
        ],
    },
    {
        "family": "database_connection_pooling",
        "difficulty": "medium",
        "title": "Introduce Central Connection Pooling",
        "context": (
            "High request concurrency creates excessive database connections."
        ),
        "decision": (
            "Use bounded database connection pools for application services."
        ),
        "rationale": (
            "Pooling protects database resources under high concurrency."
        ),
        "alternatives": ["Open new connection per request"],
        "trade_offs": [
            "Resource protection requires careful pool sizing."
        ],
    },
    {
        "family": "data_archival",
        "difficulty": "hard",
        "title": "Introduce Historical Data Archival",
        "context": (
            "Old {entity} records reduce operational query performance."
        ),
        "decision": (
            "Move historical records into lower-cost archival storage."
        ),
        "rationale": (
            "Archival keeps operational datasets smaller."
        ),
        "alternatives": ["Keep all history in active tables"],
        "trade_offs": [
            "Faster operational queries make historical retrieval slower."
        ],
    },
    {
        "family": "unique_id_strategy",
        "difficulty": "hard",
        "title": "Adopt Distributed Identifier Strategy",
        "context": (
            "Multiple independently deployed components create {entity} records."
        ),
        "decision": (
            "Use globally unique identifiers for distributed record creation."
        ),
        "rationale": (
            "Globally unique IDs avoid coordination for identifier allocation."
        ),
        "alternatives": ["Central auto-increment sequence"],
        "trade_offs": [
            "Distributed generation improves independence but increases identifier size."
        ],
    },
]


DATABASE_MINOR = [
    ("column_name", "easy", "Rename Internal Column",
     "An internal {entity} metadata column has an unclear name.",
     "Rename the metadata column without changing its type.",
     "Only schema naming changes."),
    ("seed_data", "easy", "Update Development Seed Data",
     "Local development uses outdated sample {entity} data.",
     "Replace the sample development record.",
     "Production behaviour is unchanged."),
    ("sql_formatting", "easy", "Reformat SQL Script",
     "A SQL script has inconsistent formatting.",
     "Apply standard formatting to the {entity} SQL script.",
     "SQL semantics remain unchanged."),
    ("database_comment", "easy", "Add Database Comment",
     "A table purpose is unclear to developers.",
     "Add documentation comments to the {entity} table.",
     "The database design remains unchanged."),
    ("migration_file_name", "easy", "Rename Migration File",
     "A migration filename does not follow conventions.",
     "Rename the migration file without changing statements.",
     "Only repository naming changes."),
    ("sample_value", "easy", "Change Sample Database Value",
     "Local demonstration data contains outdated wording.",
     "Update a sample value in development data.",
     "No production data is affected."),
    ("query_variable_name", "easy", "Rename Query Variable",
     "A local query variable has a confusing name.",
     "Rename the variable used to hold {entity} query results.",
     "The query remains identical."),
    ("sql_comment", "easy", "Update SQL Comment",
     "A SQL comment contains outdated terminology.",
     "Rewrite the comment above the {entity} query.",
     "Execution behaviour remains unchanged."),
    ("fixture_order", "medium", "Reorder Test Fixtures",
     "Database test fixtures are difficult to read.",
     "Reorder {entity} test fixtures in the source file.",
     "Loaded fixture content remains unchanged."),
    ("indentation_cleanup", "easy", "Clean Migration Formatting",
     "A migration file has inconsistent indentation.",
     "Reformat the migration without modifying statements.",
     "Database changes remain identical."),
    ("alias_name", "medium", "Rename SQL Alias",
     "A local SQL alias is difficult to understand.",
     "Rename an alias used in a development query.",
     "The returned data is unchanged."),
    ("documentation_example", "easy", "Update Schema Documentation Example",
     "Schema documentation shows an old {entity} value.",
     "Replace the example in database documentation.",
     "The actual schema remains unchanged."),
    ("test_table_name", "medium", "Rename Test-Only Table",
     "A temporary unit-test table has an unclear name.",
     "Rename the test-only {entity} table.",
     "Production persistence is unaffected."),
    ("developer_script_name", "easy", "Rename Local Database Script",
     "A local maintenance script has a vague filename.",
     "Rename the local {entity} database script.",
     "The script's database operations remain unchanged."),
    ("whitespace_cleanup", "easy", "Remove SQL Whitespace",
     "A SQL file contains unnecessary blank lines.",
     "Remove unnecessary whitespace from the file.",
     "No database behaviour changes."),
]


# ================================================================
# API / Component scenarios
# ================================================================

API_SIGNIFICANT = [
    {
        "family": "api_style",
        "difficulty": "easy",
        "title": "Select External API Style",
        "context": (
            "{users} require interoperable access to the {system}."
        ),
        "decision": "Use REST for externally consumed APIs.",
        "rationale": "REST is broadly supported by web and mobile clients.",
        "alternatives": ["GraphQL", "gRPC"],
        "trade_offs": [
            "Compatibility is prioritised over specialised RPC performance."
        ],
    },
    {
        "family": "api_versioning",
        "difficulty": "medium",
        "title": "Introduce API Versioning",
        "context": (
            "Client applications cannot always upgrade together with backend services."
        ),
        "decision": "Use explicit versioning for public APIs.",
        "rationale": "Versioning supports controlled interface evolution.",
        "alternatives": ["Unversioned breaking changes"],
        "trade_offs": [
            "Compatibility creates additional maintenance effort."
        ],
    },
    {
        "family": "pagination_contract",
        "difficulty": "hard",
        "title": "Require Collection Pagination",
        "context": (
            "{entity} history may contain thousands of records."
        ),
        "decision": (
            "Require pagination for large {entity} collection endpoints."
        ),
        "rationale": "Pagination limits response size and latency.",
        "alternatives": ["Return entire collection"],
        "trade_offs": [
            "Smaller responses require client pagination logic."
        ],
    },
    {
        "family": "idempotency",
        "difficulty": "hard",
        "title": "Require Idempotent Commands",
        "context": (
            "Network retries may duplicate the {critical_action} operation."
        ),
        "decision": (
            "Require idempotency keys for critical command endpoints."
        ),
        "rationale": "Idempotency prevents repeated business processing.",
        "alternatives": ["Unrestricted retry processing"],
        "trade_offs": [
            "Duplicate protection requires additional state."
        ],
    },
    {
        "family": "service_contract_versioning",
        "difficulty": "medium",
        "title": "Version Inter-Service Contracts",
        "context": (
            "Independently deployed services exchange {entity} information."
        ),
        "decision": (
            "Use versioned schemas for inter-service communication."
        ),
        "rationale": "Versioned contracts reduce integration breakage.",
        "alternatives": ["Unversioned internal messages"],
        "trade_offs": [
            "Compatibility requires contract governance."
        ],
    },
    {
        "family": "authentication_contract",
        "difficulty": "medium",
        "title": "Standardise API Authentication",
        "context": (
            "Protected endpoints in the {system} currently use inconsistent authentication."
        ),
        "decision": (
            "Require bearer-token authentication for protected APIs."
        ),
        "rationale": "A consistent authentication contract simplifies enforcement.",
        "alternatives": ["Different authentication method per endpoint"],
        "trade_offs": [
            "Standardisation requires migration of legacy clients."
        ],
    },
    {
        "family": "error_contract",
        "difficulty": "hard",
        "title": "Standardise API Error Contract",
        "context": (
            "Clients receive incompatible error structures from different services."
        ),
        "decision": (
            "Adopt a common machine-readable API error representation."
        ),
        "rationale": "Consistent errors simplify client handling and observability.",
        "alternatives": ["Service-specific error formats"],
        "trade_offs": [
            "Consistency limits service-specific error representations."
        ],
    },
    {
        "family": "async_api",
        "difficulty": "hard",
        "title": "Use Asynchronous API for Long Operations",
        "context": (
            "Some {entity} operations cannot complete within normal request timeouts."
        ),
        "decision": (
            "Use asynchronous job submission with status polling for long operations."
        ),
        "rationale": "Async processing avoids holding HTTP requests open.",
        "alternatives": ["Long synchronous request"],
        "trade_offs": [
            "Better responsiveness requires job-state management."
        ],
    },
    {
        "family": "webhook_contract",
        "difficulty": "medium",
        "title": "Introduce Webhook Notifications",
        "context": (
            "External clients require timely notification of {entity} state changes."
        ),
        "decision": (
            "Provide signed webhook callbacks for important state changes."
        ),
        "rationale": "Webhooks avoid repeated client polling.",
        "alternatives": ["Frequent polling"],
        "trade_offs": [
            "Push notifications require delivery retries and signature validation."
        ],
    },
    {
        "family": "api_rate_limit_contract",
        "difficulty": "hard",
        "title": "Define Public API Rate Limits",
        "context": (
            "External clients can generate unpredictable request volumes."
        ),
        "decision": (
            "Define explicit rate-limit rules for public API consumers."
        ),
        "rationale": "Rate limits protect shared backend capacity.",
        "alternatives": ["Unlimited client requests"],
        "trade_offs": [
            "Protection can throttle legitimate bursts."
        ],
    },
    {
        "family": "bulk_endpoint",
        "difficulty": "hard",
        "title": "Introduce Bulk Processing Endpoint",
        "context": (
            "Clients currently make hundreds of individual {entity} requests."
        ),
        "decision": (
            "Provide a bounded bulk endpoint for supported {entity} operations."
        ),
        "rationale": "Bulk processing reduces network overhead.",
        "alternatives": ["Individual requests only"],
        "trade_offs": [
            "Lower network overhead increases request-validation complexity."
        ],
    },
    {
        "family": "api_timeout_policy",
        "difficulty": "medium",
        "title": "Define Service Timeout Policy",
        "context": (
            "Cross-service calls can remain open indefinitely during failures."
        ),
        "decision": (
            "Apply explicit timeout limits to remote service calls."
        ),
        "rationale": "Timeouts prevent resource exhaustion during downstream failure.",
        "alternatives": ["Unlimited waiting"],
        "trade_offs": [
            "Failure containment may terminate genuinely slow operations."
        ],
    },
    {
        "family": "api_retry_policy",
        "difficulty": "hard",
        "title": "Adopt Controlled Retry Policy",
        "context": (
            "Transient service failures affect {entity} workflows."
        ),
        "decision": (
            "Use bounded retries with exponential backoff for retry-safe requests."
        ),
        "rationale": "Controlled retries improve resilience without overwhelming dependencies.",
        "alternatives": ["Immediate failure", "Unlimited retries"],
        "trade_offs": [
            "Resilience can increase total request latency."
        ],
    },
    {
        "family": "graphql_selection",
        "difficulty": "hard",
        "title": "Use GraphQL for Aggregated Client Queries",
        "context": (
            "Clients require flexible combinations of related {resource} data."
        ),
        "decision": (
            "Expose a GraphQL interface for complex client-side data retrieval."
        ),
        "rationale": "GraphQL reduces over-fetching across flexible query shapes.",
        "alternatives": ["Multiple fixed REST endpoints"],
        "trade_offs": [
            "Flexible queries increase server-side query-control complexity."
        ],
    },
    {
        "family": "grpc_internal",
        "difficulty": "hard",
        "title": "Use gRPC for Internal Service Calls",
        "context": (
            "High-frequency internal service calls require efficient typed communication."
        ),
        "decision": (
            "Use gRPC for selected internal service-to-service communication."
        ),
        "rationale": "Binary contracts and generated clients reduce serialization overhead.",
        "alternatives": ["JSON REST for all internal communication"],
        "trade_offs": [
            "Higher efficiency reduces direct browser compatibility."
        ],
    },
]


API_MINOR = [
    ("parameter_name", "easy", "Rename Local Request Variable",
     "An internal request variable is unclear.",
     "Rename the local variable handling {entity} input.",
     "The public contract remains unchanged."),
    ("swagger_description", "easy", "Improve Swagger Description",
     "The {entity} endpoint description is unclear.",
     "Rewrite the Swagger description.",
     "Only documentation changes."),
    ("controller_method_name", "easy", "Rename Private Controller Method",
     "A private method has an unclear name.",
     "Rename the private method handling {entity} requests.",
     "Routes and behaviour remain unchanged."),
    ("example_payload", "easy", "Update Example API Payload",
     "Swagger shows outdated sample {entity} data.",
     "Replace the example payload.",
     "Runtime API behaviour is unchanged."),
    ("response_message", "medium", "Rewrite Development Success Message",
     "A development response message is unclear.",
     "Rewrite the local success message.",
     "The response contract used by clients is unchanged."),
    ("import_order", "easy", "Reorder Controller Imports",
     "Controller imports are inconsistently ordered.",
     "Reorder imports in the {entity} controller.",
     "Executable behaviour is unchanged."),
    ("comment_update", "easy", "Update Endpoint Code Comment",
     "A comment above an endpoint is outdated.",
     "Rewrite the comment describing {entity} handling.",
     "No API behaviour changes."),
    ("dto_variable", "easy", "Rename Local DTO Variable",
     "A local DTO variable has an unclear name.",
     "Rename the local {entity} DTO variable.",
     "The serialized DTO contract remains unchanged."),
    ("swagger_example_text", "easy", "Correct Swagger Example Text",
     "An API example contains a spelling mistake.",
     "Correct the example text.",
     "No endpoint behaviour changes."),
    ("controller_file_name", "medium", "Rename Controller Source File",
     "A controller filename violates naming conventions.",
     "Rename the source file containing {entity} handlers.",
     "Routes and compiled behaviour remain unchanged."),
    ("test_method_name", "easy", "Rename API Unit Test",
     "An API test name is unclear.",
     "Rename the test covering {entity} requests.",
     "The test assertions remain unchanged."),
    ("documentation_order", "medium", "Reorder Swagger Documentation",
     "Endpoint documentation appears in an inconvenient order.",
     "Change documentation ordering for {entity} endpoints.",
     "No contract changes."),
    ("local_constant_name", "easy", "Rename Controller Constant",
     "An internal constant has a vague name.",
     "Rename the local constant used in {entity} handling.",
     "The constant value remains identical."),
    ("formatting_cleanup", "easy", "Reformat Controller Source",
     "Controller formatting is inconsistent.",
     "Apply standard formatting to the {entity} controller.",
     "Behaviour remains identical."),
    ("sample_header", "medium", "Update Documentation Header Example",
     "Swagger shows an outdated sample header value.",
     "Replace the documented header example.",
     "The required header contract is unchanged."),
]


# ================================================================
# Quality Evaluation scenarios
# ================================================================

QUALITY_SIGNIFICANT = [
    {
        "family": "authentication_strategy",
        "difficulty": "easy",
        "title": "Adopt Token-Based Authentication",
        "context": (
            "The {system} exposes protected operations involving {data}."
        ),
        "decision": (
            "Use token-based authentication with role-based authorization."
        ),
        "rationale": (
            "Stateless tokens support distributed API protection."
        ),
        "alternatives": ["Server-side sessions"],
        "trade_offs": [
            "Stateless authentication introduces token lifecycle management."
        ],
    },
    {
        "family": "encryption_strategy",
        "difficulty": "medium",
        "title": "Require Sensitive Data Encryption",
        "context": (
            "The {system} stores and transfers confidential {data}."
        ),
        "decision": (
            "Encrypt sensitive information both in transit and at rest."
        ),
        "rationale": "Encryption reduces exposure of confidential data.",
        "alternatives": ["Transport encryption only"],
        "trade_offs": [
            "Stronger protection increases key-management responsibilities."
        ],
    },
    {
        "family": "automatic_failover",
        "difficulty": "medium",
        "title": "Introduce Automatic Failover",
        "context": (
            "Critical {entity} workflows must continue after service failure."
        ),
        "decision": (
            "Use automated health monitoring and failover for critical services."
        ),
        "rationale": "Automatic failover reduces service interruption.",
        "alternatives": ["Manual recovery"],
        "trade_offs": [
            "Higher availability increases infrastructure complexity."
        ],
    },
    {
        "family": "rate_limiting",
        "difficulty": "hard",
        "title": "Apply Platform Rate Limiting",
        "context": (
            "Public endpoints require protection from excessive traffic."
        ),
        "decision": (
            "Apply centrally managed rate limits to exposed APIs."
        ),
        "rationale": "Rate limiting protects shared resources.",
        "alternatives": ["No global rate limiting"],
        "trade_offs": [
            "Protection may reject legitimate traffic bursts."
        ],
    },
    {
        "family": "central_observability",
        "difficulty": "hard",
        "title": "Adopt Centralised Observability",
        "context": (
            "Distributed failures are difficult to diagnose in the {system}."
        ),
        "decision": (
            "Use centralised logs, metrics and distributed tracing."
        ),
        "rationale": "Unified telemetry improves operational diagnosis.",
        "alternatives": ["Local logs only"],
        "trade_offs": [
            "Observability requires additional infrastructure and storage."
        ],
    },
    {
        "family": "security_audit_logging",
        "difficulty": "medium",
        "title": "Introduce Security Audit Logging",
        "context": (
            "Access to {resource} data must be auditable."
        ),
        "decision": (
            "Record security-sensitive access and modification events."
        ),
        "rationale": "Audit events support accountability and investigation.",
        "alternatives": ["General application logs only"],
        "trade_offs": [
            "Audit coverage increases storage and privacy-management requirements."
        ],
    },
    {
        "family": "circuit_breaker",
        "difficulty": "hard",
        "title": "Use Circuit Breakers for Remote Dependencies",
        "context": (
            "Repeated downstream failures can exhaust resources across the {system}."
        ),
        "decision": (
            "Apply circuit breakers to critical remote-service calls."
        ),
        "rationale": "Circuit breakers reduce cascading failure.",
        "alternatives": ["Continue calling failed services indefinitely"],
        "trade_offs": [
            "Failure isolation temporarily rejects some requests."
        ],
    },
    {
        "family": "availability_sla",
        "difficulty": "hard",
        "title": "Define High Availability Target",
        "context": (
            "The {system} supports time-sensitive operations for {users}."
        ),
        "decision": (
            "Design critical components to support a 99.9 percent availability target."
        ),
        "rationale": "An explicit target drives redundancy and recovery design.",
        "alternatives": ["Best-effort availability"],
        "trade_offs": [
            "Higher availability targets increase infrastructure cost."
        ],
    },
    {
        "family": "performance_budget",
        "difficulty": "hard",
        "title": "Define API Performance Budget",
        "context": (
            "The {critical_action} workflow must remain responsive under expected load."
        ),
        "decision": (
            "Apply a documented latency budget to critical request paths."
        ),
        "rationale": "Performance budgets make response-time requirements measurable.",
        "alternatives": ["No explicit latency target"],
        "trade_offs": [
            "Strict performance targets may constrain implementation choices."
        ],
    },
    {
        "family": "data_retention_policy",
        "difficulty": "hard",
        "title": "Adopt Data Retention Policy",
        "context": (
            "The {system} stores sensitive {data} for long periods."
        ),
        "decision": (
            "Apply explicit retention and deletion periods to sensitive records."
        ),
        "rationale": "Retention rules reduce unnecessary long-term data exposure.",
        "alternatives": ["Retain records indefinitely"],
        "trade_offs": [
            "Reduced exposure may limit access to historical information."
        ],
    },
    {
        "family": "secrets_management",
        "difficulty": "medium",
        "title": "Centralise Secrets Management",
        "context": (
            "Multiple services require database credentials and API secrets."
        ),
        "decision": (
            "Store runtime secrets in a dedicated secrets-management service."
        ),
        "rationale": "Central management reduces hard-coded credential exposure.",
        "alternatives": ["Secrets in source-controlled configuration"],
        "trade_offs": [
            "Improved security introduces dependency on secret infrastructure."
        ],
    },
    {
        "family": "disaster_recovery",
        "difficulty": "hard",
        "title": "Define Disaster Recovery Strategy",
        "context": (
            "A regional failure could make the {system} unavailable."
        ),
        "decision": (
            "Maintain tested disaster-recovery procedures and secondary infrastructure."
        ),
        "rationale": "Recovery planning limits prolonged outages.",
        "alternatives": ["Ad hoc restoration"],
        "trade_offs": [
            "Disaster readiness increases operational cost."
        ],
    },
    {
        "family": "authorization_model",
        "difficulty": "medium",
        "title": "Adopt Role-Based Access Control",
        "context": (
            "Different types of {users} require different permissions."
        ),
        "decision": (
            "Use role-based access control for protected business operations."
        ),
        "rationale": "RBAC provides consistent permission enforcement.",
        "alternatives": ["Per-endpoint custom permission checks"],
        "trade_offs": [
            "Central role design may be less flexible for unusual permissions."
        ],
    },
    {
        "family": "input_validation_policy",
        "difficulty": "medium",
        "title": "Standardise Input Validation",
        "context": (
            "External inputs reach multiple components in the {system}."
        ),
        "decision": (
            "Apply consistent schema validation at system boundaries."
        ),
        "rationale": "Boundary validation prevents malformed data from spreading internally.",
        "alternatives": ["Validate independently inside each business function"],
        "trade_offs": [
            "Consistent validation requires shared schemas and governance."
        ],
    },
    {
        "family": "backup_recovery_objective",
        "difficulty": "hard",
        "title": "Define Recovery Objectives",
        "context": (
            "Loss of {data} would significantly affect business operations."
        ),
        "decision": (
            "Define explicit recovery-point and recovery-time objectives."
        ),
        "rationale": "Recovery objectives guide backup and resilience mechanisms.",
        "alternatives": ["Undefined best-effort recovery"],
        "trade_offs": [
            "Stricter recovery objectives require greater infrastructure investment."
        ],
    },
]


QUALITY_MINOR = [
    ("log_wording", "easy", "Rewrite Debug Log Message",
     "A debug message for {entity} processing is unclear.",
     "Rewrite the debug message.",
     "Runtime quality behaviour remains unchanged."),
    ("test_name", "easy", "Rename Quality Test",
     "A quality test has an unclear name.",
     "Rename the test covering {entity} behaviour.",
     "Assertions remain unchanged."),
    ("dashboard_label", "easy", "Change Dashboard Label",
     "A monitoring label uses outdated terminology.",
     "Rename the label showing {entity} activity.",
     "Metrics and alerting remain unchanged."),
    ("threshold_description", "medium", "Clarify Threshold Documentation",
     "Documentation describing a performance threshold is unclear.",
     "Rewrite the threshold description.",
     "The numerical threshold remains unchanged."),
    ("security_comment", "medium", "Update Security Comment",
     "A security middleware comment uses outdated terminology.",
     "Rewrite the comment for {entity} security handling.",
     "The security mechanism remains unchanged."),
    ("test_description", "easy", "Rewrite Test Description",
     "A test description is difficult to understand.",
     "Rewrite the description of the {entity} quality test.",
     "Test logic remains unchanged."),
    ("dashboard_order", "easy", "Reorder Dashboard Widgets",
     "Monitoring widgets are displayed in an inconvenient order.",
     "Move the {entity} widget to a different dashboard position.",
     "Monitoring behaviour remains unchanged."),
    ("alert_name", "medium", "Rename Existing Alert",
     "An alert name is unclear to operators.",
     "Rename the existing {entity} alert.",
     "Alert conditions remain unchanged."),
    ("metric_description", "easy", "Update Metric Description",
     "A metric description is incomplete.",
     "Rewrite the description for the {entity} metric.",
     "Metric collection remains unchanged."),
    ("report_heading", "easy", "Rename Quality Report Heading",
     "A report heading uses inconsistent wording.",
     "Rename the {entity} quality-report heading.",
     "Evaluation results remain unchanged."),
    ("format_test_output", "easy", "Reformat Test Output",
     "Quality-test output is difficult to read.",
     "Change formatting of the {entity} test output.",
     "Pass/fail behaviour remains unchanged."),
    ("monitoring_comment", "easy", "Update Monitoring Comment",
     "A monitoring configuration comment is outdated.",
     "Rewrite the comment describing {entity} metrics.",
     "Configuration values remain unchanged."),
    ("dashboard_colour", "easy", "Change Dashboard Colour",
     "A dashboard colour has poor contrast.",
     "Change the visual colour for the {entity} widget.",
     "No monitoring logic changes."),
    ("documentation_typo", "easy", "Correct Security Documentation Typo",
     "Security documentation contains a spelling mistake.",
     "Correct the typo relating to {entity} protection.",
     "Security controls remain unchanged."),
    ("test_file_name", "medium", "Rename Quality Test File",
     "A test filename is inconsistent with conventions.",
     "Rename the file containing {entity} quality tests.",
     "Test execution behaviour remains unchanged."),
]


def convert_minor_scenarios(items):
    result = []

    for (
        family,
        difficulty,
        title,
        context,
        decision,
        rationale,
    ) in items:
        result.append(
            {
                "family": family,
                "difficulty": difficulty,
                "title": title,
                "context": context,
                "decision": decision,
                "rationale": rationale,
                "alternatives": [],
                "trade_offs": [],
            }
        )

    return result


ARCHITECTURE_MINOR = convert_minor_scenarios(
    ARCHITECTURE_MINOR
)

DATABASE_MINOR = convert_minor_scenarios(
    DATABASE_MINOR
)

API_MINOR = convert_minor_scenarios(
    API_MINOR
)

QUALITY_MINOR = convert_minor_scenarios(
    QUALITY_MINOR
)


MODULES = [
    (
        "architecture_decision",
        ARCHITECTURE_SIGNIFICANT,
        ARCHITECTURE_MINOR,
    ),
    (
        "database_design",
        DATABASE_SIGNIFICANT,
        DATABASE_MINOR,
    ),
    (
        "api_component_design",
        API_SIGNIFICANT,
        API_MINOR,
    ),
    (
        "quality_evaluation",
        QUALITY_SIGNIFICANT,
        QUALITY_MINOR,
    ),
]


def build_dataset():
    rows = []
    record_number = 1

    for (
        source_module,
        significant_scenarios,
        minor_scenarios,
    ) in MODULES:

        if len(significant_scenarios) != 15:
            raise ValueError(
                f"{source_module} must contain exactly "
                "15 significant scenarios."
            )

        if len(minor_scenarios) != 15:
            raise ValueError(
                f"{source_module} must contain exactly "
                "15 non-significant scenarios."
            )

        for scenario in significant_scenarios:
            for domain in DOMAINS:
                decision_id = (
                    f"ADR-CAND-{record_number:04d}"
                )

                rows.append(
                    make_row(
                        decision_id=decision_id,
                        source_module=source_module,
                        domain=domain,
                        scenario=scenario,
                        label=1,
                    )
                )

                record_number += 1

        for scenario in minor_scenarios:
            for domain in DOMAINS:
                decision_id = (
                    f"ADR-CAND-{record_number:04d}"
                )

                rows.append(
                    make_row(
                        decision_id=decision_id,
                        source_module=source_module,
                        domain=domain,
                        scenario=scenario,
                        label=0,
                    )
                )

                record_number += 1

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
    positive = sum(
        int(row["label"]) == 1
        for row in rows
    )

    negative = sum(
        int(row["label"]) == 0
        for row in rows
    )

    print()
    print("ADR Significance Candidate Dataset")
    print("==================================")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Total: {len(rows)}")
    print(f"Significant: {positive}")
    print(f"Not significant: {negative}")

    print()
    print("Source modules:")

    for source_module in sorted(
        set(
            row["source_module"]
            for row in rows
        )
    ):
        count = sum(
            row["source_module"]
            == source_module
            for row in rows
        )

        print(
            f"  {source_module}: {count}"
        )

    print()
    print("Domains:")

    for domain in sorted(
        set(
            row["domain"]
            for row in rows
        )
    ):
        count = sum(
            row["domain"] == domain
            for row in rows
        )

        print(
            f"  {domain}: {count}"
        )

    families = set(
        (
            row["source_module"],
            row["scenario_family"],
            row["label"],
        )
        for row in rows
    )

    print()
    print(
        f"Distinct module/family/label groups: "
        f"{len(families)}"
    )

    print()
    print(
        "Labels are provisional and require "
        "human/expert review."
    )


if __name__ == "__main__":
    dataset = build_dataset()

    save_dataset(
        dataset
    )

    print_summary(
        dataset
    )