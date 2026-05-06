"""Snapshot management for envault — save and restore named vault snapshots."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_SNAPSHOT_DIR = Path(".envault_snapshots")


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshot_dir(base: Optional[Path] = None) -> Path:
    return base or DEFAULT_SNAPSHOT_DIR


def save_snapshot(
    vault_path: Path,
    label: Optional[str] = None,
    snapshot_dir: Optional[Path] = None,
) -> Path:
    """Copy *vault_path* into the snapshot directory and return the snapshot path."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise SnapshotError(f"Vault file not found: {vault_path}")

    sdir = _snapshot_dir(snapshot_dir)
    sdir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = label or vault_path.stem
    snap_name = f"{stem}__{ts}{vault_path.suffix}"
    snap_path = sdir / snap_name

    shutil.copy2(vault_path, snap_path)

    meta_path = sdir / "snapshots.json"
    entries = _load_meta(meta_path)
    entries.append(
        {
            "label": label or stem,
            "vault": str(vault_path),
            "snapshot": str(snap_path),
            "created_at": ts,
        }
    )
    meta_path.write_text(json.dumps(entries, indent=2))
    return snap_path


def list_snapshots(snapshot_dir: Optional[Path] = None) -> List[dict]:
    """Return all recorded snapshot metadata entries."""
    meta_path = _snapshot_dir(snapshot_dir) / "snapshots.json"
    return _load_meta(meta_path)


def restore_snapshot(snapshot_path: Path, target: Path) -> Path:
    """Overwrite *target* with the contents of *snapshot_path*."""
    snapshot_path = Path(snapshot_path)
    if not snapshot_path.exists():
        raise SnapshotError(f"Snapshot not found: {snapshot_path}")
    target = Path(target)
    shutil.copy2(snapshot_path, target)
    return target


def _load_meta(meta_path: Path) -> List[dict]:
    if meta_path.exists():
        return json.loads(meta_path.read_text())
    return []
