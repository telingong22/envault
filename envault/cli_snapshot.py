"""CLI commands for snapshot management, registered onto the main cli group."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from envault.snapshot import SnapshotError, list_snapshots, restore_snapshot, save_snapshot

DEFAULT_VAULT = ".env.vault"
DEFAULT_SNAP_DIR = ".envault_snapshots"


@click.group("snapshot")
def snapshot_group() -> None:
    """Manage vault snapshots."""


@snapshot_group.command("save")
@click.argument("vault", default=DEFAULT_VAULT, type=click.Path())
@click.option("--label", "-l", default=None, help="Human-readable label for the snapshot.")
@click.option(
    "--snapshot-dir",
    default=DEFAULT_SNAP_DIR,
    show_default=True,
    type=click.Path(),
    help="Directory to store snapshots.",
)
def save_cmd(vault: str, label: Optional[str], snapshot_dir: str) -> None:
    """Save a snapshot of VAULT."""
    try:
        snap = save_snapshot(Path(vault), label=label, snapshot_dir=Path(snapshot_dir))
        click.echo(f"Snapshot saved: {snap}")
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc


@snapshot_group.command("list")
@click.option(
    "--snapshot-dir",
    default=DEFAULT_SNAP_DIR,
    show_default=True,
    type=click.Path(),
)
def list_cmd(snapshot_dir: str) -> None:
    """List all saved snapshots."""
    entries = list_snapshots(snapshot_dir=Path(snapshot_dir))
    if not entries:
        click.echo("No snapshots found.")
        return
    for entry in entries:
        click.echo(f"[{entry['created_at']}] {entry['label']}  →  {entry['snapshot']}")


@snapshot_group.command("restore")
@click.argument("snapshot", type=click.Path(exists=True))
@click.argument("target", default=DEFAULT_VAULT, type=click.Path())
def restore_cmd(snapshot: str, target: str) -> None:
    """Restore SNAPSHOT over TARGET vault file."""
    try:
        out = restore_snapshot(Path(snapshot), Path(target))
        click.echo(f"Restored {snapshot} → {out}")
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc
