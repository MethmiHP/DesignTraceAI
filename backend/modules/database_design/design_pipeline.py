# """
# DesignTrace AI - Database Design Pipeline

# Supports:
# - Deterministic database design generation
# - Gemini + RoBERTa database design generation
# - Structural schema validation
# - Requirement traceability validation
# - Project-independent constraint extraction and mapping
# - SQL generation and SQL constraint validation
# - SQL and Mermaid artifact saving

# The Database Design Module returns a draft and validation
# report. The Coordinator Agent handles approval, retries,
# feedback and version management.
# """

# import re
# from pathlib import Path
# from typing import Any

# from shared.models.project import ProjectInput
# from shared.models.database import DatabaseDesign

# from modules.database_design.concept_pipeline import (
#     run_concept_pipeline,
# )
# from modules.database_design.schema_generator import (
#     generate_schema_from_concepts,
# )
# from modules.database_design.relationship_generator import (
#     add_database_relationships,
# )
# from modules.database_design.constraint_generator import (
#     generate_database_constraints,
# )
# from modules.database_design.requirement_constraint_extractor import (
#     extract_requirement_constraints,
# )
# from modules.database_design.requirement_constraint_mapper import (
#     map_requirement_constraints,
# )
# from modules.database_design.requirement_constraint_applier import (
#     apply_requirement_constraints,
# )
# from modules.database_design.database_module import (
#     _apply_feedback,
# )
# from modules.database_design.gemini_adapter import (
#     convert_gemini_design,
# )
# from modules.database_design.artifact_adapter import (
#     convert_design_for_artifacts,
# )
# from modules.database_design.artifact_generator import (
#     generate_sql,
#     save_artifacts,
# )
# from modules.database_design.sql_constraint_validator import (
#     validate_sql_constraints,
# )
# from modules.database_design.schema_validator import (
#     validate_database_design,
# )


# # ============================================================
# # 1. DETERMINISTIC GENERATION
# # ============================================================

# def _generate_deterministic_design(
#     project: ProjectInput,
#     feedback: list[str] | None = None,
# ) -> DatabaseDesign:

#     design = generate_schema_from_concepts(project)

#     design = add_database_relationships(
#         design,
#         project.requirements,
#     )

#     if feedback:
#         design = _apply_feedback(design, feedback)

#     design = generate_database_constraints(design)

#     # Preserve the existing deterministic constraint workflow.
#     requirement_texts = [
#         req.requirement_text
#         for req in project.requirements
#         if req.database_relevant
#     ]

#     extracted = extract_requirement_constraints(
#         requirement_texts
#     )

#     mapped = map_requirement_constraints(
#         design,
#         extracted,
#     )

#     design = apply_requirement_constraints(
#         design,
#         mapped,
#     )

#     return design


# # ============================================================
# # 2. GEMINI + ROBERTA GENERATION
# # ============================================================

# def _generate_gemini_design(
#     project: ProjectInput,
#     extracted_concepts: Any = None,
# ) -> DatabaseDesign:

#     from shared.llm.gemini_generator import (
#         generate_database_design,
#     )

#     requirements = [
#         {
#             "requirement_id": req.requirement_id,
#             "text": req.requirement_text,
#         }
#         for req in project.requirements
#         if req.database_relevant
#     ]

#     if not requirements:
#         raise ValueError(
#             "No database-relevant requirements provided."
#         )

#     if extracted_concepts is None:
#         print("\nRunning RoBERTa concept extraction...")

#         concept_result = run_concept_pipeline(
#             project,
#             method="roberta",
#         )

#         extracted_concepts = {
#             "entities": concept_result.candidate_entities,
#             "attributes": concept_result.candidate_attributes,
#             "actions": concept_result.candidate_actions,
#         }

#         print(
#             "Entities:",
#             extracted_concepts["entities"],
#         )
#         print(
#             "Attributes:",
#             extracted_concepts["attributes"],
#         )
#         print(
#             "Actions:",
#             extracted_concepts["actions"],
#         )

#     architecture_context = (
#         project.architecture_context.model_dump()
#         if project.architecture_context is not None
#         else {}
#     )

#     print("\nGenerating database schema using Gemini...")

#     gemini_design = generate_database_design(
#         requirements=requirements,
#         project_name=project.project_name,
#         architecture_context=architecture_context,
#         database_constraints=architecture_context.get(
#             "constraints", []
#         ),
#         extracted_concepts=extracted_concepts,
#     )

#     print("\nConverting Gemini output...")

#     return convert_gemini_design(gemini_design)


# # ============================================================
# # 3. GENERATION METHOD SELECTION
# # ============================================================

# def generate_database_design_pipeline(
#     project: ProjectInput,
#     feedback: list[str] | None = None,
#     generation_method: str = "deterministic",
#     extracted_concepts: Any = None,
# ) -> DatabaseDesign:

#     if generation_method == "deterministic":
#         return _generate_deterministic_design(
#             project=project,
#             feedback=feedback,
#         )

