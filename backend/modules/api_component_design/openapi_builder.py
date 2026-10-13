#This converts API operations into an OpenAPI document.

import re

from .schemas import APIOperation


class OpenAPIBuilder:

    def build(
        self,
        operations: list[APIOperation],
    ) -> dict:

        document = {
            "openapi": "3.1.0",

            "info": {
                "title": "DesignTrace AI Generated API",
                "version": "1.0.0",
            },

            "paths": {},
        }

        for operation in operations:

            method = operation.method.lower()

            if operation.path not in document["paths"]:
                document["paths"][operation.path] = {}

            operation_object = {
                "operationId": operation.operation_id,
                "responses": {},
            }

            # Path parameters
            parameter_names = re.findall(
                r"\{([^}]+)\}",
                operation.path,
            )

            if parameter_names:

                operation_object["parameters"] = []

                for parameter_name in parameter_names:

                    operation_object["parameters"].append(
                        {
                            "name": parameter_name,
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "format": "uuid",
                            },
                        }
                    )

            # Request body
            if operation.request_schema:

                operation_object["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": self._to_json_schema(
                                operation.request_schema
                            )
                        }
                    },
                }

            success_code = (
                "201"
                if operation.operation_id.startswith("create")
                else "200"
            )

            operation_object["responses"][success_code] = {
                "description": "Successful operation",
                "content": {
                    "application/json": {
                        "schema": self._to_json_schema(
                            operation.response_schema
                        )
                    }
                },
            }

            for (
                status_code,
                description,
            ) in operation.error_responses.items():

                operation_object["responses"][
                    str(status_code)
                ] = {
                    "description": description
                }

            document["paths"][operation.path][
                method
            ] = operation_object

        return document

    def _to_json_schema(
        self,
        fields: dict,
    ) -> dict:

        properties = {}

        for field_name, field_type in fields.items():

            properties[field_name] = (
                self._convert_type(field_type)
            )

        return {
            "type": "object",
            "properties": properties,
        }

    def _convert_type(
        self,
        value,
    ) -> dict:

        if value == "uuid":
            return {
                "type": "string",
                "format": "uuid",
            }

        if value == "string":
            return {
                "type": "string"
            }

        # Values such as BOOKED / CANCELLED
        if isinstance(value, str):
            return {
                "type": "string"
            }

        return {
            "type": "object"
        }