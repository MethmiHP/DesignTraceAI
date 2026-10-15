from types import SimpleNamespace
from shared.utils.output_store import save_outputs

from modules.api_component_design.llm.provider import (
    GeminiLLMProvider,
    LLMUnavailableError,
)

from modules.api_component_design.llm.llm_api_generator import (
    LLMAPIGenerator,
)

from modules.api_component_design.schemas import (
    DatabaseEntity,
    SemanticExtraction,
)


# REAL GEMINI PROVIDER


llm_provider = GeminiLLMProvider()

generator = LLMAPIGenerator(
    llm_provider=llm_provider
)



# SEMANTIC RESULT
#
# Assume this came from:
# BERT + semantic normalization

semantic = SemanticExtraction(
    requirement_id="FR-009",
    actor="Doctor",
    action="issue",
    resource="Medical Certificate",
    confidence=None,
)



# ARCHITECTURE CONTEXT


architecture_element = SimpleNamespace(
    element_id="COMP-MEDICAL-CERTIFICATE",
    name="Medical Certificate Module",
    type="Module",
    main_responsibility=(
        "Manage patient medical certificates "
        "and their lifecycle."
    ),
)



# DATABASE CONTEXT


database_context = [
    DatabaseEntity(
        entity_id="DB-MEDICAL-CERTIFICATE",
        name="Medical Certificate",

        attributes=[
            "medical_certificate_id",
            "patient_id",
            "issued_by",
            "issued_date",
            "status",
        ],

        primary_key="medical_certificate_id",

        foreign_keys=[
            "patient_id -> Patient"
        ],

        constraints=[],
    ),

    DatabaseEntity(
        entity_id="DB-PATIENT",
        name="Patient",

        attributes=[
            "patient_id",
            "name",
        ],

        primary_key="patient_id",

        foreign_keys=[],

        constraints=[],
    ),
]



# GENERATE API USING REAL GEMINI


try:
    operation = generator.generate(
        requirement_statement=(
            "A doctor shall issue a "
            "medical certificate to a patient."
        ),
        semantic=semantic,
        architecture_element=architecture_element,
        database_context=database_context,
    )
except LLMUnavailableError as exc:
    raise SystemExit(str(exc)) from None


# OUTPUT

output_path = save_outputs("manual-gemini", {
    "api_operation": operation.model_dump(mode="json"),
})
print(f"Saved output to: {output_path}")


print()
print("Generated API Operation")
print("=======================")

print(
    operation.model_dump_json(
        indent=2
    )
)
