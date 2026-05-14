"""CLI commands for env-mask: mask / unmask / list masked keys."""
from __future__ import annotations

import click

from envault.env_mask import MaskError, list_masked, mask_keys, unmask_keys


@click.group("mask")
def mask_group() -> None:
    """Mask keys so their values are hidden in display output."""


@mask_group.command("add")
@click.argument("vault_path")
@click.argument("keys", nargs=-1, required=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def add_cmd(vault_path: str, keys: tuple, passphrase: str) -> None:
    """Mark one or more KEYS as masked in VAULT_PATH."""
    try:
        result = mask_keys(vault_path, passphrase, list(keys))
        click.echo(f"Masked {len(result.masked)} key(s): {', '.join(result.masked)}")
    except MaskError as exc:
        raise click.ClickException(str(exc)) from exc


@mask_group.command("remove")
@click.argument("vault_path")
@click.argument("keys", nargs=-1, required=True)
@click.option("--passphrase", prompt=True, hide_input=True)
def remove_cmd(vault_path: str, keys: tuple, passphrase: str) -> None:
    """Remove one or more KEYS from the mask list in VAULT_PATH."""
    try:
        result = unmask_keys(vault_path, passphrase, list(keys))
        if result.unmasked:
            click.echo(f"Unmasked {len(result.unmasked)} key(s): {', '.join(result.unmasked)}")
        else:
            click.echo("No matching masked keys found.")
    except MaskError as exc:
        raise click.ClickException(str(exc)) from exc


@mask_group.command("list")
@click.argument("vault_path")
def list_cmd(vault_path: str) -> None:
    """List all masked keys for VAULT_PATH."""
    try:
        keys = list_masked(vault_path)
        if keys:
            for k in keys:
                click.echo(k)
        else:
            click.echo("No masked keys.")
    except MaskError as exc:
        raise click.ClickException(str(exc)) from exc