#     if generation_method == "gemini":
#         if feedback:
#             raise ValueError(
#                 "Gemini feedback regeneration must be "
#                 "managed by the Coordinator Agent."
#             )

#         return _generate_gemini_design(
#             project=project,
#             extracted_concepts=extracted_concepts,
#         )

#     raise ValueError(
#         f"Unknown generation method: {generation_method}"
#     )


# # ============================================================
# # 4. GENERAL COLUMN NAME MATCHING
# # ============================================================

# def _normalize_name(value):
#     value = str(value).lower().strip()
#     value = re.sub(r"[^a-z0-9]+", "_", value)
#     return value.strip("_")


# def _singular_name(value):
#     words = _normalize_name(value).split("_")
#     result = []

#     for word in words:
#         if word.endswith("ies") and len(word) > 3:
#             word = word[:-3] + "y"
#         elif (
#             word.endswith("s")
#             and len(word) > 3
#             and not word.endswith("ss")
#             and not word.endswith("us")
#         ):
#             word = word[:-1]

#         result.append(word)

#     return "_".join(result)


# def _match_constraint_column(hint, design):
#     """
#     Map a natural-language column hint to a generated column.

#     Examples:
#       product_price -> products.price
#       customer_email -> customers.email
#       available_stock_quantity -> products.available_stock_quantity
#       order_item_quantity -> order_items.quantity

#     Ambiguous matches are not silently accepted.
#     """

#     hint = _singular_name(hint)
#     candidates = []

#     for table in design.tables:
#         table_name = _singular_name(table.table_name)

#         for column in table.columns:
#             column_name = _singular_name(column.name)

#             full_name = f"{table_name}_{column_name}"

#             # Assign a score to possible matches.
#             score = 0

#             if hint == full_name:
#                 score = 100

#             elif hint == column_name:
#                 score = 80

#             elif hint == f"{table_name}_{column_name}":
#                 score = 100

#             elif hint.endswith("_" + full_name):
#                 score = 95

#             elif hint.startswith(table_name + "_"):
#                 remainder = hint[len(table_name) + 1:]

#                 if remainder == column_name:
#                     score = 100
#                 elif column_name.endswith("_" + remainder):
#                     score = 90
#                 elif remainder.endswith("_" + column_name):
#                     score = 85

#             elif column_name.endswith("_" + hint):
#                 score = 65

#             elif hint.endswith("_" + column_name):
#                 score = 50

#             if score > 0:
#                 candidates.append(
#                     {
#                         "table": table.table_name,
#                         "column": column.name,
#                         "score": score,
#                     }
#                 )

#     if not candidates:
#         return None, []

#     best_score = max(
#         candidate["score"]
#         for candidate in candidates
#     )

#     best = [
#         candidate
#         for candidate in candidates
#         if candidate["score"] == best_score
#     ]

#     if len(best) == 1:
#         return best[0], candidates

#     return None, candidates


# # ============================================================
# # 5. EXTRACT AND MAP PROJECT CONSTRAINTS
# # ============================================================

# def _expected_constraint_rules(project, design):
#     """
#     Extract explicit constraints from project requirements
#     and architecture constraints.

#     The rules are project-independent.

#     Returns:
#         rules
#         mapped_constraints
#         unresolved_constraints
#         extraction_information
#     """

#     requirement_statements = [
#         req.requirement_text
#         for req in project.requirements
#         if req.database_relevant
#     ]

#     architecture_constraints = []

#     if project.architecture_context is not None:
#         architecture_constraints = list(
#             project.architecture_context.constraints or []
#         )

#     statements = (
#         requirement_statements
#         + architecture_constraints
#     )

#     # --------------------------------------------------------
#     # Debug the real project input.
#     # --------------------------------------------------------

#     print("\n========== CONSTRAINT INPUT DEBUG ==========")

#     print("\nArchitecture context:")

#     if project.architecture_context is not None:
#         print(
#             project.architecture_context.model_dump()
#         )
#     else:
#         print("No architecture context received.")

#     print("\nStatements received by extractor:")

#     for index, statement in enumerate(
#         statements,
#         start=1,
#     ):
#         print(f"{index}. {statement}")

#     print("============================================")

#     # --------------------------------------------------------
#     # Extract rules.
#     # --------------------------------------------------------

#     extracted = extract_requirement_constraints(
#         statements
#     )

#     print("\nExtracted explicit constraints:")

#     for rule in extracted:
#         print(rule)

#     if not extracted:
#         print("No explicit constraints extracted.")

#     rules = {
#         "unique": [],
#         "checks": [],
#         "not_null": [],
#         "foreign_keys": [],
#         "primary_keys": [],
#         "identity": [],
#     }

#     mapped = []
#     unresolved = []
#     seen_sql_rules = set()

#     # --------------------------------------------------------
#     # Map rules to generated schema columns.
#     # --------------------------------------------------------

#     for rule in extracted:
#         hint = rule.get("column_hint", "")

