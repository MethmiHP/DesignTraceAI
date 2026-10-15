from .schemas import QualityEvaluationRequest


class QualityInputPreprocessor:

    def normalize(
        self,
        request: QualityEvaluationRequest,
    ) -> QualityEvaluationRequest:

        normalized = request.model_copy(
            deep=True
        )

        normalized.project_id = (
            normalized.project_id.strip()
        )

        for requirement in (
            normalized.functional_requirements
        ):
            requirement.requirement_id = (
                requirement.requirement_id.strip()
            )

            requirement.statement = (
                requirement.statement.strip()
            )

        for requirement in (
            normalized.non_functional_requirements
        ):
            requirement.requirement_id = (
                requirement.requirement_id.strip()
            )

            requirement.statement = (
                requirement.statement.strip()
            )

        for element in (
            normalized.architecture.elements
        ):
            element.element_id = (
                element.element_id.strip()
            )

            element.name = (
                element.name.strip()
            )

            element.type = (
                element.type.strip()
            )

            element.main_responsibility = (
                element.main_responsibility.strip()
            )

        for entity in normalized.database.entities:
            entity.name = entity.name.strip()

            entity.attributes = [
                attribute.strip()
                for attribute in entity.attributes
            ]

            entity.foreign_keys = [
                foreign_key.strip()
                for foreign_key
                in entity.foreign_keys
            ]

        for operation in (
            normalized
            .api_component_design
            .api_operations
        ):
            operation.operation_id = (
                operation.operation_id.strip()
            )

            operation.method = (
                operation.method.strip().upper()
            )

            operation.path = (
                operation.path.strip()
            )

        return normalized