"""
Knowledge Loader – Milestone 3.

Single responsibility: load and parse architecture_knowledge.json into typed
KnowledgeItem dataclasses.  No embedding or retrieval logic here.

The JSON is loaded once at module import and cached in _KNOWLEDGE_ITEMS.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


# ---------------------------------------------------------------------------
# Typed data model
# ---------------------------------------------------------------------------

@dataclass
class KnowledgeItem:
    knowledge_id:        str
    title:               str
    content:             str
    architecture_styles: List[str]
    quality_attributes:  List[str]
    source:              str
    source_type:         str


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

_KB_PATH = Path(__file__).parent.parent / "knowledge" / "architecture_knowledge.json"


def load_knowledge(path: Path | None = None) -> List[KnowledgeItem]:
    """
    Load knowledge items from the JSON file.

    Args:
        path: Optional override path (useful for testing).

    Returns:
        List of KnowledgeItem dataclasses.

    Raises:
        FileNotFoundError: if the knowledge file does not exist.
        KeyError: if a required field is missing from any item.
    """
    resolved = path or _KB_PATH
    with open(resolved, encoding="utf-8") as f:
        data = json.load(f)

    items: List[KnowledgeItem] = []
    for raw in data["knowledge_items"]:
        items.append(
            KnowledgeItem(
                knowledge_id        = raw["knowledge_id"],
                title               = raw["title"],
                content             = raw["content"],
                architecture_styles = raw.get("architecture_styles", []),
                quality_attributes  = raw.get("quality_attributes", []),
                source              = raw.get("source", ""),
                source_type         = raw.get("source_type", ""),
            )
        )
    return items


# ---------------------------------------------------------------------------
# Module-level cache (loaded once)
# ---------------------------------------------------------------------------

_KNOWLEDGE_ITEMS: List[KnowledgeItem] = load_knowledge()


def get_knowledge_items() -> List[KnowledgeItem]:
    """Return the cached knowledge item list."""
    return _KNOWLEDGE_ITEMS
