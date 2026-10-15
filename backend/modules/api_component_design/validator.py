import re
from .security import validate_security


from .schemas import (
    APIComponentDesignRequest,
    APIOperation,
    ResponsibilityDesign,
)


from shared.models.common import (
    ValidationIssue,
    ValidationResult,
)


class APIDesignValidator:

    
    # SUPPORTED HTTP METHODS


    ALLOWED_METHODS = {
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    }


    # PUBLIC VALIDATION METHOD
   

    def validate(
        self,
        request: APIComponentDesignRequest,
        responsibilities: list[
            ResponsibilityDesign
        ],
        operations: list[
            APIOperation
        ],
    ) -> ValidationResult:

        issues: list[
            ValidationIssue
        ] = []


        # KNOWN REQUIREMENTS
       

        requirement_ids = {
            requirement.requirement_id
            for requirement
            in request.functional_requirements
        }


   
        # KNOWN ARCHITECTURE ELEMENTS
        

        architecture_ids = {
            element.element_id
            for element
            in request.architecture.elements
        }


        # DATABASE GROUNDING CONTEXT
       

        database_attributes = set()

        database_primary_keys = set()


        for entity in (
            request.database.entities
        ):

            database_attributes.update(
                entity.attributes
            )

            if entity.primary_key:

                database_primary_keys.add(
                    entity.primary_key
                )


       
        # DUPLICATE TRACKING
       

        operation_ids = set()

        method_paths = set()


       
        # VALIDATE RESPONSIBILITY MAPPINGS
     

        self._validate_responsibilities(
            responsibilities=responsibilities,

            requirement_ids=(
                requirement_ids
            ),

            architecture_ids=(
                architecture_ids
            ),

            issues=issues,
        )


      
        # VALIDATE API OPERATIONS
      

        for operation in operations:
            self._validate_parameters(operation, database_attributes, issues)
            validate_security(request, operation, issues)

         
            # 1. HTTP METHOD
          

            if (
                operation.method.upper()
                not in self.ALLOWED_METHODS
            ):

                issues.append(
                    ValidationIssue(
                        code=(
                            "INVALID_HTTP_METHOD"
                        ),

                        message=(
                            f"{operation.operation_id} "
                            "has an unsupported "
                            f"HTTP method: "
                            f"{operation.method}."
                        ),

                        severity="ERROR",
                    )
                )


            
            # 2. REQUIREMENT TRACEABILITY
          

            if (
                operation.requirement_id
                not in requirement_ids
            ):

                issues.append(
                    ValidationIssue(
                        code=(
                            "UNKNOWN_REQUIREMENT"
                        ),

                        message=(
                            f"{operation.operation_id} "
                            "references an unknown "
                            "requirement "
                            f"{operation.requirement_id}."
                        ),

                        severity="ERROR",
                    )
                )


        
            # 3. ARCHITECTURE TRACEABILITY
       

            if (
                operation.element_id
                not in architecture_ids
            ):

                issues.append(
                    ValidationIssue(
                        code=(
                            "UNKNOWN_ARCHITECTURE_ELEMENT"
                        ),

                        message=(
                            f"{operation.operation_id} "
                            "references an unknown "
                            "architecture element "
                            f"{operation.element_id}."
                        ),

                        severity="ERROR",
                    )
                )


          
            # 4. OPERATION ID FORMAT
        

            if not self._is_camel_case(
                operation.operation_id
            ):

                issues.append(
                    ValidationIssue(
                        code=(
                            "INVALID_OPERATION_ID_FORMAT"
                        ),

                        message=(
                            f"{operation.operation_id} "
                            "should use camelCase."
                        ),

                        severity="WARNING",
                    )
                )


          
            # 5. DUPLICATE OPERATION ID
         

            if (
                operation.operation_id
                in operation_ids
            ):

                issues.append(
                    ValidationIssue(
                        code=(
                            "DUPLICATE_OPERATION_ID"
                        ),

                        message=(
                            "Duplicate operation ID: "
                            f"{operation.operation_id}"
                        ),

                        severity="ERROR",
                    )
                )


            operation_ids.add(
                operation.operation_id
            )


            
            # 6. DUPLICATE METHOD + PATH
         

            key = (
                operation.method.upper(),
                operation.path,
            )


            if key in method_paths:

                issues.append(
                    ValidationIssue(
                        code=(
                            "DUPLICATE_ENDPOINT"
                        ),

                        message=(
                            "Duplicate endpoint: "
                            f"{operation.method} "
                            f"{operation.path}"
                        ),

                        severity="ERROR",
                    )
                )


            method_paths.add(
                key
            )


          
            # 7. PATH VALIDATION
          

            self._validate_path(
                operation=operation,

                database_attributes=(
                    database_attributes
                ),

                database_primary_keys=(
                    database_primary_keys
                ),

                issues=issues,
            )


            
            # 8. REQUEST FIELD DATABASE GROUNDING
   

            self._validate_request_fields(
                operation=operation,

                database_attributes=(
                    database_attributes
                ),

                issues=issues,
            )


         
            # 9. RESPONSE FIELD DATABASE GROUNDING
            

            self._validate_response_fields(
                operation=operation,

                database_attributes=(
                    database_attributes
                ),

                issues=issues,
            )


            
            # 10. ERROR RESPONSE VALIDATION
     

            self._validate_error_responses(
                operation=operation,
                issues=issues,
            )



        # FINAL RESULT
   

        has_errors = any(
            issue.severity == "ERROR"
            for issue in issues
        )


        return ValidationResult(
            valid=not has_errors,
            issues=issues,
        )


    
    # RESPONSIBILITY VALIDATION
   

    @staticmethod
    def _validate_responsibilities(
        responsibilities,
        requirement_ids,
        architecture_ids,
        issues,
    ):

        seen_requirements = set()


        for responsibility in responsibilities:

            
            # Known requirement
           

            if (
                responsibility.requirement_id
                not in requirement_ids
            ):

                issues.append(
                    ValidationIssue(
                        code=(
                            "RESPONSIBILITY_UNKNOWN_REQUIREMENT"
                        ),

                        message=(
                            "Responsibility references "
                            "unknown requirement "
                            f"{responsibility.requirement_id}."
                        ),

                        severity="ERROR",
                    )
                )


          
            # Known architecture element
   

            if (
                responsibility.element_id
                not in architecture_ids
            ):

                issues.append(
                    ValidationIssue(
                        code=(
                            "RESPONSIBILITY_UNKNOWN_ELEMENT"
                        ),

                        message=(
                            "Responsibility references "
                            "unknown architecture element "
                            f"{responsibility.element_id}."
                        ),

                        severity="ERROR",
                    )
                )


           
            # Duplicate requirement responsibility
            

            key = (
                responsibility.requirement_id,
                responsibility.element_id,
            )


            if key in seen_requirements:

                issues.append(
                    ValidationIssue(
                        code=(
                            "DUPLICATE_RESPONSIBILITY"
                        ),

                        message=(
                            "Duplicate responsibility "
                            "mapping for requirement "
                            f"{responsibility.requirement_id} "
                            "and architecture element "
                            f"{responsibility.element_id}."
                        ),

                        severity="WARNING",
                    )
                )


            seen_requirements.add(
                key
            )


    
    # PATH VALIDATION
  

    def _validate_path(
        self,
        operation: APIOperation,
        database_attributes: set[str],
        database_primary_keys: set[str],
        issues: list[ValidationIssue],
    ):

        path = operation.path


        
        # Must start with /
     

        if not path.startswith("/"):

            issues.append(
                ValidationIssue(
                    code="INVALID_PATH",

                    message=(
                        f"{operation.operation_id} "
                        "path must start with '/'."
                    ),

                    severity="ERROR",
                )
            )

            return


      
        # No whitespace
  

        if re.search(
            r"\s",
            path,
        ):

            issues.append(
                ValidationIssue(
                    code=(
                        "PATH_CONTAINS_WHITESPACE"
                    ),

                    message=(
                        f"{operation.operation_id} "
                        "path contains whitespace."
                    ),

                    severity="ERROR",
                )
            )


      
        # Extract path parameters
        #
        # Example:
        # /appointments/{appointment_id}


        path_parameters = re.findall(
            r"\{([^{}]+)\}",
            path,
        )


        
        # Check brace structure
     

        if (
            path.count("{")
            != path.count("}")
        ):

            issues.append(
                ValidationIssue(
                    code=(
                        "INVALID_PATH_PARAMETER_SYNTAX"
                    ),

                    message=(
                        f"{operation.operation_id} "
                        "contains malformed path "
                        "parameter syntax."
                    ),

                    severity="ERROR",
                )
            )


       
        # Validate literal path segments
        # are lowercase REST-style segments.
       

        literal_path = re.sub(
            r"\{[^{}]+\}",
            "",
            path,
        )


        if (
            literal_path
            != literal_path.lower()
        ):

            issues.append(
                ValidationIssue(
                    code=(
                        "NON_LOWERCASE_PATH"
                    ),

                    message=(
                        f"{operation.operation_id} "
                        "uses uppercase characters "
                        "in its API path."
                    ),

                    severity="WARNING",
                )
            )


      
        # Path parameter DB grounding
      

        for parameter in path_parameters:

            if (
                parameter
                not in database_attributes
            ):

                issues.append(
                    ValidationIssue(
                        code=(
                            "UNGROUNDED_PATH_PARAMETER"
                        ),

                        message=(
                            f"{operation.operation_id} "
                            "uses path parameter "
                            f"'{parameter}' which does "
                            "not exist in the supplied "
                            "database attributes."
                        ),

                        severity="ERROR",
                    )
                )

                continue


           
            # Resource path identifiers should usually
            # use a database primary key.
      

            if (
                parameter
                not in database_primary_keys
            ):

                issues.append(
                    ValidationIssue(
                        code=(
                            "NON_PRIMARY_KEY_PATH_PARAMETER"
                        ),

                        message=(
                            f"{operation.operation_id} "
                            "uses '{parameter}' as a "
                            "path parameter, but it is "
                            "not a supplied database "
                            "primary key."
                        ),

                        severity="WARNING",
                    )
                )


   
    # REQUEST FIELD GROUNDING


    def _validate_request_fields(
        self,
        operation: APIOperation,
        database_attributes: set[str],
        issues: list[ValidationIssue],
    ):

        for field_name in (
            operation.request_schema.keys()
        ):

            if self._is_database_grounded_field(
                field_name,
                database_attributes,
            ):

                continue


            issues.append(
                ValidationIssue(
                    code=(
                        "UNGROUNDED_REQUEST_FIELD"
                    ),

                    message=(
                        f"{operation.operation_id} "
                        "uses request field "
                        f"'{field_name}' which cannot "
                        "be directly grounded in the "
                        "supplied database context."
                    ),

                    # Warning for now because some
                    # legitimate API command fields,
                    # such as "reason", may not be
                    # persisted directly.
                    severity="WARNING",
                )
            )


    
    # RESPONSE FIELD GROUNDING
   

    def _validate_response_fields(
        self,
        operation: APIOperation,
        database_attributes: set[str],
        issues: list[ValidationIssue],
    ):

        allowed_operation_fields = {
            "message",
            "success",
            "result",
        }


        for field_name in (
            operation.response_schema.keys()
        ):

            if (
                field_name
                in database_attributes
            ):

                continue


            if (
                field_name
                in allowed_operation_fields
            ):

                continue


            issues.append(
                ValidationIssue(
                    code=(
                        "UNGROUNDED_RESPONSE_FIELD"
                    ),

                    message=(
                        f"{operation.operation_id} "
                        "uses response field "
                        f"'{field_name}' which cannot "
                        "be grounded in the supplied "
                        "database context."
                    ),

                    severity="WARNING",
                )
            )


    
    # ERROR RESPONSE VALIDATION
    

    @staticmethod
    def _validate_error_responses(
        operation: APIOperation,
        issues: list[ValidationIssue],
    ):

        for status_code in (
            operation.error_responses.keys()
        ):

           
            # Must be a three-digit HTTP status
       

            if not re.fullmatch(
                r"\d{3}",
                str(status_code),
            ):

                issues.append(
                    ValidationIssue(
                        code=(
                            "INVALID_ERROR_STATUS_CODE"
                        ),

                        message=(
                            f"{operation.operation_id} "
                            "contains invalid HTTP "
                            "error status code "
                            f"'{status_code}'."
                        ),

                        severity="ERROR",
                    )
                )

                continue


            numeric_code = int(
                status_code
            )


            
            # error_responses should normally use
            # HTTP 4xx or 5xx codes.
         

            if not (
                400
                <= numeric_code
                <= 599
            ):

                issues.append(
                    ValidationIssue(
                        code=(
                            "NON_ERROR_STATUS_CODE"
                        ),

                        message=(
                            f"{operation.operation_id} "
                            "uses HTTP status "
                            f"{status_code} inside "
                            "error_responses."
                        ),

                        severity="WARNING",
                    )
                )


   
    # DATABASE FIELD GROUNDING HELPER
    

    @staticmethod
    def _is_database_grounded_field(
        field_name: str,
        database_attributes: set[str],
    ) -> bool:

     
        # Exact DB attribute
    

        if (
            field_name
            in database_attributes
        ):

            return True


       

        derived_prefixes = (
            "new_",
            "updated_",
            "selected_",
            "target_",
        )


        for prefix in derived_prefixes:

            if field_name.startswith(
                prefix
            ):

                base_field = (
                    field_name[
                        len(prefix):
                    ]
                )


                if (
                    base_field
                    in database_attributes
                ):

                    return True


        return False



    # CAMEL CASE HELPER


    @staticmethod
    def _is_camel_case(
        value: str,
    ) -> bool:

        return bool(
            re.fullmatch(
                r"[a-z][A-Za-z0-9]*",
                value,
            )
        )

    @staticmethod
    def _validate_parameters(operation, database_attributes, issues):
        placeholders = set(re.findall(r"\{([^}]+)\}", operation.path))
        seen = set()
        for parameter in operation.parameters:
            name = parameter.name.lower() if parameter.location == "header" else parameter.name
            key = (parameter.location, name)
            code = None
            message = None
            if key in seen:
                code = "DUPLICATE_PARAMETER"
                message = f"Duplicate {parameter.location} parameter: {parameter.name}."
            elif parameter.location == "path" and (
                parameter.name not in placeholders or not parameter.required
            ):
                code = "INVALID_PATH_PARAMETER"
                message = f"Path parameter {parameter.name} must match a path placeholder and be required."
            elif parameter.location == "query" and parameter.name not in database_attributes:
                code = "UNGROUNDED_QUERY_PARAMETER"
                message = f"Query parameter {parameter.name} is not grounded in the supplied database attributes."
            elif parameter.location == "header" and name in {"content-type", "accept", "authorization"}:
                code = "RESERVED_HEADER_PARAMETER"
                message = f"Header {parameter.name} must be represented using OpenAPI content or security definitions."
            seen.add(key)
            if code:
                issues.append(ValidationIssue(
                    code=code,
                    message=f"{operation.operation_id}: {message}",
                    severity="ERROR",
                ))
