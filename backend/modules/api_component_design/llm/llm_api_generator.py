from .provider import BaseLLMProvider

from .structured_schemas import (
    LLMAPIOperation,
)

from ..schemas import (
    APIOperation,
    DatabaseEntity,
    SemanticExtraction,
)


class LLMAPIGenerator:

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
    ):
        self.llm_provider = llm_provider


  
    # PUBLIC GENERATION METHOD
  

    def generate(
        self,
        requirement_statement: str,
        semantic: SemanticExtraction,
        architecture_element,
        database_context: list[DatabaseEntity],
    ) -> APIOperation:

        prompt = self._build_prompt(
            requirement_statement=requirement_statement,
            semantic=semantic,
            architecture_element=architecture_element,
            database_context=database_context,
        )


      
        # LLM OUTPUT
        #
        # Gemini returns the list-based intermediate
        # representation because arbitrary dictionaries
        # are not supported by Gemini Developer API
        # structured output.


        llm_operation = (
            self.llm_provider.generate_structured(
                prompt,
                LLMAPIOperation,
            )
        )


      
        # CONVERT LLM STRUCTURE
        # INTO INTERNAL APIOperation
       

        operation = APIOperation(
            parameters=llm_operation.parameters,
            operation_id=(
                llm_operation.operation_id
            ),

            requirement_id=(
                llm_operation.requirement_id
            ),

            element_id=(
                llm_operation.element_id
            ),

            method=(
                llm_operation.method
            ),

            path=(
                llm_operation.path
            ),

            request_schema={
                field.name: field.type
                for field
                in llm_operation.request_fields
            },

            response_schema={
                field.name: field.type
                for field
                in llm_operation.response_fields
            },

            error_responses={
                error.status_code: error.message
                for error
                in llm_operation.errors
            },
        )


        return operation


   
    # PROMPT CONSTRUCTION
  

    def _build_prompt(
        self,
        requirement_statement: str,
        semantic: SemanticExtraction,
        architecture_element,
        database_context: list[DatabaseEntity],
    ) -> str:

        database_text = (
            self._format_database_context(
                database_context
            )
        )


        prompt = f"""
You are an API design assistant for DesignTrace AI.

Your task is to generate ONE REST API operation for the
given functional requirement.

You must use ONLY the supplied functional requirement,
semantic understanding, architecture context, and
database context.

Do not invent database entities, attributes, primary keys,
foreign keys, architecture components, or requirements
that are not provided.

Return an API operation using the required structured
format.

Represent request fields as a list where every item
contains:

- name
- type

Represent response fields as a list where every item
contains:

- name
- type

Represent errors as a list where every item contains:

- status_code
- message

Do not return request_schema, response_schema, or
error_responses as arbitrary JSON dictionaries.


FUNCTIONAL REQUIREMENT
----------------------

Requirement ID:
{semantic.requirement_id}

Statement:
{requirement_statement}


SEMANTIC UNDERSTANDING
----------------------

Actor:
{semantic.actor}

Action:
{semantic.action}

Resource:
{semantic.resource}


ARCHITECTURE CONTEXT
--------------------

Element ID:
{architecture_element.element_id}

Element Name:
{architecture_element.name}

Element Type:
{architecture_element.type}

Main Responsibility:
{architecture_element.main_responsibility}


DATABASE CONTEXT
----------------

{database_text}


API DESIGN RULES
----------------

1. Generate exactly ONE REST API operation.

2. Use REST-style resource-oriented paths.

3. Use lowercase plural resource names in paths.

Examples:

Appointment
-> /appointments

Medical Certificate
-> /medical-certificates


4. Select the HTTP method according to the functional
requirement semantics.

Typical mappings:

create / add / register / book / issue
-> POST

view / get / retrieve / read
-> GET

update / modify / edit / reschedule
-> PATCH

delete / remove
-> DELETE


5. Domain actions such as:

approve
reject
cancel
confirm

may use an action-oriented resource endpoint such as:

POST /resources/{{resource_id}}/approve


6. Use the supplied database primary key as the resource
path parameter when appropriate.

Example:

/medical-certificates/{{medical_certificate_id}}


7. Request fields must be grounded in supplied database
attributes.

Do not invent request fields.


8. Response fields must be grounded in supplied database
attributes or represent a valid operation state.

Examples of valid state values include:

BOOKED
CANCELLED
APPROVED
REJECTED
ISSUED


9. Do not include generated primary keys in a create
request body unless the functional requirement explicitly
requires them.


10. Include only HTTP error responses that make sense for
the operation.

Possible errors include:

400 - Invalid request
401 - Authentication required
403 - Operation not permitted
404 - Resource not found
409 - State or data conflict
422 - Business rule violation


11. operation_id must use camelCase.

Examples:

createAppointment
cancelAppointment
issueMedicalCertificate
updatePatientProfile


12. requirement_id MUST be exactly:

{semantic.requirement_id}


13. element_id MUST be exactly:

{architecture_element.element_id}


14. Do not generate OpenAPI directly.


15. Use request_fields and response_fields as arrays of
objects containing:

"name"
"type"


16. Use errors as an array of objects containing:

"status_code"
"message"


17. Include parameters as an array with name, location (path, query,
or header), type (string, uuid, integer, number, boolean), required,
and description. Keep request_fields for JSON body fields only.
Use query parameters for filters explicitly requested in the requirement;
ground filter names in the supplied database attributes. Do not invent
pagination or filters. Path parameters must exactly match placeholders
in the path and must be required. Only include custom headers when
explicitly required. Do not include Content-Type, Accept, or Authorization
as parameter headers; JSON content types are defined by the request body
and responses. Do not infer an authentication scheme from error codes.
Leave parameters empty when the operation needs none.

18. Do not return markdown or explanatory text.

Return only the structured API operation required by the
schema.
"""


        return prompt.strip()


   
    # DATABASE CONTEXT FORMATTING
   

    @staticmethod
    def _format_database_context(
        database_context: list[DatabaseEntity],
    ) -> str:

        if not database_context:

            return (
                "No relevant database entities were "
                "provided."
            )


        sections = []


        for entity in database_context:

            attributes = (
                ", ".join(
                    entity.attributes
                )
                if entity.attributes
                else "None"
            )


            foreign_keys = (
                ", ".join(
                    entity.foreign_keys
                )
                if entity.foreign_keys
                else "None"
            )


            constraints = (
                ", ".join(
                    entity.constraints
                )
                if entity.constraints
                else "None"
            )


            section = f"""
Entity:
{entity.name}

Attributes:
{attributes}

Primary Key:
{entity.primary_key or "None"}

Foreign Keys:
{foreign_keys}

Constraints:
{constraints}
""".strip()


            sections.append(
                section
            )


        return "\n\n".join(
            sections
        )