#         selected, candidates = _match_constraint_column(
#             hint,
#             design,
#         )

#         if selected is not None:
#             resolved = {
#                 **rule,
#                 "table": selected["table"],
#                 "column": selected["column"],
#                 "status": "MAPPED",
#             }

#             mapped.append(resolved)

#             rule_type = rule.get("type")

#             target_key = {
#                 "UNIQUE": "unique",
#                 "CHECK": "checks",
#                 "NOT_NULL": "not_null",
#             }.get(rule_type)

#             if target_key is not None:
#                 # One SQL rule can satisfy multiple original requirements.
#                 # Keep every entry in `mapped` for traceability.
#                 from decimal import Decimal
#                 key = (resolved["table"], resolved["column"], rule_type)
#                 if rule_type == "CHECK":
#                     if "allowed_values" in resolved:
#                         key += ("IN", tuple(sorted(set(map(str, resolved["allowed_values"])))),)
#                     else:
#                         value = resolved.get("value")
#                         normalized = Decimal(str(value)) if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value)
#                         key += (resolved.get("operator"), normalized)
#                 if key not in seen_sql_rules:
#                     rules[target_key].append(resolved)
#                     seen_sql_rules.add(key)

#             print(
#                 "MAPPED:",
#                 hint,
#                 "->",
#                 f'{selected["table"]}.{selected["column"]}',
#             )

#         else:
#             unresolved_rule = {
#                 **rule,
#                 "status": (
#                     "AMBIGUOUS"
#                     if candidates
#                     else "UNMAPPED"
#                 ),
#                 "candidate_columns": candidates,
#             }

#             unresolved.append(unresolved_rule)

#             print(
#                 "UNRESOLVED:",
#                 hint,
#                 candidates,
#             )

#     # --------------------------------------------------------
#     # Structural rules from the generated design.
#     # --------------------------------------------------------

#     for table in design.tables:
#         primary_keys = [
#             column.name
#             for column in table.columns
#             if column.primary_key
#         ]

#         if primary_keys:
#             rules["primary_keys"].append(
#                 {
#                     "table": table.table_name,
#                     "columns": primary_keys,
#                 }
#             )

#         for column in table.columns:
#             if column.foreign_key is not None:
#                 rules["foreign_keys"].append(
#                     {
#                         "table": table.table_name,
#                         "column": column.name,
#                         "references_table": (
#                             column.foreign_key.table
#                         ),
#                         "references_column": (
#                             column.foreign_key.column
#                         ),
#                     }
#                 )

#     extraction_information = {
#         "input_statement_count": len(statements),
#         "architecture_constraint_count": len(
#             architecture_constraints
#         ),
#         "extracted_constraint_count": len(extracted),
#         "mapped_constraint_count": len(mapped),
#         "unresolved_constraint_count": len(unresolved),
#     }

#     print("\nExpected SQL constraint counts:")

#     for key, values in rules.items():
#         print(f"{key}: {len(values)}")

#     print("Unresolved:", len(unresolved))

#     return (
#         rules,
#         mapped,
#         unresolved,
#         extraction_information,
#     )


# # ============================================================
# # 6. REQUIREMENT TRACEABILITY VALIDATION
# # ============================================================

# def _validate_requirement_mapping(project, design):
#     relevant_requirements = [
#         requirement
#         for requirement in project.requirements
#         if requirement.database_relevant
#     ]

#     required_ids = {
#         requirement.requirement_id
#         for requirement in relevant_requirements
#     }

#     mappings = []
#     mapped_ids = set()
#     mapping_errors = []

#     for requirement in relevant_requirements:
#         related_tables = sorted(
#             table.table_name
#             for table in design.tables
#             if requirement.requirement_id
#             in table.source_requirement_ids
#         )

#         if related_tables:
#             mapped_ids.add(
#                 requirement.requirement_id
#             )

#         mappings.append(
#             {
#                 "requirement_id": (
#                     requirement.requirement_id
#                 ),
#                 "related_tables": related_tables,
#             }
#         )

#     for table in design.tables:
#         for source_id in table.source_requirement_ids:
#             if source_id not in required_ids:
#                 mapping_errors.append(
#                     f"Unknown requirement ID "
#                     f"'{source_id}' in table "
#                     f"'{table.table_name}'."
#                 )

#     for requirement_id in sorted(
#         required_ids - mapped_ids
#     ):
#         mapping_errors.append(
#             f"No table mapping for requirement "
#             f"'{requirement_id}'."
#         )

#     total_requirements = len(required_ids)

#     coverage = (
#         len(mapped_ids) / total_requirements * 100
#         if total_requirements
#         else 0.0
#     )

#     return {
#         "valid": (
#             len(mapping_errors) == 0
#             and total_requirements > 0
#         ),
#         "coverage_percentage": round(coverage, 2),
#         "total_requirements": total_requirements,
#         "mapped_requirements": len(mapped_ids),
#         "requirement_mappings": mappings,
#         "errors": mapping_errors,
#         "warnings": [],
#     }


