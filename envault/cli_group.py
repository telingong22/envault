"""CLI commands for managing key groups."""
import click
from pathlib import Path

from envault.env_group import (
    GroupError,
    add_to_group,
    remove_from_group,
    list_groups,
    delete_group,
)


@click.group("group")
def group_cmd() -> None:
    """Organise vault keys into named groups."""


@group_cmd.command("add")
@click.argument("vault")
@click.argument("group")
@click.argument("keys", nargs=-1, required=True)
def add_cmd(vault: str, group: str, keys: tuple) -> None:
    """Add KEYS to GROUP inside VAULT."""
    try:
        result = add_to_group(vault, group, list(keys))
        click.echo(f"Group '{group}': {', '.join(result)}")
    except GroupError as exc:
        raise click.ClickException(str(exc))


@group_cmd.command("remove")
@click.argument("vault")
@click.argument("group")
@click.argument("keys", nargs=-1, required=True)
def remove_cmd(vault: str, group: str, keys: tuple) -> None:
    """Remove KEYS from GROUP inside VAULT."""
    try:
        remaining = remove_from_group(vault, group, list(keys))
        if remaining:
            click.echo(f"Group '{group}': {', '.join(remaining)}")
        else:
            click.echo(f"Group '{group}' deleted (no keys remaining).")
    except GroupError as exc:
        raise click.ClickException(str(exc))


@group_cmd.command("list")
@click.argument("vault")
def list_cmd(vault: str) -> None:
    """List all groups and their keys for VAULT."""
    groups = list_groups(vault)
    if not groups:
        click.echo("No groups defined.")
        return
    for name, keys in sorted(groups.items()):
        click.echo(f"{name}: {', '.join(keys)}")


@group_cmd.command("delete")
@click.argument("vault")
@click.argument("group")
def delete_cmd(vault: str, group: str) -> None:
    """Delete GROUP from VAULT entirely."""
    try:
        delete_group(vault, group)
        click.echo(f"Group '{group}' deleted.")
    except GroupError as exc:
        raise click.ClickException(str(exc))
