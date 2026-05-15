"""CLI surface for the audit-export feature."""

from __future__ import annotations

from pathlib import Path

import click

from envault.env_audit_export import export_audit, AuditExportError


@click.group("audit-export")
def audit_export_group() -> None:
    """Export the envault audit log."""


@audit_export_group.command("run")
@click.option(
    "--format", "fmt",
    type=click.Choice(["json", "csv", "text"], case_sensitive=False),
    default="json",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--log", "log_path",
    type=click.Path(),
    default=None,
    help="Path to audit log (defaults to envault default location).",
)
@click.option(
    "--output", "output_path",
    type=click.Path(),
    default=None,
    help="Write result to this file instead of stdout.",
)
def run_cmd(fmt: str, log_path: str | None, output_path: str | None) -> None:
    """Export the audit log in the chosen format."""
    try:
        result = export_audit(
            fmt=fmt,
            log_path=Path(log_path) if log_path else None,
            output_path=Path(output_path) if output_path else None,
        )
    except AuditExportError as exc:
        raise click.ClickException(str(exc)) from exc

    if output_path:
        click.echo(f"Audit log exported to {output_path} ({fmt})")
    else:
        click.echo(result)