# # ============================================================
# # 7. COMPLETE DATABASE DESIGN PIPELINE
# # ============================================================

# def run_complete_database_design(
#     project: ProjectInput,
#     generation_method: str = "gemini",
#     extracted_concepts: Any = None,
#     output_dir: str | Path | None = None,
# ) -> dict:

#     print(
#         "\nDesignTrace AI - Complete "
#         "Database Design Pipeline"
#     )

#     # STEP 1: Generate the database design.
#     design = generate_database_design_pipeline(
#         project=project,
#         generation_method=generation_method,
#         extracted_concepts=extracted_concepts,
#     )

#     # STEP 2: Convert to artifact format.
#     artifact_design = convert_design_for_artifacts(
#         design
#     )

#     # STEP 3: Structural schema validation.
#     print("\nValidating database schema...")

#     schema_result = validate_database_design(
#         artifact_design
#     )

#     print(
#         "Schema valid:",
#         schema_result["valid"],
#     )

#     # STEP 4: Requirement mapping validation.
#     mapping_result = _validate_requirement_mapping(
#         project,
#         design,
#     )

#     print(
#         "Mapping valid:",
#         mapping_result["valid"],
#     )

#     # STEP 5: Extract expected constraints.
#     (
#         rules,
#         mapped_constraints,
#         unresolved_constraints,
#         extraction_info,
#     ) = _expected_constraint_rules(
#         project,
#         design,
#     )

#     # STEP 6: Apply mapped UNIQUE and NOT NULL constraints.
#     design = apply_requirement_constraints(
#         design,
#         mapped_constraints,
#     )

#     # STEP 7: Convert updated design.
#     artifact_design = convert_design_for_artifacts(
#         design
#     )

#     # STEP 8: Generate SQL with CHECK constraints.
#     sql_text = generate_sql(
#         artifact_design,
#         constraint_rules=rules,
#     )

#     # STEP 9: Validate generated SQL.
#     sql_validation = validate_sql_constraints(
#         sql_text,
#         rules,
#     )

#     explicit_rule_count = (
#         len(rules["unique"])
#         + len(rules["checks"])
#         + len(rules["not_null"])
#     )

#     sql_validation["explicit_rule_count"] = (
#         explicit_rule_count
#     )

#     sql_validation["unresolved_constraints"] = (
#         unresolved_constraints
#     )

#     sql_validation["extracted_constraint_count"] = (
#         extraction_info["extracted_constraint_count"]
#     )

#     sql_validation["mapped_constraint_count"] = (
#         extraction_info["mapped_constraint_count"]
#     )

#     sql_validation["architecture_constraint_count"] = (
#         extraction_info["architecture_constraint_count"]
#     )

#     # --------------------------------------------------------
#     # Never approve unresolved extracted constraints.
#     # --------------------------------------------------------

#     if unresolved_constraints:
#         sql_validation["valid"] = False

#         for rule in unresolved_constraints:
#             sql_validation["errors"].append(
#                 "Unresolved explicit constraint: "
#                 + rule.get(
#                     "source_requirement",
#                     "Unknown source",
#                 )
#                 + " ("
#                 + rule.get("status", "UNMAPPED")
#                 + ")"
#             )

#     # --------------------------------------------------------
#     # Prevent misleading success if no explicit rules
#     # were extracted from supplied architecture constraints.
#     #
#     # This is a conservative safeguard, not a complete
#     # natural-language completeness validator.
#     # --------------------------------------------------------

#     if (
#         extraction_info["architecture_constraint_count"] > 0
#         and explicit_rule_count == 0
#     ):
#         sql_validation["valid"] = False

#         sql_validation["errors"].append(
#             "Architecture constraints were supplied, "
#             "but no explicit UNIQUE, CHECK or NOT NULL "
#             "rules were extracted. Manual review is required."
#         )

#     # Also flag the case where no explicit constraints
#     # were checked and no architecture constraints exist.
#     # Structural validation remains available.
#     if explicit_rule_count == 0:
#         sql_validation.setdefault("warnings", [])

#         sql_validation["warnings"].append(
#             "No explicit business constraints were verified. "
#             "Only structural SQL checks were performed."
#         )

#     print("\nSQL validation details:")
#     print("Explicit rules:", explicit_rule_count)
#     print(
#         "Checked rules:",
#         sql_validation.get("checked_rules", 0),
#     )
#     print(
#         "Unresolved constraints:",
#         len(unresolved_constraints),
#     )
#     print(
#         "Errors:",
#         sql_validation["errors"],
#     )

#     # STEP 10: Calculate overall validity.
#     overall_valid = bool(
#         schema_result["valid"]
#         and mapping_result["valid"]
#         and sql_validation["valid"]
#     )

#     print(
#         "\nSQL constraint validation:",
#         sql_validation["valid"],
#     )

#     print(
#         "Overall validation:",
#         overall_valid,
#     )

#     # STEP 11: Save draft artifacts.
#     artifacts = {}

