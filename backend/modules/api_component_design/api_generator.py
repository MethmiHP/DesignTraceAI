import re

from .schemas import (
    APIOperation,
    DatabaseEntity,
    SemanticExtraction,
)


class BaselineAPIGenerator:

  
    # GENERIC ACTION GROUPS
   

    CREATE_ACTIONS = {
        "create",
        "add",
        "register",
        "submit",
        "upload",
        "issue",
        "generate",
    }

    READ_ACTIONS = {
        "get",
        "view",
        "retrieve",
        "read",
    }

    UPDATE_ACTIONS = {
        "update",
        "edit",
        "modify",
    }

    DELETE_ACTIONS = {
        "delete",
        "remove",
    }

    # Domain actions that can be represented as
    # an action endpoint.
    DOMAIN_ACTIONS = {
        "approve",
        "reject",
        "confirm",
        "assign",
        "schedule",
        "process",
    }


    # PUBLIC GENERATION METHOD
  

    def generate(
        self,
        semantic: SemanticExtraction,
        element_id: str,
        database_context: list[DatabaseEntity],
    ) -> APIOperation | None:

        action = (
            semantic.action.lower()
            if semantic.action
            else None
        )

        resource = semantic.resource

        requirement_id = (
            semantic.requirement_id
        )


        if not action or not resource:
            return None


      
        # DOMAIN-SPECIFIC RULES
        #
        # These rules have priority because they contain
        # more precise API design knowledge.
  


        
        # BOOK APPOINTMENT


        if (
            action == "book"
            and resource == "Appointment"
        ):

            return APIOperation(
                operation_id="createAppointment",
                requirement_id=requirement_id,
                element_id=element_id,

                method="POST",
                path="/appointments",

                request_schema={
                    "doctor_id": "uuid",
                    "availability_id": "uuid",
                },

                response_schema={
                    "appointment_id": "uuid",
                    "status": "BOOKED",
                },

                error_responses={
                    "400": "Invalid request",
                    "401": "Authentication required",
                    "403": "Operation not permitted",
                    "409": (
                        "Selected slot is unavailable"
                    ),
                },
            )


     
        # RESCHEDULE APPOINTMENT
  

        if (
            action == "reschedule"
            and resource == "Appointment"
        ):

            return APIOperation(
                operation_id=(
                    "rescheduleAppointment"
                ),
                requirement_id=requirement_id,
                element_id=element_id,

                method="PATCH",
                path=(
                    "/appointments/"
                    "{appointment_id}/reschedule"
                ),

                request_schema={
                    "new_availability_id": "uuid",
                },

                response_schema={
                    "appointment_id": "uuid",
                    "status": "RESCHEDULED",
                },

                error_responses={
                    "401": (
                        "Authentication required"
                    ),
                    "403": (
                        "Not appointment owner"
                    ),
                    "404": (
                        "Appointment not found"
                    ),
                    "409": (
                        "Selected slot unavailable"
                    ),
                    "422": (
                        "Rescheduling not permitted"
                    ),
                },
            )


      
        # CANCEL APPOINTMENT
       

        if (
            action == "cancel"
            and resource == "Appointment"
        ):

            return APIOperation(
                operation_id=(
                    "cancelAppointment"
                ),
                requirement_id=requirement_id,
                element_id=element_id,

                method="POST",
                path=(
                    "/appointments/"
                    "{appointment_id}/cancel"
                ),

                request_schema={
                    "reason": "string"
                },

                response_schema={
                    "appointment_id": "uuid",
                    "status": "CANCELLED",
                },

                error_responses={
                    "401": (
                        "Authentication required"
                    ),
                    "403": (
                        "Not appointment owner"
                    ),
                    "404": (
                        "Appointment not found"
                    ),
                    "422": (
                        "Cancellation not permitted"
                    ),
                },
            )


        # GENERIC DETERMINISTIC API GENERATION
  

        database_entity = (
            self._find_database_entity(
                resource,
                database_context,
            )
        )


        # Generic generation requires a matching
        # database entity so that endpoint and schema
        # generation are grounded in database context.
        if database_entity is None:
            return None


        resource_path = (
            self._resource_path(
                resource
            )
        )

        resource_class_name = (
            self._resource_class_name(
                resource
            )
        )

        primary_key = (
            self._get_primary_key(
                database_entity,
                resource,
            )
        )


        # GENERIC CREATE
        #
        # create/add/register/... Medical Certificate
        #
        # POST /medical-certificates
   

        if action in self.CREATE_ACTIONS:

            request_schema = (
                self._build_request_schema(
                    database_entity,
                    exclude_primary_key=True,
                )
            )

            response_schema = (
                self._build_response_schema(
                    database_entity
                )
            )


            return APIOperation(
                operation_id=(
                    f"create{resource_class_name}"
                ),
                requirement_id=requirement_id,
                element_id=element_id,

                method="POST",

                path=(
                    f"/{resource_path}"
                ),

                request_schema=(
                    request_schema
                ),

                response_schema=(
                    response_schema
                ),

                error_responses={
                    "400": "Invalid request",
                    "401": (
                        "Authentication required"
                    ),
                    "403": (
                        "Operation not permitted"
                    ),
                    "409": (
                        f"{resource} already exists "
                        "or conflicts with existing data"
                    ),
                },
            )


        # GENERIC READ
        #
        # view/retrieve/read Medical Certificate
        #
        # GET /medical-certificates/{medical_certificate_id}


        if action in self.READ_ACTIONS:

            response_schema = (
                self._build_response_schema(
                    database_entity
                )
            )


            return APIOperation(
                operation_id=(
                    f"get{resource_class_name}"
                ),
                requirement_id=requirement_id,
                element_id=element_id,

                method="GET",

                path=(
                    f"/{resource_path}/"
                    f"{{{primary_key}}}"
                ),

                request_schema={},

                response_schema=(
                    response_schema
                ),

                error_responses={
                    "401": (
                        "Authentication required"
                    ),
                    "403": (
                        "Operation not permitted"
                    ),
                    "404": (
                        f"{resource} not found"
                    ),
                },
            )


        # GENERIC UPDATE
        #
        # update/edit/modify Medical Certificate
        #
        # PATCH /medical-certificates/{medical_certificate_id}


        if action in self.UPDATE_ACTIONS:

            request_schema = (
                self._build_request_schema(
                    database_entity,
                    exclude_primary_key=True,
                )
            )

            response_schema = (
                self._build_response_schema(
                    database_entity
                )
            )


            return APIOperation(
                operation_id=(
                    f"update{resource_class_name}"
                ),
                requirement_id=requirement_id,
                element_id=element_id,

                method="PATCH",

                path=(
                    f"/{resource_path}/"
                    f"{{{primary_key}}}"
                ),

                request_schema=(
                    request_schema
                ),

                response_schema=(
                    response_schema
                ),

                error_responses={
                    "400": "Invalid request",
                    "401": (
                        "Authentication required"
                    ),
                    "403": (
                        "Operation not permitted"
                    ),
                    "404": (
                        f"{resource} not found"
                    ),
                    "409": (
                        "Update conflicts with "
                        "existing data"
                    ),
                },
            )


      
        # GENERIC DELETE
        #
        # delete/remove Medical Certificate
        #
        # DELETE /medical-certificates/{medical_certificate_id}


        if action in self.DELETE_ACTIONS:

            return APIOperation(
                operation_id=(
                    f"delete{resource_class_name}"
                ),
                requirement_id=requirement_id,
                element_id=element_id,

                method="DELETE",

                path=(
                    f"/{resource_path}/"
                    f"{{{primary_key}}}"
                ),

                request_schema={},

                response_schema={
                    primary_key: (
                        self._infer_type(
                            primary_key
                        )
                    ),
                    "status": "DELETED",
                },

                error_responses={
                    "401": (
                        "Authentication required"
                    ),
                    "403": (
                        "Operation not permitted"
                    ),
                    "404": (
                        f"{resource} not found"
                    ),
                    "409": (
                        f"{resource} cannot "
                        "be deleted"
                    ),
                },
            )


     
        # GENERIC DOMAIN ACTION
        #
        # approve Medical Certificate
        #
        # POST
        # /medical-certificates/{medical_certificate_id}/approve
    

        if action in self.DOMAIN_ACTIONS:

            return APIOperation(
                operation_id=(
                    f"{action}"
                    f"{resource_class_name}"
                ),
                requirement_id=requirement_id,
                element_id=element_id,

                method="POST",

                path=(
                    f"/{resource_path}/"
                    f"{{{primary_key}}}/"
                    f"{action}"
                ),

                request_schema={},

                response_schema={
                    primary_key: (
                        self._infer_type(
                            primary_key
                        )
                    ),
                    "status": (
                        action.upper()
                    ),
                },

                error_responses={
                    "400": "Invalid request",
                    "401": (
                        "Authentication required"
                    ),
                    "403": (
                        "Operation not permitted"
                    ),
                    "404": (
                        f"{resource} not found"
                    ),
                    "422": (
                        f"{action.capitalize()} "
                        "operation not permitted"
                    ),
                },
            )


       
        # UNSUPPORTED / AMBIGUOUS ACTION


        return None


  
    # DATABASE ENTITY MATCHING


    @staticmethod
    def _find_database_entity(
        resource: str,
        database_context: list[DatabaseEntity],
    ) -> DatabaseEntity | None:

        normalized_resource = (
            BaselineAPIGenerator
            ._normalize_name(
                resource
            )
        )


        for entity in database_context:

            normalized_entity = (
                BaselineAPIGenerator
                ._normalize_name(
                    entity.name
                )
            )

            if (
                normalized_entity
                == normalized_resource
            ):

                return entity


        return None


    # REQUEST SCHEMA


    @staticmethod
    def _build_request_schema(
        entity: DatabaseEntity,
        exclude_primary_key: bool = True,
    ) -> dict[str, str]:

        schema = {}

        for attribute in entity.attributes:

            if (
                exclude_primary_key
                and entity.primary_key
                and attribute
                == entity.primary_key
            ):

                continue


            schema[attribute] = (
                BaselineAPIGenerator
                ._infer_type(
                    attribute
                )
            )


        return schema


  
    # RESPONSE SCHEMA


    @staticmethod
    def _build_response_schema(
        entity: DatabaseEntity,
    ) -> dict[str, str]:

        schema = {}

        for attribute in entity.attributes:

            schema[attribute] = (
                BaselineAPIGenerator
                ._infer_type(
                    attribute
                )
            )


        return schema


    # PRIMARY KEY


    @staticmethod
    def _get_primary_key(
        entity: DatabaseEntity,
        resource: str,
    ) -> str:

        if entity.primary_key:
            return entity.primary_key


        resource_snake = (
            BaselineAPIGenerator
            ._to_snake_case(
                resource
            )
        )


        return (
            f"{resource_snake}_id"
        )


   
    # SIMPLE ATTRIBUTE TYPE INFERENCE


    @staticmethod
    def _infer_type(
        attribute: str,
    ) -> str:

        attribute_lower = (
            attribute.lower()
        )


        if (
            attribute_lower == "id"
            or attribute_lower.endswith(
                "_id"
            )
        ):

            return "uuid"


        # Keep the deterministic baseline simple.
        # OpenAPIBuilder already understands
        # string and uuid types.
        return "string"



    # RESOURCE -> REST PATH
    #
    # Medical Certificate
    # -> medical-certificates


    @staticmethod
    def _resource_path(
        resource: str,
    ) -> str:

        words = re.findall(
            r"[A-Za-z0-9]+",
            resource.lower(),
        )


        if not words:
            return "resources"


        last_word = words[-1]

        words[-1] = (
            BaselineAPIGenerator
            ._pluralize(
                last_word
            )
        )


        return "-".join(
            words
        )


  
    # RESOURCE -> CLASS STYLE NAME
    #
    # Medical Certificate
    # -> MedicalCertificate


    @staticmethod
    def _resource_class_name(
        resource: str,
    ) -> str:

        words = re.findall(
            r"[A-Za-z0-9]+",
            resource,
        )


        return "".join(
            word.capitalize()
            for word in words
        )



    # NAME NORMALIZATION


    @staticmethod
    def _normalize_name(
        value: str,
    ) -> str:

        return re.sub(
            r"[^a-z0-9]",
            "",
            value.lower(),
        )


    # SNAKE CASE
    #
    # Medical Certificate
    # -> medical_certificate
  

    @staticmethod
    def _to_snake_case(
        value: str,
    ) -> str:

        words = re.findall(
            r"[A-Za-z0-9]+",
            value.lower(),
        )

        return "_".join(
            words
        )



    # SIMPLE PLURALIZATION


    @staticmethod
    def _pluralize(
        word: str,
    ) -> str:

        if word.endswith(
            (
                "s",
                "x",
                "z",
                "ch",
                "sh",
            )
        ):

            return (
                word
                + "es"
            )


        if (
            word.endswith("y")
            and len(word) > 1
            and word[-2]
            not in "aeiou"
        ):

            return (
                word[:-1]
                + "ies"
            )


        return (
            word
            + "s"
        )