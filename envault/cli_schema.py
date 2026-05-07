"""CLI commands for schema validation."""
from __future__ import annotations

import json
from pathlib import Path

import click

from envault.env_schema import SchemaError, validate


@click.group("schema")
def schema_group() -> None:
    """Validate .env files against a key schema."""


@schema_group.command("check")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.argument("schema_file", type=click.Path(exists=True, path_type=Path))
def check_cmd(env_file: Path, schema_file: Path) -> None:
    """Check ENV_FILE against SCHEMA_FILE and print a human-readable report."""
    try:
        result = validate(env_file, schema_file)
    except SchemaError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())
    if not result.ok:
        raise SystemExit(1)


@schema_group.command("json")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.argument("schema_file", type=click.Path(exists=True, path_type=Path))
def json_cmd(env_file: Path, schema_file: Path) -> None:
    """Check ENV_FILE against SCHEMA_FILE and emit JSON output."""
    try:
        result = validate(env_file, schema_file)
    except SchemaError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(json.dumps(result.as_dict(), indent=2))
    if not result.ok:
        raise SystemExit(1)