#     if schema_result["valid"]:
#         if output_dir is None:
#             output_dir = (
#                 Path(__file__).resolve().parents[2]
#                 / "outputs"
#                 / "database_designs"
#                 / "artifacts"
#             )

#         artifacts = save_artifacts(
#             design=artifact_design,
#             output_dir=output_dir,
#             base_name=(
#                 f"{project.project_id}_database_design"
#             ),
#             constraint_rules=rules,
#         )

#     # STEP 12: Return draft and validation report.
#     return {
#         "project_id": project.project_id,
#         "generation_method": generation_method,
#         "design": design.model_dump(),
#         "schema_validation": schema_result,
#         "mapping_validation": mapping_result,
#         "sql_constraint_validation": sql_validation,
#         "overall_valid": overall_valid,
#         "artifacts": artifacts,
#     }

"""
DesignTrace AI - Database Design Pipeline

Supports:
- Deterministic database design generation
- Gemini + RoBERTa database design generation
- Structural schema validation
- Requirement traceability validation
- Project-independent constraint extraction and mapping
- SQL generation and SQL constraint validation
- SQL and Mermaid artifact saving

The Database Design Module returns a draft and validation
report. The Coordinator Agent handles approval, retries,
feedback and version management.
"""

import re
from pathlib import Path
from typing import Any

from shared.models.project import ProjectInput
from shared.models.database import DatabaseDesign

from modules.database_design.concept_pipeline import (
    run_concept_pipeline,
)
from modules.database_design.schema_generator import (
    generate_schema_from_concepts,
)
from modules.database_design.relationship_generator import (
    add_database_relationships,
)
from modules.database_design.constraint_generator import (
    generate_database_constraints,
)
from modules.database_design.requirement_constraint_extractor import (
    extract_requirement_constraints,
)
from modules.database_design.requirement_constraint_mapper import (
    map_requirement_constraints,
)
from modules.database_design.requirement_constraint_applier import (
    apply_requirement_constraints,
)
from modules.database_design.database_module import (
    _apply_feedback,
)
from modules.database_design.gemini_adapter import (
    convert_gemini_design,
)
from modules.database_design.artifact_adapter import (
    convert_design_for_artifacts,
)
from modules.database_design.artifact_generator import (
    generate_sql,
    save_artifacts,
)
from modules.database_design.sql_constraint_validator import (
    validate_sql_constraints,
)
from modules.database_design.schema_validator import (
    validate_database_design,
)


# ============================================================
# 1. DETERMINISTIC GENERATION
# ============================================================

def _generate_deterministic_design(
    project: ProjectInput,
    feedback: list[str] | None = None,
) -> DatabaseDesign:

    design = generate_schema_from_concepts(project)

    design = add_database_relationships(
        design,
        project.requirements,
    )

    if feedback:
        design = _apply_feedback(design, feedback)

    design = generate_database_constraints(design)

    # Preserve the existing deterministic constraint workflow.
    requirement_texts = [
        req.requirement_text
        for req in project.requirements
        if req.database_relevant
    ]

    extracted = extract_requirement_constraints(
        requirement_texts
    )

    mapped = map_requirement_constraints(
        design,
        extracted,
    )

    design = apply_requirement_constraints(
        design,
        mapped,
    )

    return design


# ============================================================
# 2. GEMINI + ROBERTA GENERATION
# ============================================================

def _generate_gemini_design(
    project: ProjectInput,
    extracted_concepts: Any = None,
) -> DatabaseDesign:

    from shared.llm.gemini_generator import (
        generate_database_design,
    )

    requirements = [
        {
            "requirement_id": req.requirement_id,
            "text": req.requirement_text,
        }
        for req in project.requirements
        if req.database_relevant
    ]

    if not requirements:
        raise ValueError(
            "No database-relevant requirements provided."
        )

    if extracted_concepts is None:
        print("\nRunning RoBERTa concept extraction...")

        concept_result = run_concept_pipeline(
            project,
            method="roberta",
        )

        extracted_concepts = {
            "entities": concept_result.candidate_entities,
            "attributes": concept_result.candidate_attributes,
            "actions": concept_result.candidate_actions,
        }

        print(
            "Entities:",
            extracted_concepts["entities"],
        )
        print(
            "Attributes:",
            extracted_concepts["attributes"],
        )
        print(
            "Actions:",
            extracted_concepts["actions"],
        )

    architecture_context = (
        project.architecture_context.model_dump()
        if project.architecture_context is not None
        else {}
    )

    print("\nGenerating database schema using Gemini...")

    gemini_design = generate_database_design(
        requirements=requirements,
        project_name=project.project_name,
        architecture_context=architecture_context,
        database_constraints=architecture_context.get(
            "constraints", []
        ),
        extracted_concepts=extracted_concepts,
    )

    print("\nConverting Gemini output...")

    return convert_gemini_design(gemini_design)


# ============================================================
# 3. GENERATION METHOD SELECTION
# ============================================================

