# Generated process outputs

Each completed API/component design run saves its artifacts here in a separate
`<project>_<UTC timestamp>_<unique ID>/` directory. This location is resolved from
the backend source, regardless of the terminal's working directory.

- `request.json`: submitted design input
- `raw_semantic_extractions.json`: BERT output before normalization
- `semantic_extractions.json`: normalized actors, actions, and resources
- `responsibilities.json`: component responsibilities
- `database_context.json`: relevant entities per mapped requirement
- `preprocessing_issues.json`: input validation issues
- `initial_api_operations.json`: operations before refinement
- `initial_openapi_document.json`: OpenAPI before refinement
- `initial_validation.json`: validation before refinement
- `refinement_issues.json`: issues supplied to refinement
- `api_operations.json`: final refined operations
- `requirement_to_api_mapping.json`: requirement-to-operation traceability
- `openapi_document.json`: final exportable OpenAPI document
- `validation.json`: final validation, including generation/fallback warnings
- `response.json`: the complete response returned to the caller

Results that fail design validation are saved too. Requests rejected by FastAPI
before the design process starts, and unexpected exceptions that prevent a
response from being produced, do not create a completed run folder. Filesystem
errors propagate instead of silently skipping persistence.

The manual Gemini generation script saves its returned operation as
`manual-gemini_<UTC timestamp>_<unique ID>/api_operation.json`.

Files are UTF-8, indented JSON. Runs are staged before their directory is renamed
into place, and existing runs are never overwritten. Generated run directories
are ignored by Git. Automated tests use temporary directories instead.
