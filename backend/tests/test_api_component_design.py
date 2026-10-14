from copy import deepcopy

from fastapi.testclient import TestClient

from app import app


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