def generate_database_design_pipeline(
    project: ProjectInput,
    feedback: list[str] | None = None,
    generation_method: str = "deterministic",
    extracted_concepts: Any = None,
) -> DatabaseDesign:

    if generation_method == "deterministic":
        return _generate_deterministic_design(
            project=project,
            feedback=feedback,
        )

    if generation_method == "gemini":
        if feedback:
            raise ValueError(
                "Gemini feedback regeneration must be "
                "managed by the Coordinator Agent."
            )

        return _generate_gemini_design(
            project=project,
            extracted_concepts=extracted_concepts,
        )

    raise ValueError(
        f"Unknown generation method: {generation_method}"
    )


# ============================================================
# 4. GENERAL COLUMN NAME MATCHING
# ============================================================

def _normalize_name(value):
    value = str(value).lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def _singular_name(value):
    words = _normalize_name(value).split("_")
    result = []

    for word in words:
        if word.endswith("ies") and len(word) > 3:
            word = word[:-3] + "y"
        elif (
            word.endswith("s")
            and len(word) > 3
            and not word.endswith("ss")
            and not word.endswith("us")
        ):
            word = word[:-1]

        result.append(word)

    return "_".join(result)


def _match_constraint_column(hint, design):
    """Map a natural-language hint to exactly one schema column.

    Prefer the shared mapper, then try conservative generic token matching
    for schema columns that add descriptive suffixes (e.g. email_address).
    Never choose between tied candidates.
    """
    mapped = map_requirement_constraints(
        design,
        [{"type": "CHECK", "column_hint": hint}],
    )[0]
    candidates = list(mapped.get("candidate_columns", []))
    if mapped.get("status") == "MAPPED":
        return {
            "table": mapped["table"],
            "column": mapped["column"],
        }, candidates
    if mapped.get("status") == "AMBIGUOUS":
        return None, candidates

    def tokens(value):
        return [part for part in _singular_name(value).split("_") if part]

    hint_words = set(tokens(hint))
    if not hint_words:
        return None, []

    ranked = []
    for table in design.tables:
        table_words = set(tokens(table.table_name))
        for column in table.columns:
            column_words = set(tokens(column.name))
            # Every hint token must be accounted for by the table or column.
            if not hint_words.issubset(table_words | column_words):
                continue
            # The descriptive part of the hint must identify the column;
            # a table prefix alone is insufficient.
            column_hint_words = hint_words - table_words
            if column_hint_words and not column_hint_words.issubset(column_words):
                continue
            if not column_hint_words and not hint_words.intersection(column_words):
                continue
            # When a hint identifies a table, favor its columns.
            table_overlap = len(hint_words & table_words)
            column_overlap = len(hint_words & column_words)
            # Penalize unexplained extra column tokens, rather than inventing
            # equivalences between different column names.
            score = (table_overlap * 100 + column_overlap * 20
                     - len(column_words - hint_words) * 5)
            ranked.append({
                "table": table.table_name,
                "column": column.name,
                "score": score,
            })

    ranked.sort(key=lambda item: item["score"], reverse=True)
    if not ranked:
        return None, []
    best = [item for item in ranked if item["score"] == ranked[0]["score"]]
    if len(best) != 1:
        return None, ranked
    return best[0], ranked


# ============================================================
# 5. EXTRACT AND MAP PROJECT CONSTRAINTS
# ============================================================

