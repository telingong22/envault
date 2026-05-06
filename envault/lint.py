"""Lint .env files for common issues: duplicates, empty values, suspicious keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.inspector import parse_env


@dataclass
class LintIssue:
    level: str        # 'warning' | 'error'
    code: str         # short machine-readable code
    message: str
    line: int | None = None

    def as_dict(self) -> dict:
        return {"level": self.level, "code": self.code,
                "message": self.message, "line": self.line}


@dataclass
class LintResult:
    path: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "warning")

    def summary(self) -> str:
        return (
            f"{self.path}: {self.error_count} error(s), "
            f"{self.warning_count} warning(s)"
        )


def lint_env(env_path: str | Path) -> LintResult:
    """Analyse *env_path* and return a :class:`LintResult`."""
    path = Path(env_path)
    result = LintResult(path=str(path))

    if not path.exists():
        result.issues.append(
            LintIssue(level="error", code="FILE_NOT_FOUND",
                      message=f"File not found: {path}")
        )
        return result

    raw_lines = path.read_text().splitlines()
    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            result.issues.append(LintIssue(
                level="warning", code="NO_EQUALS",
                message=f"Line {lineno} has no '=' sign: {stripped!r}",
                line=lineno,
            ))
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()

        if key in seen_keys:
            result.issues.append(LintIssue(
                level="error", code="DUPLICATE_KEY",
                message=f"Duplicate key '{key}' (first seen on line {seen_keys[key]})",
                line=lineno,
            ))
        else:
            seen_keys[key] = lineno

        if value == "":
            result.issues.append(LintIssue(
                level="warning", code="EMPTY_VALUE",
                message=f"Key '{key}' has an empty value",
                line=lineno,
            ))

        if any(c in key for c in (" ", "-", ".")):
            result.issues.append(LintIssue(
                level="warning", code="INVALID_KEY_CHARS",
                message=f"Key '{key}' contains characters that may cause shell issues",
                line=lineno,
            ))

    return result
