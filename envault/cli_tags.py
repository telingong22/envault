"""CLI commands for tag management."""

from __future__ import annotations

from pathlib import Path

import click

from envault.tags import TagError, add_tag, find_vaults_by_tag, list_tags, remove_tag


@click.group("tags")
def tags_group() -> None:
    """Manage tags on vault files."""


@tags_group.command("add")
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.argument("tag")
def add_cmd(vault: Path, tag: str) -> None:
    """Add TAG to VAULT."""
    try:
        updated = add_tag(vault, tag)
        click.echo(f"Tags for {vault.name}: {', '.join(updated)}")
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc


@tags_group.command("remove")
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.argument("tag")
def remove_cmd(vault: Path, tag: str) -> None:
    """Remove TAG from VAULT."""
    try:
        updated = remove_tag(vault, tag)
        remaining = ", ".join(updated) if updated else "(none)"
        click.echo(f"Tags for {vault.name}: {remaining}")
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc


@tags_group.command("list")
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
def list_cmd(vault: Path) -> None:
    """List tags on VAULT."""
    try:
        tags = list_tags(vault)
        if tags:
            click.echo("\n".join(tags))
        else:
            click.echo("No tags.")
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc


@tags_group.command("find")
@click.argument("tag")
@click.option(
    "--dir",
    "directory",
    default=".",
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory to search.",
)
def find_cmd(tag: str, directory: Path) -> None:
    """Find vaults in DIRECTORY that carry TAG."""
    matches = find_vaults_by_tag(directory, tag)
    if matches:
        for p in matches:
            click.echo(str(p))
    else:
        click.echo("No matching vaults found.")
