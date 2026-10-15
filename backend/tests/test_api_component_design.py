from copy import deepcopy

from fastapi.testclient import TestClient

from app import app

import asyncio

from modules.api_component_design.service import (
    APIComponentDesignService,
)

from modules.api_component_design.schemas import (
    APIComponentDesignRequest,
)

from modules.api_component_design.llm.stub_provider import (
    StubLLMProvider,
)

from modules.api_component_design.llm.structured_schemas import (
    APIFieldSpec,
    APIErrorSpec,
    LLMAPIOperation,
)


client = TestClient(app)



# BASE TEST DATA


def get_base_request():

    return {
        "project_id": "careflow-test-001",

        "functional_requirements": [
            {
                "requirement_id": "FR-003",
                "statement": (
                    "A patient shall book an available "
                    "appointment with a selected doctor."
                ),
                "priority": "High",
            }
        ],

        "architecture": {
            "architecture_id": "ARCH-001",
            "selected_architecture": "Modular Architecture",

            "elements": [
                {
                    "element_id": "COMP-APPOINTMENT",
                    "name": "Appointment Module",
                    "type": "Module",
                    "main_responsibility": (
                        "Manage appointment booking, "
                        "availability, rescheduling "
                        "and cancellation."
                    ),
                }
            ],
        },

        "database": {
            "entities": [
                {
                    "entity_id": "DB-APPOINTMENT",
                    "name": "Appointment",

                    "attributes": [
                        "appointment_id",
                        "patient_id",
                        "doctor_id",
                        "availability_id",
                        "status",
                    ],

                    "primary_key": "appointment_id",

                    "foreign_keys": [
                        "patient_id -> Patient",
                        "doctor_id -> Doctor",
                        "availability_id -> Availability",
                    ],

                    "constraints": [],
                },

                {
                    "entity_id": "DB-PATIENT",
                    "name": "Patient",

                    "attributes": [
                        "patient_id",
                        "name",
                    ],

                    "primary_key": "patient_id",
                    "foreign_keys": [],
                    "constraints": [],
                },

                {
                    "entity_id": "DB-DOCTOR",
                    "name": "Doctor",

                    "attributes": [
                        "doctor_id",
                        "name",
                    ],

                    "primary_key": "doctor_id",
                    "foreign_keys": [],
                    "constraints": [],
                },

                {
                    "entity_id": "DB-AVAILABILITY",
                    "name": "Availability",

                    "attributes": [
                        "availability_id",
                        "doctor_id",
                    ],

                    "primary_key": "availability_id",

                    "foreign_keys": [
                        "doctor_id -> Doctor",
                    ],

                    "constraints": [],
                },
            ],

            "relationships": [],
            "constraints": [],
        },

        "non_functional_requirements": [],
    }



# TEST 1 - BOOK APPOINTMENT


def test_book_appointment():

    request_data = get_base_request()

    response = client.post(
        "/api-component/design",
        json=request_data,
    )

    assert response.status_code == 200

    data = response.json()

    semantic = data[
        "semantic_extractions"
    ][0]

    assert (
        semantic["actor"]
        == "Patient"
    )

    assert (
        semantic["action"]
        == "book"
    )

    assert (
        semantic["resource"]
        == "Appointment"
    )


    responsibility = data[
        "responsibilities"
    ][0]

    assert (
        responsibility[
            "element_name"
        ]
        == "Appointment Module"
    )


    operation = data[
        "api_operations"
    ][0]

    assert (
        operation["method"]
        == "POST"
    )

    assert (
        operation["path"]
        == "/appointments"
    )


    mapping = data[
        "requirement_to_api_mapping"
    ][0]

    assert (
        mapping["requirement_id"]
        == "FR-003"
    )

    assert (
        mapping["operation_id"]
        == "createAppointment"
    )


    assert (
        data[
            "openapi_document"
        ][
            "openapi"
        ]
        == "3.1.0"
    )

    assert (
        data[
            "validation"
        ][
            "valid"
        ]
        is True
    )



# TEST 2 - RESCHEDULE APPOINTMENT


