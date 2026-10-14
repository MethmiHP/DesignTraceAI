def find_span(
    text: str,
    phrase: str,
    label: str,
):
    if not phrase:
        return None

    start = text.lower().find(
        phrase.lower()
    )

    if start == -1:
        return None

    end = start + len(phrase)

    return (
        start,
        end,
        label,
    )


def get_gold_entities(
    row: dict,
):
    text = row["requirement_text"]

    entities = set()

    fields = [
        ("actor_text", "ACTOR"),
        ("action_text", "ACTION"),
        ("resource_text", "RESOURCE"),
    ]

    for column, label in fields:

        span = find_span(
            text,
            row[column],
            label,
        )

        if span:
            entities.add(span)

    return entities


def calculate_metrics(
    results: list[tuple[set, set]],
):
    labels = [
        "ACTOR",
        "ACTION",
        "RESOURCE",
    ]

    metrics = {}

    macro_f1 = 0

    for label in labels:

        tp = 0
        fp = 0
        fn = 0

        for gold, predicted in results:

            gold_label = {
                item
                for item in gold
                if item[2] == label
            }

            predicted_label = {
                item
                for item in predicted
                if item[2] == label
            }

            tp += len(
                gold_label
                & predicted_label
            )

            fp += len(
                predicted_label
                - gold_label
            )

            fn += len(
                gold_label
                - predicted_label
            )

        precision = (
            tp / (tp + fp)
            if tp + fp
            else 0
        )

        recall = (
            tp / (tp + fn)
            if tp + fn
            else 0
        )

        f1 = (
            2
            * precision
            * recall
            / (precision + recall)
            if precision + recall
            else 0
        )

        metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

        macro_f1 += f1

    metrics["macro_f1"] = (
        macro_f1 / len(labels)
    )

    exact_matches = sum(
        gold == predicted
        for gold, predicted in results
    )

    metrics["exact_match"] = (
        exact_matches
        / len(results)
        if results
        else 0
    )

    return metrics


def print_metrics(
    name: str,
    metrics: dict,
):

    print()
    print(name)
    print("=" * len(name))

    for label in [
        "ACTOR",
        "ACTION",
        "RESOURCE",
    ]:

        result = metrics[label]

        print()
        print(label)

        print(
            f"Precision: "
            f"{result['precision']:.3f}"
        )

        print(
            f"Recall:    "
            f"{result['recall']:.3f}"
        )

        print(
            f"F1:        "
            f"{result['f1']:.3f}"
        )

    print()

    print(
        f"Macro F1: "
        f"{metrics['macro_f1']:.3f}"
    )

    print(
        f"All-three exact match: "
        f"{metrics['exact_match']:.3f}"
    )