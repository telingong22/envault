"""CLI commands for env-value validation."""
from __future__ import annotations

import json
import sys

import click

from envault.env_validate import ValidateError, validate_vault


@click.group("validate")
def validate_group() -> None:
    """Validate env values against rules."""


@validate_group.command("check")
@click.argument("vault_path")
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option(
    "--regex",
    "regex_rules",
    multiple=True,
    metavar="KEY=PATTERN",
    help="KEY=regex pattern",
)
@click.option(
    "--choices",
    "choices_rules",
    multiple=True,
    metavar="KEY=a,b,c",
    help="KEY=comma-separated allowed values",
)
@click.option("--json", "as_json", is_flag=True, default=False)
def check_cmd(
    vault_path: str,
    passphrase: str,
    regex_rules: tuple,
    choices_rules: tuple,
    as_json: bool,
) -> None:
    """Check vault env values satisfy the supplied rules."""
    rules: dict = {}

    for item in regex_rules:
        if "=" not in item:
            click.echo(f"Invalid --regex option: {item!r}", err=True)
            sys.exit(2)
        k, pattern = item.split("=", 1)
        rules.setdefault(k, {})["regex"] = pattern

    for item in choices_rules:
        if "=" not in item:
            click.echo(f"Invalid --choices option: {item!r}", err=True)
            sys.exit(2)
        k, vals = item.split("=", 1)
        rules.setdefault(k, {})["choices"] = [v.strip() for v in vals.split(",")]

    try:
        result = validate_vault(vault_path, passphrase, rules)
    except ValidateError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(result.as_dict(), indent=2))
    else:
        if result.ok:
            click.echo("Validation passed.")
        else:
            click.echo(f"Validation failed: {result.violation_count} violation(s).")
            for v in result.violations:
                click.echo(f"  [{v.rule}] {v.message}")

    sys.exit(0 if result.ok else 1)
