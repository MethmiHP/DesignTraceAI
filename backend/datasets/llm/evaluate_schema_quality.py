import csv
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

CASES_PATH = BASE_DIR / "datasets" / "llm" / "evaluation_cases.json"
GENERATED_DIR = BASE_DIR / "outputs" / "llm_evaluation" / "generated_designs"
OUTPUT_DIR = BASE_DIR / "outputs" / "llm_evaluation"

METRICS = [
    "entities",
    "attributes",
    "primary_keys",
    "foreign_keys",
    "relationships",
    "requirement_mapping",
]

# Human-reviewed equivalences only.
# Format: case_id -> generated table name -> expected table name.
APPROVED_ALIASES = {
    "LLM-002": {
        "borrow_records": "loans",
    },
    "LLM-009": {
        "event_registrations": "registrations",
    },
}


def normalize(value):
    """Normalize formatting without guessing semantic meaning."""
    value = str(value).strip().lower()
    value = re.sub(r"[\s\-]+", "_", value)
    return value


def normalize_cardinality(value):
    value = normalize(value)

    aliases = {
        "1:n": "one_to_many",
        "1:m": "one_to_many",
        "one_to_many": "one_to_many",
        "many_to_one": "many_to_one",
        "1:1": "one_to_one",
        "one_to_one": "one_to_one",
        "m:n": "many_to_many",
        "many_to_many": "many_to_many",
    }

    return aliases.get(value, value)


def canonical_table(name, aliases=None):
    """Convert a generated table name to its approved expected name."""
    name = normalize(name)

    if aliases is None:
        return name

    return aliases.get(name, name)


def parse_reference(reference):
    """Convert 'patients.patient_id' to (table, column)."""
    parts = str(reference).rsplit(".", 1)

    if len(parts) != 2:
        raise ValueError(
            f"Invalid foreign key reference: {reference}"
        )

    return normalize(parts[0]), normalize(parts[1])


def expected_features(expected):
    """Extract comparable features from the human-reviewed gold design."""
    result = {name: set() for name in METRICS}

    result["entities"] = {
        normalize(name)
        for name in expected.get("entities", [])
    }

    for table, columns in expected.get("attributes", {}).items():
        for column in columns:
            result["attributes"].add((
                normalize(table),
                normalize(column),
            ))

    for table, columns in expected.get("primary_keys", {}).items():
        if isinstance(columns, str):
            columns = [columns]

        for column in columns:
            result["primary_keys"].add((
                normalize(table),
                normalize(column),
            ))

    for fk in expected.get("foreign_keys", []):
        target_table, target_column = parse_reference(
            fk["references"]
        )

        result["foreign_keys"].add((
            normalize(fk["table"]),
            normalize(fk["column"]),
            target_table,
            target_column,
        ))

    for relationship in expected.get("relationships", []):
        result["relationships"].add((
            normalize(relationship["from"]),
            normalize(relationship["to"]),
            normalize_cardinality(
                relationship["cardinality"]
            ),
        ))

    for requirement_id, tables in expected.get(
        "requirement_mapping", {}
    ).items():
        for table in tables:
            result["requirement_mapping"].add((
                normalize(requirement_id),
                normalize(table),
            ))

    return result


def generated_features(design, aliases=None):
    """Extract features, optionally applying reviewed table aliases."""
    result = {name: set() for name in METRICS}

    for table in design.get("tables", []):
        table_name = canonical_table(
            table["table_name"], aliases
        )

        result["entities"].add(table_name)

        for column in table.get("columns", []):
            column_name = normalize(column["name"])

            result["attributes"].add((
                table_name,
                column_name,
            ))

            if column.get("primary_key", False):
                result["primary_keys"].add((
                    table_name,
                    column_name,
                ))

            fk = column.get("foreign_key")

            if isinstance(fk, dict):
                result["foreign_keys"].add((
                    table_name,
                    column_name,
                    canonical_table(fk["table"], aliases),
                    normalize(fk["column"]),
                ))

        for requirement_id in table.get(
            "source_requirement_ids", []
        ):
            result["requirement_mapping"].add((
                normalize(requirement_id),
                table_name,
            ))

    for relationship in design.get("relationships", []):
        result["relationships"].add((
            canonical_table(
                relationship["from_table"], aliases
            ),
            canonical_table(
                relationship["to_table"], aliases
            ),
            normalize_cardinality(
                relationship["relationship_type"]
            ),
        ))

    return result


def format_item(item):
    if isinstance(item, tuple):
        return ".".join(item)

    return str(item)


