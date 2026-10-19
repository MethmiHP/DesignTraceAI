"""Map requirement constraints to existing columns without guessing."""

import re
from shared.models.database import DatabaseDesign


STOP_WORDS = {
    "a", "an", "the", "of", "for", "in", "on", "to",
    "each", "every", "must", "shall", "should",
}


def _tokens(value):
    value = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1_\2",
        str(value or ""),
    ).lower()

    words = re.findall(r"[a-z0-9]+", value)
    result = []

    for word in words:
        if word in STOP_WORDS:
            continue

        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif (
            word.endswith("s")
            and not word.endswith(("ss", "us", "is"))
            and len(word) > 3
        ):
            word = word[:-1]

        result.append(word)

    return result


def _score_match(hint, table_name, column_name):
    hint_tokens = set(_tokens(hint))
    column_tokens = set(_tokens(column_name))
    table_tokens = set(_tokens(table_name))

    if not hint_tokens or not column_tokens:
        return 0

    if not column_tokens.issubset(hint_tokens):
        return 0

    extra_tokens = hint_tokens - column_tokens

    if not extra_tokens:
        return 100

    if extra_tokens.issubset(table_tokens):
        return 90

    if table_tokens and table_tokens.issubset(hint_tokens):
        return 80

    return 0


# Keep compatibility with diagnostic scripts.
score_match = _score_match


def map_requirement_constraints(
    design: DatabaseDesign,
    constraints: list[dict],
) -> list[dict]:

    mapped = []

    for constraint in constraints:
        hint = (
            constraint.get("column_hint")
            or constraint.get("column")
            or ""
        )

        candidates = []

        for table in design.tables:
            for column in table.columns:
                score = _score_match(
                    hint,
                    table.table_name,
                    column.name,
                )

                if score > 0:
                    candidates.append({
                        "table": table.table_name,
                        "column": column.name,
                        "score": score,
                    })

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        if candidates:
            best_score = candidates[0]["score"]
            best = [
                item
                for item in candidates
                if item["score"] == best_score
            ]
        else:
            best = []

        candidate_columns = [
            {
                "table": item["table"],
                "column": item["column"],
            }
            for item in candidates
        ]

        if len(best) == 1:
            mapped.append({
                **constraint,
                "table": best[0]["table"],
                "column": best[0]["column"],
                "status": "MAPPED",
                "candidate_columns": candidate_columns,
            })
        else:
            mapped.append({
                **constraint,
                "table": None,
                "column": None,
                "status": (
                    "AMBIGUOUS" if best else "UNMAPPED"
                ),
                "candidate_columns": candidate_columns,
            })

    return mapped