def test_reschedule_appointment():

    request_data = get_base_request()

    request_data[
        "functional_requirements"
    ][0] = {
        "requirement_id": "FR-004",
        "statement": (
            "A patient shall reschedule an appointment "
            "to another available consultation slot."
        ),
        "priority": "High",
    }


    response = client.post(
        "/api-component/design",
        json=request_data,
    )

    assert response.status_code == 200

    data = response.json()

    semantic = data[
        "semantic_extractions"
    ][0]

    assert (
        semantic["actor"]
        == "Patient"
    )

    assert (
        semantic["action"]
        == "reschedule"
    )

    assert (
        semantic["resource"]
        == "Appointment"
    )


    operation = data[
        "api_operations"
    ][0]

    assert (
        operation["method"]
        == "PATCH"
    )

    assert (
        operation["path"]
        == (
            "/appointments/"
            "{appointment_id}/reschedule"
        )
    )

    assert (
        operation["operation_id"]
        == "rescheduleAppointment"
    )

    assert (
        data[
            "validation"
        ][
            "valid"
        ]
        is True
    )



# TEST 3 - CANCEL APPOINTMENT


def test_cancel_appointment():

    request_data = get_base_request()

    request_data[
        "functional_requirements"
    ][0] = {
        "requirement_id": "FR-005",
        "statement": (
            "A patient shall cancel "
            "an appointment."
        ),
        "priority": "High",
    }


    response = client.post(
        "/api-component/design",
        json=request_data,
    )

    assert response.status_code == 200

    data = response.json()

    semantic = data[
        "semantic_extractions"
    ][0]

    assert (
        semantic["actor"]
        == "Patient"
    )

    assert (
        semantic["action"]
        == "cancel"
    )

    assert (
        semantic["resource"]
        == "Appointment"
    )


    operation = data[
        "api_operations"
    ][0]

    assert (
        operation["method"]
        == "POST"
    )

    assert (
        operation["path"]
        == (
            "/appointments/"
            "{appointment_id}/cancel"
        )
    )

    assert (
        operation["operation_id"]
        == "cancelAppointment"
    )

    assert (
        data[
            "validation"
        ][
            "valid"
        ]
        is True
    )



# TEST 4
# BERT EXTRACTS RESOURCE BUT ARCHITECTURE MAPPING FAILS


def test_unmapped_resource_after_bert_extraction():

    request_data = get_base_request()

    request_data[
        "functional_requirements"
    ][0] = {
        "requirement_id": "FR-UNKNOWN",
        "statement": (
            "A patient shall manage "
            "a medical certificate."
        ),
        "priority": "Medium",
    }


    response = client.post(
        "/api-component/design",
        json=request_data,
    )

    assert response.status_code == 200

    data = response.json()



    # BERT should understand the requirement


    semantic = data[
        "semantic_extractions"
    ][0]

    assert (
        semantic["actor"]
        == "Patient"
    )

    assert (
        semantic["action"]
        == "manage"
    )

    assert (
        semantic["resource"]
        == "Medical Certificate"
    )


    # The supplied architecture does not contain a
    # Medical Certificate component/module.
    #
    # Therefore architecture mapping should fail.


    assert (
        len(
            data[
                "responsibilities"
            ]
        )
        == 0
    )

    assert (
        len(
            data[
                "api_operations"
            ]
        )
        == 0
    )



    # Overall validation should fail because architecture
    # mapping failure is an ERROR.


    assert (
        data[
            "validation"
        ][
            "valid"
        ]
        is False
    )


    issue_codes = [
        issue["code"]
        for issue
        in data[
            "validation"
        ][
            "issues"
        ]
    ]

    assert (
        "ARCHITECTURE_MAPPING_FAILED"
        in issue_codes
    )



# TEST 5 - NO MATCHING ARCHITECTURE ELEMENT


