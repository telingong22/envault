"""Schema validation for .env files — check keys against a required/optional spec."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.inspector import parse_env


class SchemaError(Exception):
    """Raised when schema operations fail."""


@dataclass
class SchemaViolation:
    key: str
    message: str

    def as_dict(self) -> dict:
        return {"key": self.key, "message": self.message}


@dataclass
class SchemaResult:
    violations: List[SchemaViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def summary(self) -> str:
        if self.ok:
            return "Schema validation passed."
        lines = [f"Schema validation failed ({self.violation_count} violation(s)):"]
        for v in self.violations:
            lines.append(f"  [{v.key}] {v.message}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "violation_count": self.violation_count,
            "violations": [v.as_dict() for v in self.violations],
        }


def _load_schema(schema_path: Path) -> dict:
    try:
        raw = json.loads(schema_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaError(f"Cannot read schema file: {exc}") from exc
    if not isinstance(raw, dict):
        raise SchemaError("Schema must be a JSON object.")
    return raw


def validate(env_path: Path, schema_path: Path) -> SchemaResult:
    """Validate *env_path* against a JSON schema file.

    Schema format::

        {
            "required": ["DB_URL", "SECRET_KEY"],
            "optional": ["DEBUG", "PORT"],
            "no_empty": true
        }

    Keys not listed in required or optional are flagged as unknown when
    ``allow_extra`` is absent / false.
    """
    if not env_path.exists():
        raise SchemaError(f"Env file not found: {env_path}")

    schema = _load_schema(schema_path)
    required: list = schema.get("required", [])
    optional: list = schema.get("optional", [])
    no_empty: bool = schema.get("no_empty", False)
    allow_extra: bool = schema.get("allow_extra", True)

    env = parse_env(env_path)
    violations: List[SchemaViolation] = []

    for key in required:
        if key not in env:
            violations.append(SchemaViolation(key=key, message="required key is missing"))

    if no_empty:
        for key, value in env.items():
            if value == "":
                violations.append(SchemaViolation(key=key, message="value must not be empty"))

    if not allow_extra:
        known = set(required) | set(optional)
        for key in env:
            if key not in known:
                violations.append(SchemaViolation(key=key, message="unknown key not in schema"))

    return SchemaResult(violations=violations)
