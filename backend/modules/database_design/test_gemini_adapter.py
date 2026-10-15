"""
Test conversion of Gemini JSON into the
existing DesignTrace AI DatabaseDesign model.
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from modules.database_design.gemini_adapter import (
    convert_gemini_design,
)


def main():
    input_path = (
        BASE_DIR
        / "outputs"
        / "database_designs"
        / "LLM-001_gemini.json"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Gemini output not found: {input_path}"
        )

    with input_path.open(
        "r",
        encoding="utf-8"
    ) as file:
        gemini_design = json.load(file)

    design = convert_gemini_design(
        gemini_design
    )

    print("DesignTrace AI - Gemini Adapter Test")
    print("------------------------------------")

    print("\nConverted tables:")

    for table in design.tables:
        print("-", table.table_name)

        for column in table.columns:
            print(
                "   ",
                column.name,
                column.data_type,
            )

            if column.foreign_key:
                print(
                    "      FK ->",
                    column.foreign_key.table,
                    ".",
                    column.foreign_key.column,
                    sep="",
                )

    print(
        "\nRelationships:",
        len(design.relationships)
    )

    print(
        "Constraints:",
        len(design.constraints)
    )

    output_path = (
        BASE_DIR
        / "outputs"
        / "database_designs"
        / "LLM-001_standardized.json"
    )

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            design.model_dump(),
            file,
            indent=2,
        )

    print("\nSaved:", output_path)
    print("\nGemini adapter test successful!")


if __name__ == "__main__":
    main()
