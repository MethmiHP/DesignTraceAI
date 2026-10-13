from .schemas import (
    APIOperation,
    DatabaseEntity,
    SemanticExtraction,
)


class BaselineAPIGenerator:

    def generate(
        self,
        semantic: SemanticExtraction,
        element_id: str,
        database_context: list[DatabaseEntity],
    ) -> APIOperation | None:

        action = semantic.action
        resource = semantic.resource
        requirement_id = semantic.requirement_id

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
                    "409": "Selected slot is unavailable",
                },
            )

        # RESCHEDULE
        if (
            action == "reschedule"
            and resource == "Appointment"
        ):

            return APIOperation(
                operation_id="rescheduleAppointment",
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
                    "401": "Authentication required",
                    "403": "Not appointment owner",
                    "404": "Appointment not found",
                    "409": "Selected slot unavailable",
                    "422": "Rescheduling not permitted",
                },
            )

        # CANCEL
        if (
            action == "cancel"
            and resource == "Appointment"
        ):

            return APIOperation(
                operation_id="cancelAppointment",
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
                    "401": "Authentication required",
                    "403": "Not appointment owner",
                    "404": "Appointment not found",
                    "422": "Cancellation not permitted",
                },
            )

        return None