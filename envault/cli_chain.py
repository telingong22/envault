"""CLI surface for env-chain: cascade key lookup across multiple vaults."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import click

from envault.env_chain import ChainError, resolve_key


@click.group("chain")
def chain_group() -> None:
    """Cascade key lookup across an ordered list of vaults."""


@chain_group.command("resolve")
@click.argument("key")
@click.option(
    "--vault",
    "vault_paths",
    multiple=True,
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Vault file to include (repeat to add more, priority left-to-right).",
)
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def resolve_cmd(
    key: str,
    vault_paths: List[Path],
    passphrase: str,
    as_json: bool,
) -> None:
    """Resolve KEY from the first vault in the chain that contains it."""
    try:
        result = resolve_key(key, list(vault_paths), passphrase)
    except ChainError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        click.echo(json.dumps(result.as_dict(), indent=2))
        return

    if result.found:
        click.echo(f"key      : {result.key}")
        click.echo(f"value    : {result.value}")
        click.echo(f"found in : {result.found_in}")
    else:
        click.echo(f"key '{key}' not found in any vault.")
        raise SystemExit(1)
