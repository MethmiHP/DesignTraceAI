def validate_requirement_mapping(requirements, design):
    """
    Validate Gemini-generated requirement-to-table mappings.
    """

    errors = []
    warnings = []

    requirement_ids = {
        req["requirement_id"]
        for req in requirements
    }

    table_names = {
        table["name"]
        for table in design.get("tables", [])
    }

    mappings = design.get("requirement_mapping", [])

    seen_ids = set()
    covered_ids = set()

    for mapping in mappings:
        requirement_id = mapping["requirement_id"]
        related_tables = mapping.get("related_tables", [])

        if requirement_id not in requirement_ids:
            errors.append(
                f"Unknown requirement ID: {requirement_id}"
            )

        if requirement_id in seen_ids:
            errors.append(
                f"Duplicate mapping: {requirement_id}"
            )

        seen_ids.add(requirement_id)

        for table_name in related_tables:
            if table_name not in table_names:
                errors.append(
                    f"Unknown table '{table_name}' "
                    f"in requirement '{requirement_id}'"
                )

        if related_tables and all(
            table in table_names
            for table in related_tables
        ):
            covered_ids.add(requirement_id)

        if not related_tables:
            warnings.append(
                f"Requirement '{requirement_id}' "
                "has no related tables."
            )

    for requirement_id in requirement_ids:
        if requirement_id not in seen_ids:
            errors.append(
                f"Missing mapping for: {requirement_id}"
            )

    total = len(requirement_ids)

    coverage = (
        len(covered_ids) / total * 100
        if total
        else 0.0
    )

    return {
        "valid": len(errors) == 0,
        "coverage_percentage": round(coverage, 2),
        "total_requirements": total,
        "mapped_requirements": len(covered_ids),
        "errors": errors,
        "warnings": warnings,
    }
