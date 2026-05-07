"""CLI commands for managing vault TTL (time-to-live)."""

from __future__ import annotations

import json
from pathlib import Path

import click

from envault.ttl import TTLError, clear_ttl, get_ttl, set_ttl


@click.group("ttl")
def ttl_group() -> None:
    """Manage expiry (TTL) settings for a vault."""


@ttl_group.command("set")
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.argument("seconds", type=float)
@click.option("--note", default="", help="Optional note to attach to the TTL.")
def set_cmd(vault: Path, seconds: float, note: str) -> None:
    """Set a TTL of SECONDS on VAULT."""
    try:
        record = set_ttl(vault, seconds=seconds, note=note)
    except TTLError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        f"TTL set: vault expires at {record.expires_at.isoformat()} "
        f"({record.seconds_remaining:.0f}s remaining)"
    )


@ttl_group.command("status")
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def status_cmd(vault: Path, as_json: bool) -> None:
    """Show TTL status for VAULT."""
    try:
        record = get_ttl(vault)
    except TTLError as exc:
        raise click.ClickException(str(exc)) from exc
    if as_json:
        click.echo(json.dumps(record.as_dict(), indent=2))
    else:
        state = "EXPIRED" if record.expired else "valid"
        click.echo(
            f"Status : {state}\n"
            f"Expires: {record.expires_at.isoformat()}\n"
            f"Remaining: {record.seconds_remaining:.0f}s\n"
            f"Note   : {record.note or '(none)'}" 
        )


@ttl_group.command("clear")
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
def clear_cmd(vault: Path) -> None:
    """Remove the TTL from VAULT."""
    removed = clear_ttl(vault)
    if removed:
        click.echo("TTL cleared.")
    else:
        click.echo("No TTL was set for this vault.")
