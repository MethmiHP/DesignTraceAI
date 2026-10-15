import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    BASE_DIR / "datasets" / "llm" / "evaluation_cases.json"
)

def main():
    print("DesignTrace AI - LLM Dataset Validation")
    print("--------------------------------------")

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    if not isinstance(cases, list) or not cases:
        raise ValueError("Dataset must be a non-empty list.")

    required_fields = {
        "case_id",
        "project_id",
        "domain",
        "difficulty",
        "requirements",
    }

    errors = []
    seen_ids = set()

    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            errors.append(f"Case {index}: must be an object")
            continue

        case_id = case.get("case_id", f"Case {index}")

        missing = required_fields - set(case)
        if missing:
            errors.append(f"{case_id}: missing {sorted(missing)}")

        if case_id in seen_ids:
            errors.append(f"{case_id}: duplicate case ID")
        seen_ids.add(case_id)

        requirements = case.get("requirements")

        if not isinstance(requirements, list) or not requirements:
            errors.append(f"{case_id}: requirements must be a non-empty list")
            continue

        requirement_ids = set()

        for requirement in requirements:
            if not isinstance(requirement, dict):
                errors.append(f"{case_id}: invalid requirement object")
                continue

            req_id = requirement.get("requirement_id")
            text = requirement.get("text")

            if not isinstance(req_id, str) or not req_id.strip():
                errors.append(f"{case_id}: missing requirement_id")
            elif req_id in requirement_ids:
                errors.append(f"{case_id}: duplicate requirement {req_id}")

            requirement_ids.add(req_id)

            if not isinstance(text, str) or not text.strip():
                errors.append(f"{case_id}: empty requirement text")

    print("Total evaluation cases:", len(cases))
    print("Total issues:", len(errors))

    if errors:
        print("\nValidation issues:")
        for error in errors:
            print("-", error)
        raise SystemExit(1)

    print("\nBasic dataset structure is valid!")
    print("Ready for detailed gold-design review.")

if __name__ == "__main__":
    main()