def calculate_scores(tp, fp, fn):
    precision = (
        tp / (tp + fp)
        if tp + fp > 0
        else (1.0 if fn == 0 else 0.0)
    )

    recall = (
        tp / (tp + fn)
        if tp + fn > 0
        else 1.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def evaluate_metric(expected, generated):
    correct = expected & generated
    missing = expected - generated
    extra = generated - expected

    result = calculate_scores(
        len(correct),
        len(extra),
        len(missing),
    )

    result["missing"] = sorted(
        format_item(item) for item in missing
    )
    result["extra"] = sorted(
        format_item(item) for item in extra
    )

    return result


def load_cases():
    with CASES_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("cases", "evaluation_cases"):
            if isinstance(data.get(key), list):
                return data[key]

    raise ValueError(
        "Unsupported evaluation_cases.json structure"
    )


def evaluate_all(cases, mode):
    """
    mode='strict': exact normalized-name matching
    mode='semantic': approved table aliases only
    """
    reports = []

    totals = {
        metric: {"tp": 0, "fp": 0, "fn": 0}
        for metric in METRICS
    }

    skipped = []

    print("\n" + "=" * 60)
    print(f"{mode.upper()} SCHEMA QUALITY EVALUATION")
    print("=" * 60)

    for case in cases:
        case_id = case["case_id"]
        generated_path = (
            GENERATED_DIR / f"{case_id}_design.json"
        )

        if not generated_path.exists():
            print(
                f"{case_id}: SKIPPED - generated design missing"
            )
            skipped.append(case_id)
            continue

        with generated_path.open(
            "r", encoding="utf-8"
        ) as file:
            design = json.load(file)

        expected = expected_features(
            case["expected_design"]
        )

        aliases = (
            {
                normalize(source): normalize(target)
                for source, target in APPROVED_ALIASES.get(
                    case_id, {}
                ).items()
            }
            if mode == "semantic"
            else {}
        )

        generated = generated_features(
            design,
            aliases=aliases,
        )

        scores = {}

        print(
            f"\n{case_id}: {case['project_id']}"
        )

        for metric in METRICS:
            score = evaluate_metric(
                expected[metric],
                generated[metric],
            )

            scores[metric] = score

            for key in ("tp", "fp", "fn"):
                totals[metric][key] += score[key]

            print(
                f"  {metric:22s} "
                f"P={score['precision']:.3f} "
                f"R={score['recall']:.3f} "
                f"F1={score['f1']:.3f}"
            )

        reports.append({
            "case_id": case_id,
            "project_id": case["project_id"],
            "applied_table_aliases": aliases,
            "metrics": scores,
        })

    overall = {}

    print("\n" + "=" * 60)
    print(f"{mode.upper()} MICRO-AVERAGED RESULTS")
    print("=" * 60)

    for metric in METRICS:
        counts = totals[metric]

        score = calculate_scores(
            counts["tp"],
            counts["fp"],
            counts["fn"],
        )

        overall[metric] = score

        print(
            f"{metric:22s} "
            f"P={score['precision']:.3f} "
            f"R={score['recall']:.3f} "
            f"F1={score['f1']:.3f}"
        )

    return {
        "evaluation_method": (
            "exact_normalized_name_match"
            if mode == "strict"
            else "human_approved_table_alias_match"
        ),
        "total_cases": len(cases),
        "evaluated_cases": len(reports),
        "skipped_cases": skipped,
        "approved_aliases": (
            APPROVED_ALIASES
            if mode == "semantic"
            else {}
        ),
        "overall": overall,
        "cases": reports,
    }


def save_report(report, json_name, csv_name):
    json_path = OUTPUT_DIR / json_name
    csv_path = OUTPUT_DIR / csv_name

    with json_path.open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    with csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)

        writer.writerow([
            "metric",
            "tp",
            "fp",
            "fn",
            "precision",
            "recall",
            "f1",
        ])

        for metric, score in report["overall"].items():
            writer.writerow([
                metric,
                score["tp"],
                score["fp"],
                score["fn"],
                score["precision"],
                score["recall"],
                score["f1"],
            ])

    print("\nSaved:")
    print(json_path)
    print(csv_path)


def save_comparison(strict_report, semantic_report):
    comparison_path = (
        OUTPUT_DIR / "schema_quality_comparison.csv"
    )

    with comparison_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)

        writer.writerow([
            "metric",
            "strict_f1",
            "semantic_f1",
            "f1_difference",
        ])

        for metric in METRICS:
            strict_f1 = strict_report["overall"][metric]["f1"]
            semantic_f1 = semantic_report["overall"][metric]["f1"]

            writer.writerow([
                metric,
                strict_f1,
                semantic_f1,
                round(semantic_f1 - strict_f1, 4),
            ])

    print("\n" + "=" * 60)
    print("STRICT VS SEMANTIC COMPARISON")
    print("=" * 60)

    for metric in METRICS:
        strict_f1 = strict_report["overall"][metric]["f1"]
        semantic_f1 = semantic_report["overall"][metric]["f1"]

        print(
            f"{metric:22s} "
            f"Strict={strict_f1:.3f} "
            f"Semantic={semantic_f1:.3f}"
        )

    print("\nComparison saved:")
    print(comparison_path)


def main():
    cases = load_cases()
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    strict_report = evaluate_all(
        cases,
        mode="strict",
    )

    semantic_report = evaluate_all(
        cases,
        mode="semantic",
    )

    # Preserve original report names for existing workflows.
    save_report(
        strict_report,
        "schema_quality_report.json",
        "schema_quality_summary.csv",
    )

    # New human-reviewed naming-equivalence reports.
    save_report(
        semantic_report,
        "schema_quality_semantic_report.json",
        "schema_quality_semantic_summary.csv",
    )

    save_comparison(
        strict_report,
        semantic_report,
    )

    print("\nSchema quality evaluation completed!")


if __name__ == "__main__":
    main()
