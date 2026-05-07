"""CLI commands for managing vault key aliases."""

from __future__ import annotations

from pathlib import Path

import click

from envault.alias import AliasError, set_alias, remove_alias, list_aliases, resolve_alias


@click.group("alias")
def alias_group() -> None:
    """Manage friendly aliases for vault keys."""


@alias_group.command("set")
@click.argument("alias")
@click.argument("key")
@click.option(
    "--vault",
    "vault_path",
    default=".env.vault",
    show_default=True,
    help="Path to the vault file.",
)
def set_cmd(alias: str, key: str, vault_path: str) -> None:
    """Map ALIAS to KEY inside the vault."""
    try:
        mapping = set_alias(Path(vault_path), alias, key)
        click.echo(f"Alias '{alias}' -> '{key}' saved.  Total aliases: {len(mapping)}")
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc


@alias_group.command("remove")
@click.argument("alias")
@click.option("--vault", "vault_path", default=".env.vault", show_default=True)
def remove_cmd(alias: str, vault_path: str) -> None:
    """Remove ALIAS from the vault."""
    try:
        remove_alias(Path(vault_path), alias)
        click.echo(f"Alias '{alias}' removed.")
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc


@alias_group.command("list")
@click.option("--vault", "vault_path", default=".env.vault", show_default=True)
def list_cmd(vault_path: str) -> None:
    """List all aliases defined for the vault."""
    try:
        mapping = list_aliases(Path(vault_path))
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc

    if not mapping:
        click.echo("No aliases defined.")
        return

    width = max(len(a) for a in mapping)
    for alias, key in sorted(mapping.items()):
        click.echo(f"  {alias:<{width}}  ->  {key}")


@alias_group.command("resolve")
@click.argument("alias")
@click.option("--vault", "vault_path", default=".env.vault", show_default=True)
def resolve_cmd(alias: str, vault_path: str) -> None:
    """Print the key that ALIAS resolves to."""
    try:
        key = resolve_alias(Path(vault_path), alias)
        click.echo(key)
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc
