"""CLI commands for reordering keys inside a vault."""
from __future__ import annotations

import json

import click

from envault.env_reorder import ReorderError, reorder_keys


@click.group("reorder")
def reorder_group() -> None:
    """Reorder keys within a vault."""


@reorder_group.command("run")
@click.argument("vault_path")
@click.argument("keys", nargs=-1, required=True)
@click.option("--passphrase", "-p", prompt=True, hide_input=True, help="Master passphrase.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output JSON.")
def run_cmd(vault_path: str, keys: tuple[str, ...], passphrase: str, as_json: bool) -> None:
    """Reorder KEYS to the top of VAULT_PATH.

    Keys are placed at the top of the file in the order given.  Any keys
    not listed retain their original relative order below the reordered
    block.
    """
    try:
        result = reorder_keys(vault_path, passphrase, list(keys))
    except ReorderError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        click.echo(json.dumps(result.as_dict(), indent=2))
        return

    if result.ordered:
        click.echo("Reordered keys: " + ", ".join(result.ordered))
    if result.unchanged:
        click.echo("Keys not found (skipped): " + ", ".join(result.unchanged))
    if not result.ordered:
        click.echo("No keys were reordered.")
