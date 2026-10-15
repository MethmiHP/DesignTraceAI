"""
DesignTrace AI - Requirement Mapping Evaluation

Compare generated requirement-to-database mappings
with manually prepared gold mappings.
"""

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

GENERATED_DIR = BASE_DIR / "baseline_results"
GOLD_DIR = BASE_DIR / "gold_mappings"

PROJECTS = ["hospital", "library", "ecommerce", "student",]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def extract_links(report):
    links = set()

    for mapping in report["requirement_mappings"]:
        requirement_id = mapping["requirement_id"]

        for element in mapping["database_elements"]:
            links.add((requirement_id, element))

    return links


def evaluate_project(project_name):
    generated_path = (
        GENERATED_DIR
        / project_name
        / "requirement_mapping.json"
    )

    gold_path = GOLD_DIR / f"{project_name}.json"

    generated = load_json(generated_path)
    gold = load_json(gold_path)

    generated_links = extract_links(generated)
    gold_links = extract_links(gold)

    correct = generated_links & gold_links
    incorrect = generated_links - gold_links
    missing = gold_links - generated_links

    precision = (
        len(correct) / len(generated_links)
        if generated_links else 0.0
    )

    recall = (
        len(correct) / len(gold_links)
        if gold_links else 0.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    print(f"\n{project_name.upper()} Mapping Evaluation")
    print("-" * 40)

    print("Correct links:", len(correct))
    print("Incorrect links:", len(incorrect))
    print("Missing links:", len(missing))
    print(f"Precision: {precision:.3f}")
    print(f"Recall: {recall:.3f}")
    print(f"F1-score: {f1:.3f}")

    print("\nIncorrect generated links:")
    for link in sorted(incorrect):
        print(link)

    print("\nMissing expected links:")
    for link in sorted(missing):
        print(link)

    return {
        "project": project_name,
        "correct_links": len(correct),
        "incorrect_links": len(incorrect),
        "missing_links": len(missing),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
    }


def main():
    results = []

    for project_name in PROJECTS:
        results.append(evaluate_project(project_name))

    output_path = BASE_DIR / "mapping_evaluation_results.json"

    output_path.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print("\nEvaluation completed.")
    print("Results saved to:", output_path)


if __name__ == "__main__":
    main()
