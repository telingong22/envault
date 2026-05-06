"""CLI commands for linting .env files."""
from __future__ import annotations

from pathlib import Path

import click

from envault.lint import lint_env


@click.group("lint")
def lint_group():
    """Lint .env files for common issues."""


@lint_group.command("check")
@click.argument("env_path", default=".env", metavar="ENV_FILE")
@click.option("--strict", is_flag=True, default=False,
              help="Exit with non-zero status on warnings too.")
def check_cmd(env_path: str, strict: bool):
    """Check ENV_FILE for duplicate keys, empty values, and other issues."""
    result = lint_env(env_path)

    if not result.issues:
        click.secho(f"✔  {env_path}: no issues found.", fg="green")
        raise SystemExit(0)

    for issue in result.issues:
        colour = "red" if issue.level == "error" else "yellow"
        prefix = "ERROR" if issue.level == "error" else "WARN "
        location = f" (line {issue.line})" if issue.line else ""
        click.secho(
            f"  [{prefix}] {issue.code}{location}: {issue.message}",
            fg=colour,
        )

    click.echo(result.summary())

    if not result.ok or (strict and result.warning_count):
        raise SystemExit(1)
    raise SystemExit(0)


@lint_group.command("json")
@click.argument("env_path", default=".env", metavar="ENV_FILE")
def json_cmd(env_path: str):
    """Output lint results as JSON."""
    import json

    result = lint_env(env_path)
    payload = {
        "path": result.path,
        "ok": result.ok,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "issues": [i.as_dict() for i in result.issues],
    }
    click.echo(json.dumps(payload, indent=2))
    raise SystemExit(0 if result.ok else 1)
