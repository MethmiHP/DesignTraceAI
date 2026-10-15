# API generation providers

With `API_COMPONENT_ENABLE_LLM=true`, each mapped requirement is processed in order:

1. Gemini
2. Groq, if Gemini cannot initialize, fails, or returns invalid structured output
3. `BaselineAPIGenerator`, if both LLM providers fail

Both provider outputs must pass the Pydantic structured-output schema. API design
checks (database grounding, architecture traceability, etc.) still run afterward;
schema-valid semantic errors appear in validation results, rather than being
silently replaced. The baseline only handles its supported actions.

Add these settings to `backend/.env` (keep your real keys out of version control):

```dotenv
API_COMPONENT_ENABLE_LLM=true
GEMINI_API_KEY=your_existing_gemini_key
API_COMPONENT_LLM_MODEL=gemini-3.8-flash
GROQ_API_KEY=your_groq_key
API_COMPONENT_GROQ_MODEL=openai/gpt-oss-120b
```

Restart the backend after editing `.env`. No frontend key or configuration is needed.
`API_COMPONENT_ENABLE_LLM=false` selects baseline-only mode. Tests use offline
providers and do not consume quota. Explicitly injecting `llm_provider` into the
service replaces the default chain, allowing isolated testing.

Groq uses `httpx` (already used by the backend's test client) and its HTTPS chat
completions endpoint with strict JSON Schema output. Use a Groq model supporting
strict structured output when overriding the default:
https://console.groq.com/docs/structured-outputs

Provider failures log only their names and exception types. If both fail, the
existing `LLM_API_GENERATION_FAILED` warning appears in the response and saved
outputs when baseline generation is attempted. The manual Gemini-only test script
continues to test Gemini specifically; the full chain runs through the service.

## Security design

The API design request accepts a `security` policy. It applies to every generated
operation; an optional `functional_requirements[i].security` policy overrides it
for one requirement. Existing clients default to `unspecified` and receive a
review warning rather than an invented authentication scheme.

```json
{
  "authentication": "bearer",
  "roles": ["customer"],
  "access_rules": ["Customers may access only their own bank accounts."]
}
```

Supported authentication values: `unspecified`, `none` (explicit public access),
`bearer`, `basic`, and `api_key`. API keys additionally accept `api_key_name`
(default `X-API-Key`) and `api_key_location` (`header`, `query`, or `cookie`).
Never include actual credentials in design input.

Policies are supplied to the LLM prompt, then attached deterministically to the
operation so neither provider nor baseline fallback can omit the declared policy.
Protected operations document 401 errors, plus 403 when roles/access rules exist.
OpenAPI includes `components.securitySchemes` and operation-level `security`.
Roles and access rules are exported as `x-required-roles` and `x-access-rules`;
they are not OAuth scopes. Public operations export `security: []`.

Validation flags missing/mismatched policies, contradictory public access,
and missing authentication/authorization errors. Authentication wording in
requirements can trigger a missing-configuration error, but this is a simple
keyword check, not complete natural-language security analysis. This feature
creates design metadata only: it does not secure the DesignTrace application or
implement authentication/authorization in the generated target API.
