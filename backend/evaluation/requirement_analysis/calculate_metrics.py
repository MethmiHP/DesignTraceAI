# Calculates final Requirement Analysis evaluation metrics by comparing
# human-reviewed gold labels with successfully matched pipeline predictions.
# It reports classification and detection metrics for FR/NFR, NFR categories,
# ASRs, ambiguity, incompleteness, conflicts, missing requirements, and coverage.

import csv
from pathlib import Path


PREDICTIONS_FILE = Path(
    "evaluation/requirement_analysis/"
    "requirement_analysis_predictions.csv"
)


# HELPERS

def to_bool(value):
    """
    Convert CSV values into Python booleans.
    """

    if isinstance(value, bool):
        return value

    if value is None:
        return False

    return str(value).strip().lower() in {
        "true",
        "1",
        "yes"
    }


def safe_divide(numerator, denominator):
    """
    Avoid division-by-zero errors.
    """

    if denominator == 0:
        return 0.0

    return numerator / denominator


# BINARY CLASSIFICATION METRICS

def binary_metrics(
    y_true,
    y_pred
):
    """
    Calculate:
    - accuracy
    - precision
    - recall
    - F1
    - TP
    - TN
    - FP
    - FN
    """

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    for truth, pred in zip(
        y_true,
        y_pred
    ):

        if truth is True and pred is True:
            tp += 1

        elif truth is False and pred is False:
            tn += 1

        elif truth is False and pred is True:
            fp += 1

        elif truth is True and pred is False:
            fn += 1

    total = (
        tp
        + tn
        + fp
        + fn
    )

    accuracy = safe_divide(
        tp + tn,
        total
    )

    precision = safe_divide(
        tp,
        tp + fp
    )

    recall = safe_divide(
        tp,
        tp + fn
    )

    f1 = safe_divide(
        2 * precision * recall,
        precision + recall
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "total": total,
    }


# MULTI-CLASS METRICS
def multiclass_metrics(
    y_true,
    y_pred
):
    """
    Calculate:
    - accuracy
    - per-class precision/recall/F1
    - macro F1
    - weighted F1
    """

    labels = sorted(
        set(y_true)
        | set(y_pred)
    )

    total = len(y_true)

    correct = sum(
        1
        for truth, pred
        in zip(
            y_true,
            y_pred
        )
        if truth == pred
    )

    accuracy = safe_divide(
        correct,
        total
    )

    per_class = {}

    macro_f1_values = []

    weighted_f1_sum = 0.0

    total_support = 0

    for label in labels:

        tp = sum(
            1
            for truth, pred
            in zip(
                y_true,
                y_pred
            )
            if (
                truth == label
                and
                pred == label
            )
        )

        fp = sum(
            1
            for truth, pred
            in zip(
                y_true,
                y_pred
            )
            if (
                truth != label
                and
                pred == label
            )
        )

        fn = sum(
            1
            for truth, pred
            in zip(
                y_true,
                y_pred
            )
            if (
                truth == label
                and
                pred != label
            )
        )

        support = sum(
            1
            for truth in y_true
            if truth == label
        )

        precision = safe_divide(
            tp,
            tp + fp
        )

        recall = safe_divide(
            tp,
            tp + fn
        )

        f1 = safe_divide(
            2 * precision * recall,
            precision + recall
        )

        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

        macro_f1_values.append(
            f1
        )

        weighted_f1_sum += (
            f1
            * support
        )

        total_support += support

    macro_f1 = safe_divide(
        sum(
            macro_f1_values
        ),
        len(
            macro_f1_values
        )
    )

    weighted_f1 = safe_divide(
        weighted_f1_sum,
        total_support
    )

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class": per_class,
        "total": total,
    }


# LOAD VALID PREDICTIONS

def load_predictions():

    if not PREDICTIONS_FILE.exists():

        raise FileNotFoundError(
            f"Predictions file not found: "
            f"{PREDICTIONS_FILE}"
        )

    with PREDICTIONS_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        rows = list(
            csv.DictReader(
                file
            )
        )

    # Only evaluate successful matched predictions.
    valid_rows = [
        row
        for row in rows
        if row.get(
            "status"
        ) == "OK"
    ]

    return (
        rows,
        valid_rows
    )


# PRINT HELPER

def print_metric_block(
    title,
    metrics
):

    print(
        "\n---------------------------------------"
    )

    print(
        title
    )

    print(
        "---------------------------------------"
    )

    print(
        f"Accuracy : "
        f"{metrics['accuracy']:.4f}"
    )

    print(
        f"Precision: "
        f"{metrics['precision']:.4f}"
    )

    print(
        f"Recall   : "
        f"{metrics['recall']:.4f}"
    )

    print(
        f"F1       : "
        f"{metrics['f1']:.4f}"
    )

    print(
        f"TP={metrics['tp']} "
        f"TN={metrics['tn']} "
        f"FP={metrics['fp']} "
        f"FN={metrics['fn']}"
    )


# MAIN

