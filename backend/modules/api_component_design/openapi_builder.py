#This converts API operations into an OpenAPI document.

import re

from .schemas import APIOperation
from .security import security_scheme


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

            scheme = security_scheme(operation.security)
            if scheme:
                name, definition = scheme
                document.setdefault("components", {}).setdefault("securitySchemes", {})[name] = definition
                operation_object["security"] = [{name: []}]
            elif operation.security.authentication == "none":
                operation_object["security"] = []
            if operation.security.roles:
                operation_object["x-required-roles"] = operation.security.roles
            if operation.security.access_rules:
                operation_object["x-access-rules"] = operation.security.access_rules

            # Preserve explicit query/header/path metadata from generation.
            parameters = [
                {
                    "name": parameter.name,
                    "in": parameter.location,
                    "required": True if parameter.location == "path" else parameter.required,
                    "description": parameter.description,
                    "schema": self._convert_type(parameter.type),
                }
                for parameter in operation.parameters
                if not (parameter.location == "header" and parameter.name.lower()
                        in {"content-type", "accept", "authorization"})
            ]
            declared_paths = {item["name"] for item in parameters if item["in"] == "path"}
            for name in dict.fromkeys(re.findall(r"\{([^}]+)\}", operation.path)):
                if name not in declared_paths:
                    parameters.append({
                        "name": name,
                        "in": "path",
                        "required": True,
                        "description": f"Identifier for {name.removesuffix('_id').replace('_', ' ')}.",
                        "schema": {"type": "string", "format": "uuid"},
                    })
            if parameters:
                operation_object["parameters"] = parameters

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

        if isinstance(value, str) and value in {"integer", "number", "boolean"}:
            return {"type": value}

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