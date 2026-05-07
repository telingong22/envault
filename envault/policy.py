"""Policy enforcement for vault secrets — define and validate rules on .env keys/values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.inspector import parse_env


class PolicyError(Exception):
    """Raised when a policy cannot be loaded or applied."""


@dataclass
class PolicyViolation:
    key: str
    rule: str
    message: str

    def as_dict(self) -> dict:
        return {"key": self.key, "rule": self.rule, "message": self.message}


@dataclass
class PolicyResult:
    violations: List[PolicyViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.ok:
            return "All policy checks passed."
        lines = [f"{len(self.violations)} policy violation(s):"]
        for v in self.violations:
            lines.append(f"  [{v.rule}] {v.key}: {v.message}")
        return "\n".join(lines)


# Built-in rule implementations

def _check_no_empty_values(pairs: dict) -> List[PolicyViolation]:
    return [
        PolicyViolation(k, "no_empty_values", "Value must not be empty.")
        for k, v in pairs.items() if v == ""
    ]


def _check_min_length(pairs: dict, length: int) -> List[PolicyViolation]:
    return [
        PolicyViolation(k, "min_length", f"Value must be at least {length} characters.")
        for k, v in pairs.items() if len(v) < length
    ]


def _check_key_pattern(pairs: dict, pattern: str) -> List[PolicyViolation]:
    regex = re.compile(pattern)
    return [
        PolicyViolation(k, "key_pattern", f"Key does not match pattern '{pattern}'.")
        for k in pairs if not regex.fullmatch(k)
    ]


def _check_required_keys(pairs: dict, keys: List[str]) -> List[PolicyViolation]:
    return [
        PolicyViolation(k, "required_keys", "Required key is missing.")
        for k in keys if k not in pairs
    ]


def check_policy(
    env_path: Path,
    *,
    no_empty_values: bool = False,
    min_length: Optional[int] = None,
    key_pattern: Optional[str] = None,
    required_keys: Optional[List[str]] = None,
) -> PolicyResult:
    """Run policy checks against a plain .env file and return a PolicyResult."""
    if not env_path.exists():
        raise PolicyError(f"Env file not found: {env_path}")

    pairs = parse_env(env_path)
    violations: List[PolicyViolation] = []

    if no_empty_values:
        violations.extend(_check_no_empty_values(pairs))
    if min_length is not None:
        violations.extend(_check_min_length(pairs, min_length))
    if key_pattern is not None:
        violations.extend(_check_key_pattern(pairs, key_pattern))
    if required_keys:
        violations.extend(_check_required_keys(pairs, required_keys))

    return PolicyResult(violations=violations)
