# Tests the configured Gemini LLM connection by creating the provider,
# sending a simple text-generation request, and confirming that a valid
# response is returned successfully from the Gemini API.

import asyncio

from shared.llm.factory import get_llm_provider


async def main():

    print("1. Creating Gemini client...")

    llm = get_llm_provider()

    print("2. Gemini client created.")

    print("3. Sending request to Gemini...")

    result = await llm.generate(
        "Reply only with: Gemini connection works."
    )

    print("4. Response received.")

    print(result)


if __name__ == "__main__":
    asyncio.run(main())