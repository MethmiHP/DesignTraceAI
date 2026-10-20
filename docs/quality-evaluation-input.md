# Quality evaluation input

POST `/quality-evaluation/evaluate` with a compact coordinator payload. The frontend **Load example** supplies a complete example.

| Field | Relevant information |
| --- | --- |
| `project_id` | Project being evaluated |
| `functional_requirements` | Requirement ID and normalized statement; priority if supplied |
| `non_functional_requirements` | Requirement ID, normalized statement, category; priority if supplied |
| `architecture` | Architecture style, components, responsibilities, requirement IDs, relationships |
| `database` | Entities, columns/types, keys, nullability, uniqueness, relationships, constraints, requirement IDs |
| `api_component_design` | Responsibilities, operations, schemas, errors, security, parameters, requirement-to-API mappings, OpenAPI |

## Full upstream output compatibility

Full module outputs can still be submitted. The adapters extract the fields above; the complete upstream responses are not serialized into the evaluation context or LLM prompt.

- `requirement_analysis.requirements`: split by `requirement_type`; map `normalized_statement` to `statement`, and NFR `quality_attribute` to `category`.
- `architecture.high_level_design`: map `architecture_style` and components to the selected architecture and elements. Keep relationships and component requirement IDs.
- `database.design.tables`: map tables and columns to entities; translate foreign keys into `column -> table.column`. Retain structured column details and constraints.
- `api_component_design`: keep the API contract and responsibility/requirement mappings.

Excluded metadata includes original requirement text, requirement-analysis issue reports, ASR/confidence flags, summary counts, generated SRS, architecture rankings/scores, generic retrieved evidence, ADR alternatives, provider/generation metadata, upstream validation reports, semantic extraction intermediates, and SQL/diagram file paths. These are not independent evidence that design rules pass.

Typed fields use an allowlist: unrelated extra keys on module objects are ignored. Design dictionaries such as OpenAPI, request/response schemas, and security policies retain their contract contents.

## Validation

Nested project IDs, when supplied, must match the evaluation project ID. Do not combine unrelated projects by relabeling their IDs. Malformed components, columns, or foreign keys return HTTP 422. Duplicate analysis requirement IDs, blank normalized statements, and conflicting legacy requirement lists are rejected.

Supported NFR categories are Availability, Fault Tolerance, Legal, Look and Feel, Maintainability, Operational, Performance, Portability, Scalability, Security, and Usability. Upstream category matching ignores case and surrounding whitespace. Null or unsupported NFR categories return a clear error instead of being guessed. Null quality attributes on FRs are valid.

The raw-description input to requirement analysis is not a quality evaluation input. Supply its normalized requirements instead. Priorities are not inferred from ASR flags or confidence.

Existing deterministic API checks inspect OpenAPI. Retained operation security metadata does not fabricate missing OpenAPI security declarations.
