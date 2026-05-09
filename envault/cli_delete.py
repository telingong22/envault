"""CLI commands for deleting keys from a vault."""

from __future__ import annotations

from pathlib import Path

import click

from envault.env_delete import DeleteError, delete_keys


@click.group("delete")
def delete_group() -> None:
    """Delete keys from an encrypted vault."""


@delete_group.command("run")
@click.argument("keys", nargs=-1, required=True)
@click.option(
    "--vault",
    "vault_path",
    default=".env.vault",
    show_default=True,
    help="Path to the vault file.",
)
@click.option(
    "--passphrase",
    envvar="ENVAULT_PASSPHRASE",
    prompt=True,
    hide_input=True,
    help="Master passphrase (or set ENVAULT_PASSPHRASE).",
)
@click.option(
    "--missing-ok",
    is_flag=True,
    default=False,
    help="Do not error if a key does not exist.",
)
def run_cmd(
    keys: tuple,
    vault_path: str,
    passphrase: str,
    missing_ok: bool,
) -> None:
    """Delete one or more KEYS from the vault."""
    try:
        result = delete_keys(
            Path(vault_path),
            list(keys),
            passphrase,
            missing_ok=missing_ok,
        )
    except DeleteError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.deleted:
        click.echo("Deleted keys:")
        for key in result.deleted:
            click.echo(f"  - {key}")
    else:
        click.echo("No keys deleted.")

    if result.not_found:
        click.echo("Keys not found (skipped):")
        for key in result.not_found:
            click.echo(f"  - {key}")