def test_no_matching_architecture_element():

    request_data = get_base_request()

    request_data[
        "architecture"
    ][
        "elements"
    ] = [
        {
            "element_id": "COMP-PAYMENT",
            "name": "Payment Module",
            "type": "Module",
            "main_responsibility": (
                "Manage payments "
                "and payment transactions."
            ),
        }
    ]


    response = client.post(
        "/api-component/design",
        json=request_data,
    )

    assert response.status_code == 200

    data = response.json()


    assert (
        data[
            "validation"
        ][
            "valid"
        ]
        is False
    )


    issue_codes = [
        issue["code"]
        for issue
        in data[
            "validation"
        ][
            "issues"
        ]
    ]


    assert (
        "ARCHITECTURE_MAPPING_FAILED"
        in issue_codes
    )



# TEST 6 - MISSING DATABASE ENTITIES


def test_missing_database_entities():

    request_data = get_base_request()

    request_data[
        "database"
    ][
        "entities"
    ] = []


    response = client.post(
        "/api-component/design",
        json=request_data,
    )

    assert response.status_code == 200

    data = response.json()


    assert (
        data[
            "validation"
        ][
            "valid"
        ]
        is False
    )


    issue_codes = [
        issue["code"]
        for issue
        in data[
            "validation"
        ][
            "issues"
        ]
    ]


    assert (
        "NO_DATABASE_ENTITIES"
        in issue_codes
    )


# TEST 7 - DUPLICATE REQUIREMENT ID


def test_duplicate_requirement_id():

    request_data = get_base_request()

    duplicate_requirement = deepcopy(
        request_data[
            "functional_requirements"
        ][0]
    )


    request_data[
        "functional_requirements"
    ].append(
        duplicate_requirement
    )


    response = client.post(
        "/api-component/design",
        json=request_data,
    )

    assert response.status_code == 200

    data = response.json()


    assert (
        data[
            "validation"
        ][
            "valid"
        ]
        is False
    )


    issue_codes = [
        issue["code"]
        for issue
        in data[
            "validation"
        ][
            "issues"
        ]
    ]


    assert (
        "DUPLICATE_REQUIREMENT_ID"
        in issue_codes
    )



# TEST 8 - SERVICE USES LLM API GENERATION



def test_service_uses_llm_api_generator():


    # Fake structured response from the LLM.
    #
    # We intentionally use a different operation_id from
    # the baseline generator so that we can prove the
    # LLM path was actually selected.
    

    llm_response = LLMAPIOperation(
        operation_id="bookAppointmentViaLLM",

        requirement_id="FR-003",

        element_id="COMP-APPOINTMENT",

        method="POST",

        path="/appointments",

        request_fields=[
            APIFieldSpec(
                name="doctor_id",
                type="uuid",
            ),

            APIFieldSpec(
                name="availability_id",
                type="uuid",
            ),
        ],

        response_fields=[
            APIFieldSpec(
                name="appointment_id",
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
                message="Authentication required",
            ),

            APIErrorSpec(
                status_code="409",
                message=(
                    "Selected slot is unavailable"
                ),
            ),
        ],
    )



    # Stub LLM provider


    stub_llm = StubLLMProvider(
        llm_response
    )



    # Create service with LLM explicitly enabled.
    #
    # Gemini is NOT called because we inject StubLLMProvider.
   

    service = APIComponentDesignService(
        llm_provider=stub_llm,
        enable_llm=True,
    )



    # Use the same request data as the existing
    # appointment tests.
    

    request_data = get_base_request()

    request = APIComponentDesignRequest(
        **request_data
    )


   
    # Run service
   

    result = asyncio.run(
        service.design(
            request
        )
    )



    # VERIFY LLM PATH WAS USED


    assert len(
        result.api_operations
    ) == 1


    operation = (
        result.api_operations[0]
    )


    # Baseline generator would return:
    #
    # createAppointment
    #
    # Therefore this proves that the LLM result
    # was selected instead.
    assert (
        operation.operation_id
        == "bookAppointmentViaLLM"
    )


    assert (
        operation.method
        == "POST"
    )


    assert (
        operation.path
        == "/appointments"
    )


    assert (
        operation.request_schema
        == {
            "doctor_id": "uuid",
            "availability_id": "uuid",
        }
    )


    assert (
        operation.response_schema
        == {
            "appointment_id": "uuid",
            "status": "string",
        }
    )



    # VERIFY REQUIREMENT -> API TRACEABILITY


    assert len(
        result.requirement_to_api_mapping
    ) == 1


    mapping = (
        result.requirement_to_api_mapping[0]
    )


    assert (
        mapping.requirement_id
        == "FR-003"
    )


    assert (
        mapping.operation_id
        == "bookAppointmentViaLLM"
    )



    # VERIFY THE LLM RECEIVED THE GROUNDED PROMPT
 
    prompt = stub_llm.last_prompt

    assert prompt is not None

    assert (
        "A patient shall book an available "
        "appointment with a selected doctor."
        in prompt
    )

    assert "Patient" in prompt

    assert "book" in prompt

    assert "Appointment" in prompt

    assert "Appointment Module" in prompt

    assert "appointment_id" in prompt

    assert "doctor_id" in prompt

    assert "availability_id" in prompt