def main():

    print(
        "\n======================================="
    )

    print(
        "REQUIREMENT ANALYSIS METRICS"
    )

    print(
        "======================================="
    )


    # LOAD PREDICTIONS

    all_rows, valid_rows = (
        load_predictions()
    )

    print(
        f"Rows in prediction file: "
        f"{len(all_rows)}"
    )

    print(
        f"Valid matched rows: "
        f"{len(valid_rows)}"
    )

    print(
        f"Excluded rows: "
        f"{len(all_rows) - len(valid_rows)}"
    )


    if not valid_rows:

        print(
            "\nNo valid predictions available yet."
        )

        print(
            "Run the prediction evaluation first."
        )

        return


    # 1. FR / NFR

    fr_nfr_true = [
        row[
            "gold_requirement_type"
        ]
        for row in valid_rows
    ]

    fr_nfr_pred = [
        row[
            "pred_requirement_type"
        ]
        for row in valid_rows
    ]

    fr_nfr_metrics = (
        multiclass_metrics(
            fr_nfr_true,
            fr_nfr_pred
        )
    )

    print(
        "\n======================================="
    )

    print(
        "1. FR / NFR CLASSIFICATION"
    )

    print(
        "======================================="
    )

    print(
        f"Accuracy   : "
        f"{fr_nfr_metrics['accuracy']:.4f}"
    )

    print(
        f"Macro F1   : "
        f"{fr_nfr_metrics['macro_f1']:.4f}"
    )

    print(
        f"Weighted F1: "
        f"{fr_nfr_metrics['weighted_f1']:.4f}"
    )


    print(
        "\nPer class:"
    )

    for label, values in (
        fr_nfr_metrics[
            "per_class"
        ].items()
    ):

        print(
            f"{label}: "
            f"Precision={values['precision']:.4f}, "
            f"Recall={values['recall']:.4f}, "
            f"F1={values['f1']:.4f}, "
            f"Support={values['support']}"
        )


    # 2. NFR QUALITY ATTRIBUTE

    nfr_rows = [
        row
        for row in valid_rows
        if (
            row[
                "gold_requirement_type"
            ]
            == "NFR"
        )
    ]


    if nfr_rows:

        nfr_true = [
            (
                row[
                    "gold_quality_attribute"
                ]
                or ""
            )
            for row in nfr_rows
        ]

        nfr_pred = [
            (
                row[
                    "pred_quality_attribute"
                ]
                or ""
            )
            for row in nfr_rows
        ]

        nfr_metrics = (
            multiclass_metrics(
                nfr_true,
                nfr_pred
            )
        )

        print(
            "\n======================================="
        )

        print(
            "2. NFR QUALITY ATTRIBUTE"
        )

        print(
            "======================================="
        )

        print(
            f"NFR rows     : "
            f"{len(nfr_rows)}"
        )

        print(
            f"Accuracy     : "
            f"{nfr_metrics['accuracy']:.4f}"
        )

        print(
            f"Macro F1     : "
            f"{nfr_metrics['macro_f1']:.4f}"
        )

        print(
            f"Weighted F1  : "
            f"{nfr_metrics['weighted_f1']:.4f}"
        )


        print(
            "\nPer class:"
        )

        for label, values in (
            nfr_metrics[
                "per_class"
            ].items()
        ):

            print(
                f"{label}: "
                f"Precision={values['precision']:.4f}, "
                f"Recall={values['recall']:.4f}, "
                f"F1={values['f1']:.4f}, "
                f"Support={values['support']}"
            )


    # 3. ASR

    asr_true = [
        to_bool(
            row["gold_asr"]
        )
        for row in valid_rows
    ]

    asr_pred = [
        to_bool(
            row["pred_asr"]
        )
        for row in valid_rows
    ]

    asr_metrics = binary_metrics(
        asr_true,
        asr_pred
    )

    print_metric_block(
        "3. ASR DETECTION",
        asr_metrics
    )


    # 4. AMBIGUITY

    ambiguous_true = [
        to_bool(
            row[
                "gold_ambiguous"
            ]
        )
        for row in valid_rows
    ]

    ambiguous_pred = [
        to_bool(
            row[
                "pred_ambiguous"
            ]
        )
        for row in valid_rows
    ]

    ambiguous_metrics = binary_metrics(
        ambiguous_true,
        ambiguous_pred
    )

    print_metric_block(
        "4. AMBIGUITY DETECTION",
        ambiguous_metrics
    )


    # 5. INCOMPLETENESS

    incomplete_true = [
        to_bool(
            row[
                "gold_incomplete"
            ]
        )
        for row in valid_rows
    ]

    incomplete_pred = [
        to_bool(
            row[
                "pred_incomplete"
            ]
        )
        for row in valid_rows
    ]

    incomplete_metrics = binary_metrics(
        incomplete_true,
        incomplete_pred
    )

    print_metric_block(
        "5. INCOMPLETENESS DETECTION",
        incomplete_metrics
    )


    # 6. CONFLICT

    conflicting_true = [
        to_bool(
            row[
                "gold_conflicting"
            ]
        )
        for row in valid_rows
    ]

    conflicting_pred = [
        to_bool(
            row[
                "pred_conflicting"
            ]
        )
        for row in valid_rows
    ]

    conflict_metrics = binary_metrics(
        conflicting_true,
        conflicting_pred
    )

    print_metric_block(
        "6. CONFLICT DETECTION",
        conflict_metrics
    )


    # 7. POTENTIALLY MISSING

    missing_true = [
        to_bool(
            row[
                "gold_potentially_missing"
            ]
        )
        for row in valid_rows
    ]

    missing_pred = [
        to_bool(
            row[
                "pred_potentially_missing"
            ]
        )
        for row in valid_rows
    ]

    missing_metrics = binary_metrics(
        missing_true,
        missing_pred
    )

    print_metric_block(
        "7. POTENTIALLY MISSING DETECTION",
        missing_metrics
    )


    # FINAL COVERAGE

    print(
        "\n======================================="
    )

    print(
        "EVALUATION COVERAGE"
    )

    print(
        "======================================="
    )

    coverage = safe_divide(
        len(valid_rows),
        len(all_rows)
    )

    print(
        f"Successfully evaluated rows: "
        f"{len(valid_rows)}"
    )

    print(
        f"Total prediction rows: "
        f"{len(all_rows)}"
    )

    print(
        f"Coverage: "
        f"{coverage:.4f}"
    )


if __name__ == "__main__":
    main()