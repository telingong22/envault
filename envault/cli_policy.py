"""CLI commands for envault policy enforcement."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import click

from envault.policy import check_policy, PolicyError


@click.group("policy")
def policy_group() -> None:
    """Enforce naming and value policies on .env files."""


@policy_group.command("check")
@click.argument("env_path", default=".env", type=click.Path())
@click.option("--no-empty", is_flag=True, default=False, help="Disallow empty values.")
@click.option("--min-length", default=None, type=int, help="Minimum value length.")
@click.option("--key-pattern", default=None, type=str, help="Regex pattern keys must match.")
@click.option(
    "--require",
    "required_keys",
    multiple=True,
    help="Keys that must be present (repeatable).",
)
def check_cmd(
    env_path: str,
    no_empty: bool,
    min_length: Optional[int],
    key_pattern: Optional[str],
    required_keys: tuple,
) -> None:
    """Run policy checks against ENV_PATH (default: .env)."""
    try:
        result = check_policy(
            Path(env_path),
            no_empty_values=no_empty,
            min_length=min_length,
            key_pattern=key_pattern,
            required_keys=list(required_keys) or None,
        )
    except PolicyError as exc:
        raise click.ClickException(str(exc))

    click.echo(result.summary())
    if not result.ok:
        raise SystemExit(1)


@policy_group.command("check-json")
@click.argument("env_path", default=".env", type=click.Path())
@click.option("--no-empty", is_flag=True, default=False)
@click.option("--min-length", default=None, type=int)
@click.option("--key-pattern", default=None, type=str)
@click.option("--require", "required_keys", multiple=True)
def json_cmd(
    env_path: str,
    no_empty: bool,
    min_length: Optional[int],
    key_pattern: Optional[str],
    required_keys: tuple,
) -> None:
    """Run policy checks and emit results as JSON."""
    try:
        result = check_policy(
            Path(env_path),
            no_empty_values=no_empty,
            min_length=min_length,
            key_pattern=key_pattern,
            required_keys=list(required_keys) or None,
        )
    except PolicyError as exc:
        raise click.ClickException(str(exc))

    payload = {
        "ok": result.ok,
        "violation_count": len(result.violations),
        "violations": [v.as_dict() for v in result.violations],
    }
    click.echo(json.dumps(payload, indent=2))
    if not result.ok:
        raise SystemExit(1)
