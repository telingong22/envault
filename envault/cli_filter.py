"""CLI commands for filtering vault keys."""

from __future__ import annotations

import json
from pathlib import Path

import click

from envault.env_filter import FilterError, filter_keys


@click.group("filter")
def filter_group() -> None:
    """Filter vault keys by glob pattern, prefix, or regex."""


@filter_group.command("run")
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.option("--passphrase", "-p", required=True, envvar="ENVAULT_PASSPHRASE", help="Master passphrase.")
@click.option("--pattern", default=None, help="Glob pattern to match keys (e.g. 'DB_*').")
@click.option("--prefix", default=None, help="Key prefix to match (e.g. 'AWS_').")
@click.option("--regex", default=None, help="Regular expression to match keys.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
@click.option("--values/--no-values", default=False, help="Show values alongside keys.")
def run_cmd(
    vault: Path,
    passphrase: str,
    pattern: str | None,
    prefix: str | None,
    regex: str | None,
    as_json: bool,
    values: bool,
) -> None:
    """Filter and display vault keys matching the given criteria."""
    try:
        result = filter_keys(
            vault,
            passphrase,
            pattern=pattern,
            prefix=prefix,
            regex=regex,
        )
    except FilterError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        data = result.as_dict()
        if not values:
            data["matched"] = list(data["matched"].keys())
        click.echo(json.dumps(data, indent=2))
        return

    click.echo(f"Matched {len(result.matched)} / {result.total_keys} keys")
    for key, value in result.matched.items():
        if values:
            click.echo(f"  {key}={value}")
        else:
            click.echo(f"  {key}")
