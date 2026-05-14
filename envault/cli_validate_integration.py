"""Integration helpers: register validate group with the main CLI."""
from __future__ import annotations

import click

from envault.cli_validate import validate_group


def register_validate_group(cli: click.Group) -> None:
    """Attach the validate command group to *cli*."""
    cli.add_command(validate_group)


def validate_summary(result) -> str:
    """Return a one-line human-readable summary for a ValidationResult."""
    if result.ok:
        return "Validation passed with no violations."
    parts = [f"Validation failed: {result.violation_count} violation(s)."]
    for v in result.violations:
        parts.append(f"  [{v.rule}] {v.message}")
    return "\n".join(parts)
