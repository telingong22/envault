"""Validate env values against simple rules (regex, choices, range)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from envault.vault import Vault
from envault.inspector import parse_env


class ValidateError(Exception):
    """Raised when validation cannot be performed."""


@dataclass
class ValidationViolation:
    key: str
    rule: str
    message: str

    def as_dict(self) -> dict:
        return {"key": self.key, "rule": self.rule, "message": self.message}


@dataclass
class ValidationResult:
    vault_path: str
    violations: list[ValidationViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def as_dict(self) -> dict:
        return {
            "vault_path": self.vault_path,
            "ok": self.ok,
            "violation_count": self.violation_count,
            "violations": [v.as_dict() for v in self.violations],
        }


def _check_rule(key: str, value: str, rule_name: str, rule_value: Any) -> ValidationViolation | None:
    if rule_name == "regex":
        if not re.fullmatch(rule_value, value):
            return ValidationViolation(key, "regex", f"{key!r} does not match pattern {rule_value!r}")
    elif rule_name == "choices":
        if value not in rule_value:
            return ValidationViolation(key, "choices", f"{key!r} value {value!r} not in allowed choices")
    elif rule_name == "min_length":
        if len(value) < int(rule_value):
            return ValidationViolation(key, "min_length", f"{key!r} too short (min {rule_value})")
    elif rule_name == "max_length":
        if len(value) > int(rule_value):
            return ValidationViolation(key, "max_length", f"{key!r} too long (max {rule_value})")
    elif rule_name == "required":
        if rule_value and not value.strip():
            return ValidationViolation(key, "required", f"{key!r} is required but empty")
    return None


def validate_vault(
    vault_path: str | Path,
    passphrase: str,
    rules: dict[str, dict[str, Any]],
) -> ValidationResult:
    """Validate decrypted env values against *rules*.

    *rules* maps key names to a dict of rule_name -> rule_value.
    Keys not present in *rules* are ignored.
    """
    vp = Path(vault_path)
    if not vp.exists():
        raise ValidateError(f"Vault not found: {vp}")
    v = Vault(vp.parent / vp.name.replace(".vault", ".env"))
    v.unlock(passphrase, vault_path=str(vp))
    env = parse_env(v.env_path)
    result = ValidationResult(vault_path=str(vp))
    for key, key_rules in rules.items():
        value = env.get(key, "")
        for rule_name, rule_value in key_rules.items():
            violation = _check_rule(key, value, rule_name, rule_value)
            if violation:
                result.violations.append(violation)
    return result
