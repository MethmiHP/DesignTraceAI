class PromptManager:

    @staticmethod
    def api_generation_prompt(
        requirement: str,
        semantic_data: dict,
        architecture_context: dict,
        database_context: dict,
    ) -> str:

        return f"""
You are assisting with software API design.

Functional Requirement:
{requirement}

Extracted Semantics:
{semantic_data}

Architecture Context:
{architecture_context}

Database Context:
{database_context}

Rules:
- Respect the existing architecture boundaries.
- Do not create a new component unless explicitly required.
- Use database information only as design context.
- Do not expose sensitive internal database fields.
- Preserve the source requirement ID.
- Generate a REST API operation.

Return:
- service_id
- detailed_responsibility
- HTTP method
- path
- request schema
- response schema
- error responses
"""