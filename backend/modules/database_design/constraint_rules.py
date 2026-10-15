"""
Common constraint definitions for DesignTrace AI.

"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConstraintRules:
    unique: list[dict[str, Any]] = field(default_factory=list)
    checks: list[dict[str, Any]] = field(default_factory=list)
    foreign_keys: list[dict[str, Any]] = field(default_factory=list)
    primary_keys: list[dict[str, Any]] = field(default_factory=list)
    not_null: list[dict[str, Any]] = field(default_factory=list)
    identity: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            unique=data.get("unique", []),
            checks=data.get("checks", []),
            foreign_keys=data.get("foreign_keys", []),
            primary_keys=data.get("primary_keys", []),
            not_null=data.get("not_null", []),
            identity=data.get("identity", []),
        )

    def to_dict(self):
        return {
            "unique": self.unique,
            "checks": self.checks,
            "foreign_keys": self.foreign_keys,
            "primary_keys": self.primary_keys,
            "not_null": self.not_null,
            "identity": self.identity,
        }