def _expected_constraint_rules(project, design):
    """
    Extract explicit constraints from project requirements
    and architecture constraints.

    The rules are project-independent.

    Returns:
        rules
        mapped_constraints
        unresolved_constraints
        extraction_information
    """

    requirement_statements = [
        req.requirement_text
        for req in project.requirements
        if req.database_relevant
    ]

    architecture_constraints = []

    if project.architecture_context is not None:
        architecture_constraints = list(
            project.architecture_context.constraints or []
        )

    statements = (
        requirement_statements
        + architecture_constraints
    )

    # --------------------------------------------------------
    # Debug the real project input.
    # --------------------------------------------------------

    print("\n========== CONSTRAINT INPUT DEBUG ==========")

    print("\nArchitecture context:")

    if project.architecture_context is not None:
        print(
            project.architecture_context.model_dump()
        )
    else:
        print("No architecture context received.")

    print("\nStatements received by extractor:")

    for index, statement in enumerate(
        statements,
        start=1,
    ):
        print(f"{index}. {statement}")

    print("============================================")

    # --------------------------------------------------------
    # Extract rules.
    # --------------------------------------------------------

    extracted = extract_requirement_constraints(
        statements
    )

    print("\nExtracted explicit constraints:")

    for rule in extracted:
        print(rule)

    if not extracted:
        print("No explicit constraints extracted.")

    rules = {
        "unique": [],
        "checks": [],
        "not_null": [],
        "foreign_keys": [],
        "primary_keys": [],
        "identity": [],
    }

    mapped = []
    unresolved = []
    seen_sql_rules = set()

    # --------------------------------------------------------
    # Map rules to generated schema columns.
    # --------------------------------------------------------

    for rule in extracted:
        hint = rule.get("column_hint", "")

        selected, candidates = _match_constraint_column(
            hint,
            design,
        )

        if selected is not None:
            resolved = {
                **rule,
                "table": selected["table"],
                "column": selected["column"],
                "status": "MAPPED",
            }

            mapped.append(resolved)

            rule_type = rule.get("type")

            target_key = {
                "UNIQUE": "unique",
                "CHECK": "checks",
                "NOT_NULL": "not_null",
            }.get(rule_type)

            if target_key is not None:
                # One SQL rule can satisfy multiple original requirements.
                # Keep every entry in `mapped` for traceability.
                from decimal import Decimal
                key = (resolved["table"], resolved["column"], rule_type)
                if rule_type == "CHECK":
                    if "allowed_values" in resolved:
                        key += ("IN", tuple(sorted(set(map(str, resolved["allowed_values"])))),)
                    else:
                        value = resolved.get("value")
                        normalized = Decimal(str(value)) if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value)
                        key += (resolved.get("operator"), normalized)
                if key not in seen_sql_rules:
                    rules[target_key].append(resolved)
                    seen_sql_rules.add(key)

            print(
                "MAPPED:",
                hint,
                "->",
                f'{selected["table"]}.{selected["column"]}',
            )

        else:
            unresolved_rule = {
                **rule,
                "status": (
                    "AMBIGUOUS"
                    if candidates
                    else "UNMAPPED"
                ),
                "candidate_columns": candidates,
            }

            unresolved.append(unresolved_rule)

            print(
                "UNRESOLVED:",
                hint,
                candidates,
            )

    # --------------------------------------------------------
    # Structural rules from the generated design.
    # --------------------------------------------------------

    for table in design.tables:
        primary_keys = [
            column.name
            for column in table.columns
            if column.primary_key
        ]

        if primary_keys:
            rules["primary_keys"].append(
                {
                    "table": table.table_name,
                    "columns": primary_keys,
                }
            )

        for column in table.columns:
            if column.foreign_key is not None:
                rules["foreign_keys"].append(
                    {
                        "table": table.table_name,
                        "column": column.name,
                        "references_table": (
                            column.foreign_key.table
                        ),
                        "references_column": (
                            column.foreign_key.column
                        ),
                    }
                )

    extraction_information = {
        "input_statement_count": len(statements),
        "architecture_constraint_count": len(
            architecture_constraints
        ),
        "extracted_constraint_count": len(extracted),
        "mapped_constraint_count": len(mapped),
        "unresolved_constraint_count": len(unresolved),
    }

    print("\nExpected SQL constraint counts:")

    for key, values in rules.items():
        print(f"{key}: {len(values)}")

    print("Unresolved:", len(unresolved))

    return (
        rules,
        mapped,
        unresolved,
        extraction_information,
    )


# ============================================================
# 6. REQUIREMENT TRACEABILITY VALIDATION
# ============================================================

def _validate_requirement_mapping(project, design):
    relevant_requirements = [
        requirement
        for requirement in project.requirements
        if requirement.database_relevant
    ]

    required_ids = {
        requirement.requirement_id
        for requirement in relevant_requirements
    }

    mappings = []
    mapped_ids = set()
    mapping_errors = []

    for requirement in relevant_requirements:
        related_tables = sorted(
            table.table_name
            for table in design.tables
            if requirement.requirement_id
            in table.source_requirement_ids
        )

        if related_tables:
            mapped_ids.add(
                requirement.requirement_id
            )

        mappings.append(
            {
                "requirement_id": (
                    requirement.requirement_id
                ),
                "related_tables": related_tables,
            }
        )

    for table in design.tables:
        for source_id in table.source_requirement_ids:
            if source_id not in required_ids:
                mapping_errors.append(
                    f"Unknown requirement ID "
                    f"'{source_id}' in table "
                    f"'{table.table_name}'."
                )

    for requirement_id in sorted(
        required_ids - mapped_ids
    ):
        mapping_errors.append(
            f"No table mapping for requirement "
            f"'{requirement_id}'."
        )

    total_requirements = len(required_ids)

    coverage = (
        len(mapped_ids) / total_requirements * 100
        if total_requirements
        else 0.0
    )

    return {
        "valid": (
            len(mapping_errors) == 0
            and total_requirements > 0
        ),
        "coverage_percentage": round(coverage, 2),
        "total_requirements": total_requirements,
        "mapped_requirements": len(mapped_ids),
        "requirement_mappings": mappings,
        "errors": mapping_errors,
        "warnings": [],
    }


# ============================================================
# 7. COMPLETE DATABASE DESIGN PIPELINE
# ============================================================