# TEST 9 - LLM HALLUCINATED REQUEST FIELD IS DETECTED


def test_llm_ungrounded_request_field_detected():

    # Simulate an LLM response that invents a field
    # which does not exist in the supplied database context.

    llm_response = LLMAPIOperation(
        operation_id="bookAppointmentViaLLM",

        requirement_id="FR-003",

        element_id="COMP-APPOINTMENT",

        method="POST",

        path="/appointments",

        request_fields=[
            APIFieldSpec(
                name="doctor_id",
                type="uuid",
            ),

            APIFieldSpec(
                name="availability_id",
                type="uuid",
            ),

            # Hallucinated field
            APIFieldSpec(
                name="insurance_secret_code",
                type="string",
            ),
        ],

        response_fields=[
            APIFieldSpec(
                name="appointment_id",
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
        ],
    )


    stub_llm = StubLLMProvider(
        llm_response
    )


    service = APIComponentDesignService(
        llm_provider=stub_llm,
        enable_llm=True,
    )


    request = APIComponentDesignRequest(
        **get_base_request()
    )


    result = asyncio.run(
        service.design(
            request
        )
    )


    issue_codes = [
        issue.code
        for issue
        in result.validation.issues
    ]


    # The validator should identify the
    # hallucinated request field.
    assert (
        "UNGROUNDED_REQUEST_FIELD"
        in issue_codes
    )


    # Currently this issue is a WARNING,
    # therefore the complete design is still
    # considered valid.
    assert (
        result.validation.valid
        is True
    )


  
# TEST 10 - LLM HALLUCINATED PATH PARAMETER IS REJECTED



def test_llm_ungrounded_path_parameter_rejected():

    # Simulate an LLM response that invents a path
    # parameter that does not exist in the database.

    llm_response = LLMAPIOperation(
        operation_id="updateAppointmentViaLLM",

        requirement_id="FR-003",

        element_id="COMP-APPOINTMENT",

        method="PATCH",

        # made_up_id does NOT exist
        # in the supplied database context.
        path=(
            "/appointments/"
            "{made_up_id}"
        ),

        request_fields=[
            APIFieldSpec(
                name="status",
                type="string",
            ),
        ],

        response_fields=[
            APIFieldSpec(
                name="appointment_id",
                type="uuid",
            ),

            APIFieldSpec(
                name="status",
                type="string",
            ),
        ],

        errors=[
            APIErrorSpec(
                status_code="404",
                message="Appointment not found",
            ),
        ],
    )


    stub_llm = StubLLMProvider(
        llm_response
    )


    service = APIComponentDesignService(
        llm_provider=stub_llm,
        enable_llm=True,
    )


    request = APIComponentDesignRequest(
        **get_base_request()
    )


    result = asyncio.run(
        service.design(
            request
        )
    )


    issue_codes = [
        issue.code
        for issue
        in result.validation.issues
    ]


    # Unknown path identifiers are treated
    # more strictly than request-body fields.
    assert (
        "UNGROUNDED_PATH_PARAMETER"
        in issue_codes
    )


    # This guardrail is an ERROR,
    # therefore final validation must fail.
    assert (
        result.validation.valid
        is False
    )


# TEST 11 - SAFE STRUCTURAL REFINEMENT



def test_refinement_fixes_safe_structural_issues():

    # Simulate an LLM result with:
    #
    # - lowercase HTTP method
    # - missing leading /
    # - uppercase path segment
    # - duplicated trailing /
    #
    # These are safe deterministic corrections.

    llm_response = LLMAPIOperation(
        operation_id="bookAppointmentViaLLM",

        requirement_id="FR-003",

        element_id="COMP-APPOINTMENT",

        method="post",

        path="Appointments//",

        request_fields=[
            APIFieldSpec(
                name="doctor_id",
                type="uuid",
            ),

            APIFieldSpec(
                name="availability_id",
                type="uuid",
            ),
        ],

        response_fields=[
            APIFieldSpec(
                name="appointment_id",
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
        ],
    )


    stub_llm = StubLLMProvider(
        llm_response
    )


    service = APIComponentDesignService(
        llm_provider=stub_llm,
        enable_llm=True,
    )


    request = APIComponentDesignRequest(
        **get_base_request()
    )


    result = asyncio.run(
        service.design(
            request
        )
    )


    assert len(
        result.api_operations
    ) == 1


    operation = (
        result.api_operations[0]
    )


    # Refinement should normalize method.
    assert (
        operation.method
        == "POST"
    )


    # Refinement should normalize path:
    #
    # Appointments//
    # ->
    # /appointments
    assert (
        operation.path
        == "/appointments"
    )


    # Final validation is performed after
    # refinement, so the corrected operation
    # should now be valid.
    assert (
        result.validation.valid
        is True
    )


    issue_codes = [
        issue.code
        for issue
        in result.validation.issues
    ]


    assert (
        "INVALID_PATH"
        not in issue_codes
    )

    assert (
        "INVALID_HTTP_METHOD"
        not in issue_codes
    )



# TEST 12 - REFINEMENT DOES NOT HIDE UNSUPPORTED METHOD



def test_refinement_preserves_unfixable_http_method_error():

    # TRACE is not part of the supported API method set.
    #
    # Refinement may normalize its casing, but it must
    # NOT invent a different method such as GET or POST.

    llm_response = LLMAPIOperation(
        operation_id="bookAppointmentViaLLM",

        requirement_id="FR-003",

        element_id="COMP-APPOINTMENT",

        method="trace",

        path="/appointments",

        request_fields=[],

        response_fields=[
            APIFieldSpec(
                name="appointment_id",
                type="uuid",
            ),
        ],

        errors=[],
    )


    stub_llm = StubLLMProvider(
        llm_response
    )


    service = APIComponentDesignService(
        llm_provider=stub_llm,
        enable_llm=True,
    )


    request = APIComponentDesignRequest(
        **get_base_request()
    )


    result = asyncio.run(
        service.design(
            request
        )
    )


    assert len(
        result.api_operations
    ) == 1


    operation = (
        result.api_operations[0]
    )


    # Refinement normalizes casing only.
    assert (
        operation.method
        == "TRACE"
    )


    # It must NOT guess a replacement method.
    assert (
        operation.method
        not in {
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        }
    )


    issue_codes = [
        issue.code
        for issue
        in result.validation.issues
    ]


    assert (
        "INVALID_HTTP_METHOD"
        in issue_codes
    )


    assert (
        result.validation.valid
        is False
    )


    # TEST 13 - LLM PROVIDER FAILURE USES BASELINE FALLBACK

def test_llm_provider_failure_uses_baseline_fallback():

    class FailingLLMProvider:

        def generate_structured(
            self,
            prompt,
            schema_class,
        ):
            raise RuntimeError(
                "Simulated LLM provider failure"
            )


    service = APIComponentDesignService(
        llm_provider=FailingLLMProvider(),
        enable_llm=True,
    )


    request = APIComponentDesignRequest(
        **get_base_request()
    )


    result = asyncio.run(
        service.design(
            request
        )
    )


    issue_codes = [
        issue.code
        for issue
        in result.validation.issues
    ]


    assert (
        "LLM_API_GENERATION_FAILED"
        in issue_codes
    )


    # FR-003 has a deterministic appointment
    # baseline rule, so fallback should still
    # produce an API operation.

    assert len(
        result.api_operations
    ) == 1


    assert (
        result.validation.valid
        is True
    )