"""CLI commands for comparing two vault files."""
from __future__ import annotations

import json
from pathlib import Path

import click

from envault.compare import CompareError, compare_vaults


@click.group("compare")
def compare_group() -> None:
    """Compare two encrypted vault files."""


@compare_group.command("run")
@click.argument("vault_a", type=click.Path(exists=True, path_type=Path))
@click.argument("vault_b", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--passphrase",
    "-p",
    prompt=True,
    hide_input=True,
    help="Passphrase for both vaults (or vault A if --passphrase-b is given).",
)
@click.option(
    "--passphrase-b",
    default=None,
    hide_input=True,
    help="Separate passphrase for vault B.",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def run_cmd(
    vault_a: Path,
    vault_b: Path,
    passphrase: str,
    passphrase_b: str | None,
    as_json: bool,
) -> None:
    """Compare VAULT_A against VAULT_B and print differences."""
    try:
        result = compare_vaults(vault_a, vault_b, passphrase, passphrase_b)
    except CompareError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        click.echo(json.dumps(result.as_dict(), indent=2))
        return

    if result.has_differences:
        click.echo(f"Comparing {vault_a.name}  vs  {vault_b.name}")
        click.echo(result.summary())
    else:
        click.echo("Vaults are identical.")
