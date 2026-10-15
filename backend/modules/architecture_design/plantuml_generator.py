"""
PlantUML Generator – Milestone 5.

Deterministically transforms a Pydantic-validated HighLevelArchitectureDesign
into a strict PlantUML string. The LLM does NOT generate this string directly.
"""

from __future__ import annotations
import re

from .schemas import HighLevelArchitectureDesign


def sanitize_alias(name: str) -> str:
    """
    Produce a valid PlantUML alias (alphanumeric).
    Example: 'API Gateway' -> 'APIGateway'
    """
    return re.sub(r'[^a-zA-Z0-9]', '', name)


def generate_plantuml(design: HighLevelArchitectureDesign) -> str:
    """
    Deterministically build a PlantUML component diagram.
    
    Args:
        design: Pydantic-validated architecture design structure.
        
    Returns:
        A complete PlantUML string.
    """
    lines = [
        "@startuml",
        f"title High-Level Architecture: {design.style}",
        "skinparam componentStyle uml2",
        ""
    ]

    # Map component_type -> plantuml declaration type
    valid_types = {"database", "queue", "node", "cloud", "actor", "interface"}
    
    # 1. Declare components
    for comp in design.components:
        alias = sanitize_alias(comp.component_id)
        
        # Default to 'component' if type is unrecognized or generic
        ctype = comp.component_type.lower()
        if ctype not in valid_types:
            ctype = "component"
            
        # Add the responsibility as a note or description, but keep it simple
        lines.append(f'{ctype} "{comp.name}" as {alias}')
    
    lines.append("")

    # 2. Declare connections
    # We rely on the guardrails in service.py to ensure source/target IDs are valid
    for conn in design.connections:
        src_alias = sanitize_alias(conn.source)
        dst_alias = sanitize_alias(conn.target)
        
        # Add relationship label
        label = conn.relationship
        if conn.protocol_or_mechanism:
            label += f" [{conn.protocol_or_mechanism}]"
            
        lines.append(f"{src_alias} --> {dst_alias} : {label}")

    lines.append("")
    lines.append("@enduml")
    
    return "\n".join(lines)
