from types import SimpleNamespace

from modules.api_component_design.llm.stub_provider import (
    StubLLMProvider,
)

from modules.api_component_design.llm.llm_api_generator import (
    LLMAPIGenerator,
)

from modules.api_component_design.llm.structured_schemas import (
    APIErrorSpec,
    APIFieldSpec,
    LLMAPIOperation,
)

from modules.api_component_design.schemas import (
    DatabaseEntity,
    SemanticExtraction,
)


def test_llm_api_generator():

  
    # EXPECTED LLM RESPONSE
    #
    # This is the Gemini-compatible intermediate format.
  

    expected_operation = LLMAPIOperation(
        operation_id=(
            "issueMedicalCertificate"
        ),

        requirement_id="FR-009",

        element_id=(
            "COMP-MEDICAL-CERTIFICATE"
        ),

        method="POST",

        path="/medical-certificates",

        request_fields=[
            APIFieldSpec(
                name="patient_id",
                type="uuid",
            ),

            APIFieldSpec(
                name="issued_by",
                type="string",
            ),

            APIFieldSpec(
                name="issued_date",
                type="string",
            ),
        ],

        response_fields=[
            APIFieldSpec(
                name=(
                    "medical_certificate_id"
                ),
                type="uuid",
            ),

            APIFieldSpec(
                name="status",
                type="string",
            ),
        ],

        errors=[
            APIErrorSpec(
                status_code="400",
                message="Invalid request",
            ),

            APIErrorSpec(
                status_code="401",
                message=(
                    "Authentication required"
                ),
            ),

            APIErrorSpec(
                status_code="403",
                message=(
                    "Operation not permitted"
                ),
            ),
        ],
    )


   
    # STUB LLM


    stub_llm = StubLLMProvider(
        expected_operation
    )


    generator = LLMAPIGenerator(
        llm_provider=stub_llm
    )


    # BERT + NORMALIZATION RESULT
   

    semantic = SemanticExtraction(
        requirement_id="FR-009",
        actor="Doctor",
        action="issue",
        resource="Medical Certificate",
        confidence=None,
    )


    # ARCHITECTURE CONTEXT
    

    architecture_element = SimpleNamespace(
        element_id=(
            "COMP-MEDICAL-CERTIFICATE"
        ),

        name=(
            "Medical Certificate Module"
        ),

        type="Module",

        main_responsibility=(
            "Manage patient medical "
            "certificates and their lifecycle."
        ),
    )



    # DATABASE CONTEXT
  

    database_context = [
        DatabaseEntity(
            entity_id=(
                "DB-MEDICAL-CERTIFICATE"
            ),

            name="Medical Certificate",

            attributes=[
                "medical_certificate_id",
                "patient_id",
                "issued_by",
                "issued_date",
                "status",
            ],

            primary_key=(
                "medical_certificate_id"
            ),

            foreign_keys=[
                "patient_id -> Patient"
            ],

            constraints=[],
        )
    ]


   
    # GENERATE
    #
    # LLMAPIGenerator must convert:
    #
    # LLMAPIOperation
    # ->
    # APIOperation
   

    operation = generator.generate(
        requirement_statement=(
            "A doctor shall issue a "
            "medical certificate to a patient."
        ),

        semantic=semantic,

        architecture_element=(
            architecture_element
        ),

        database_context=(
            database_context
        ),
    )



    # VERIFY FINAL APIOperation


    assert (
        operation.operation_id
        == "issueMedicalCertificate"
    )


    assert (
        operation.method
        == "POST"
    )


    assert (
        operation.path
        == "/medical-certificates"
    )


    assert (
        operation.requirement_id
        == "FR-009"
    )


    assert (
        operation.element_id
        == "COMP-MEDICAL-CERTIFICATE"
    )



    # VERIFY LIST -> DICT CONVERSION


    assert (
        operation.request_schema
        == {
            "patient_id": "uuid",
            "issued_by": "string",
            "issued_date": "string",
        }
    )


    assert (
        operation.response_schema
        == {
            "medical_certificate_id": "uuid",
            "status": "string",
        }
    )


    assert (
        operation.error_responses
        == {
            "400": "Invalid request",
            "401": (
                "Authentication required"
            ),
            "403": (
                "Operation not permitted"
            ),
        }
    )


    
    # VERIFY PROMPT GROUNDING
  

    prompt = stub_llm.last_prompt


    assert prompt is not None


    assert (
        "A doctor shall issue a "
        "medical certificate to a patient."
        in prompt
    )


    assert "Doctor" in prompt

    assert "issue" in prompt


    assert (
        "Medical Certificate"
        in prompt
    )


    assert (
        "Medical Certificate Module"
        in prompt
    )


    assert (
        "medical_certificate_id"
        in prompt
    )


    assert "patient_id" in prompt


    # VERIFY NEW GEMINI FORMAT IN PROMPT
  

    assert "request_fields" in prompt

    assert "response_fields" in prompt

    assert "status_code" in prompt