def run_complete_database_design(
    project: ProjectInput,
    generation_method: str = "gemini",
    extracted_concepts: Any = None,
    output_dir: str | Path | None = None,
) -> dict:

    print(
        "\nDesignTrace AI - Complete "
        "Database Design Pipeline"
    )

    # STEP 1: Generate the database design.
    design = generate_database_design_pipeline(
        project=project,
        generation_method=generation_method,
        extracted_concepts=extracted_concepts,
    )

    # STEP 2: Convert to artifact format.
    artifact_design = convert_design_for_artifacts(
        design
    )

    # STEP 3: Structural schema validation.
    print("\nValidating database schema...")

    schema_result = validate_database_design(
        artifact_design
    )

    print(
        "Schema valid:",
        schema_result["valid"],
    )

    # STEP 4: Requirement mapping validation.
    mapping_result = _validate_requirement_mapping(
        project,
        design,
    )

    print(
        "Mapping valid:",
        mapping_result["valid"],
    )

    # STEP 5: Extract expected constraints.
    (
        rules,
        mapped_constraints,
        unresolved_constraints,
        extraction_info,
    ) = _expected_constraint_rules(
        project,
        design,
    )

    # STEP 6: Apply mapped UNIQUE and NOT NULL constraints.
    design = apply_requirement_constraints(
        design,
        mapped_constraints,
    )

    # STEP 7: Convert updated design.
    artifact_design = convert_design_for_artifacts(
        design
    )

    # STEP 8: Generate SQL with CHECK constraints.
    sql_text = generate_sql(
        artifact_design,
        constraint_rules=rules,
    )

    # STEP 9: Validate generated SQL.
    sql_validation = validate_sql_constraints(
        sql_text,
        rules,
    )

    explicit_rule_count = (
        len(rules["unique"])
        + len(rules["checks"])
        + len(rules["not_null"])
    )

    sql_validation["explicit_rule_count"] = (
        explicit_rule_count
    )

    sql_validation["unresolved_constraints"] = (
        unresolved_constraints
    )

    sql_validation["extracted_constraint_count"] = (
        extraction_info["extracted_constraint_count"]
    )

    sql_validation["mapped_constraint_count"] = (
        extraction_info["mapped_constraint_count"]
    )

    sql_validation["architecture_constraint_count"] = (
        extraction_info["architecture_constraint_count"]
    )

    # --------------------------------------------------------
    # Never approve unresolved extracted constraints.
    # --------------------------------------------------------

    if unresolved_constraints:
        sql_validation["valid"] = False

        for rule in unresolved_constraints:
            sql_validation["errors"].append(
                "Unresolved explicit constraint: "
                + rule.get(
                    "source_requirement",
                    "Unknown source",
                )
                + " ("
                + rule.get("status", "UNMAPPED")
                + ")"
            )

    # --------------------------------------------------------
    # Prevent misleading success if no explicit rules
    # were extracted from supplied architecture constraints.
    #
    # This is a conservative safeguard, not a complete
    # natural-language completeness validator.
    # --------------------------------------------------------

    if (
        extraction_info["architecture_constraint_count"] > 0
        and explicit_rule_count == 0
    ):
        sql_validation["valid"] = False

        sql_validation["errors"].append(
            "Architecture constraints were supplied, "
            "but no explicit UNIQUE, CHECK or NOT NULL "
            "rules were extracted. Manual review is required."
        )

    # Also flag the case where no explicit constraints
    # were checked and no architecture constraints exist.
    # Structural validation remains available.
    if explicit_rule_count == 0:
        sql_validation.setdefault("warnings", [])

        sql_validation["warnings"].append(
            "No explicit business constraints were verified. "
            "Only structural SQL checks were performed."
        )

    print("\nSQL validation details:")
    print("Explicit rules:", explicit_rule_count)
    print(
        "Checked rules:",
        sql_validation.get("checked_rules", 0),
    )
    print(
        "Unresolved constraints:",
        len(unresolved_constraints),
    )
    print(
        "Errors:",
        sql_validation["errors"],
    )

    # STEP 10: Calculate overall validity.
    overall_valid = bool(
        schema_result["valid"]
        and mapping_result["valid"]
        and sql_validation["valid"]
    )

    print(
        "\nSQL constraint validation:",
        sql_validation["valid"],
    )

    print(
        "Overall validation:",
        overall_valid,
    )

    # STEP 11: Save draft artifacts.
    artifacts = {}

    if schema_result["valid"]:
        if output_dir is None:
            output_dir = (
                Path(__file__).resolve().parents[2]
                / "outputs"
                / "database_designs"
                / "artifacts"
            )

        artifacts = save_artifacts(
            design=artifact_design,
            output_dir=output_dir,
            base_name=(
                f"{project.project_id}_database_design"
            ),
            constraint_rules=rules,
        )

    # STEP 12: Return draft and validation report.
    return {
        "project_id": project.project_id,
        "generation_method": generation_method,
        "design": design.model_dump(),
        "schema_validation": schema_result,
        "mapping_validation": mapping_result,
        "sql_constraint_validation": sql_validation,
        "overall_valid": overall_valid,
        "artifacts": artifacts,
    }
