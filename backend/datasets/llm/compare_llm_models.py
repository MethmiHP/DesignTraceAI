import os
import json
import csv
import time
from pathlib import Path

from openai import OpenAI
from google import genai
from dotenv import load_dotenv

load_dotenv()

# API clients
groq = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

gemini = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

OUTPUT = PROJECT_ROOT / "outputs" / "llm_comparison"
OUTPUT.mkdir(parents=True, exist_ok=True)

# Same requirements for both models
TEST_CASES = {
    "hospital": "Patients can book appointments with doctors. Each appointment has a date, time and status.",
    "library": "Members can borrow books. Each borrowing records the member, book, borrow date and return date.",
    "ecommerce": "Customers place orders containing products. Each order has a date, total and payment status.",
    "university": "Students enroll in courses. Each enrollment records the student, course, semester and grade.",
    "hotel": "Guests reserve rooms. Each reservation has check-in date, check-out date and booking status."
}

PROMPT = """
You are a relational database designer.

Generate a database design from these requirements:

{requirements}

Return ONLY JSON with this structure:

{{
  "entities": [
    {{
      "name": "EntityName",
      "attributes": [
        {{
          "name": "attribute_name",
          "data_type": "VARCHAR(100)"
        }}
      ],
      "primary_key": "id",
      "foreign_keys": []
    }}
  ],
  "relationships": []
}}

Include suitable entities, attributes, primary keys,
foreign keys and relationships.

Do not include markdown.
"""

def extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text.strip())

def call_groq(prompt):
    response = groq.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

def call_gemini(prompt):
    for attempt in range(3):
        try:
            response = gemini.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config={"temperature": 0}
            )
            return response.text

        except Exception as e:
            if "503" in str(e) and attempt < 2:
                wait = 5 * (attempt + 1)
                print(f"Gemini busy. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    response = gemini.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={"temperature": 0}
    )
    return response.text

results = []

for case_name, requirements in TEST_CASES.items():
    prompt = PROMPT.format(requirements=requirements)

    for model_name, function in [
        ("gemini", call_gemini),
        ("gpt_oss_20b", call_groq)
    ]:
        print(f"Testing {model_name}: {case_name}")

        start = time.perf_counter()
        valid_json = False
        entity_count = 0
        has_entities = False
        has_relationships = False
        error = ""

        try:
            raw = function(prompt)
            schema = extract_json(raw)

            valid_json = isinstance(schema, dict)
            if valid_json:
                entities = schema.get("entities", [])
                relationships = schema.get("relationships", [])

                has_entities = isinstance(entities, list) and len(entities) > 0
                has_relationships = isinstance(relationships, list)
                entity_count = len(entities) if isinstance(entities, list) else 0

            filename = OUTPUT / f"{case_name}_{model_name}.json"
            filename.write_text(
                json.dumps(schema, indent=2),
                encoding="utf-8"
            )

        except Exception as exc:
            error = str(exc)
            print("ERROR:", error)

        elapsed = round(time.perf_counter() - start, 2)

        results.append({
            "case": case_name,
            "model": model_name,
            "valid_json": valid_json,
            "has_entities": has_entities,
            "has_relationships_field": has_relationships,
            "entity_count": entity_count,
            "latency_seconds": elapsed,
            "error": error
        })

        print(
            f"  JSON={valid_json}, "
            f"Entities={entity_count}, "
            f"Time={elapsed}s"
        )

csv_file = OUTPUT / "comparison_results.csv"

with csv_file.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=results[0].keys()
    )
    writer.writeheader()
    writer.writerows(results)

print("\nCOMPARISON COMPLETED")
print("Results saved to:", csv_file)
