import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

prompt = """
You are a software database designer.

Generate a relational database schema for
the following requirement:

FR-001: The system shall allow patients
to book appointments with doctors.

Return ONLY valid JSON with these keys:
- entities
- relationships

Each entity must include:
- name
- attributes
- primary_key
- foreign_keys

Do not include markdown formatting.
"""

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "system",
            "content": "You generate relational database designs."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0
)

content = response.choices[0].message.content

print("\nGROQ RESPONSE:\n")
print(content)

try:
    schema = json.loads(content)
    print("\nSUCCESS: Valid JSON returned.")
except json.JSONDecodeError:
    print("\nWARNING: Response is not valid JSON.")