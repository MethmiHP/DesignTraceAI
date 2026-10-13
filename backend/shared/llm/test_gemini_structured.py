# Tests the configured LLM provider's structured-output capability by sending
# a sample requirement and requesting a schema-constrained JSON response.
# This verifies that the provider connection and generate_structured() method
# work correctly before using them in the full Requirement Analysis pipeline.

import asyncio

from shared.llm.factory import get_llm_provider


async def main():

    llm = get_llm_provider()

    print("Sending structured request...")

    result = await llm.generate_structured(
        prompt=(
            "Analyze this requirement: "
            "'The system shall respond within 2 seconds.' "
            "Return whether it is FR or NFR."
        ),

        response_schema={
            "type": "object",
            "properties": {
                "requirement_type": {
                    "type": "string"
                }
            },
            "required": [
                "requirement_type"
            ]
        },

        temperature=0.0
    )

    print("Structured response received:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())