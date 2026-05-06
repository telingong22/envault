"""CLI commands for managing vault profiles."""
from __future__ import annotations

from pathlib import Path

import click

from envault.profile import (
    ProfileError,
    create_profile,
    delete_profile,
    get_profile,
    list_profiles,
)


@click.group("profile")
def profile_group() -> None:
    """Manage named key profiles for a vault."""


@profile_group.command("create")
@click.argument("vault", type=click.Path(exists=True))
@click.argument("name")
@click.argument("keys", nargs=-1, required=True)
def create_cmd(vault: str, name: str, keys: tuple) -> None:
    """Create or replace a profile with the specified KEYS."""
    try:
        result = create_profile(Path(vault), name, list(keys))
        click.echo(f"Profile '{name}' saved with keys: {', '.join(result)}")
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc


@profile_group.command("delete")
@click.argument("vault", type=click.Path(exists=True))
@click.argument("name")
def delete_cmd(vault: str, name: str) -> None:
    """Delete a named profile."""
    try:
        delete_profile(Path(vault), name)
        click.echo(f"Profile '{name}' deleted.")
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc


@profile_group.command("show")
@click.argument("vault", type=click.Path(exists=True))
@click.argument("name")
def show_cmd(vault: str, name: str) -> None:
    """Show keys belonging to a profile."""
    try:
        keys = get_profile(Path(vault), name)
        click.echo(f"Profile '{name}':")
        for key in keys:
            click.echo(f"  {key}")
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc


@profile_group.command("list")
@click.argument("vault", type=click.Path(exists=True))
def list_cmd(vault: str) -> None:
    """List all profiles for a vault."""
    profiles = list_profiles(Path(vault))
    if not profiles:
        click.echo("No profiles defined.")
        return
    for name, keys in profiles.items():
        click.echo(f"{name}: {', '.join(keys)}")
