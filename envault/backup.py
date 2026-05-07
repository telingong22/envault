"""Automatic backup management for vault files."""
from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

_BACKUP_SUFFIX = ".bak"
_TIMESTAMP_FMT = "%Y%m%d_%H%M%S"


class BackupError(Exception):
    """Raised when a backup operation fails."""


@dataclass
class BackupEntry:
    path: Path
    vault_path: Path
    timestamp: str

    def as_dict(self) -> dict:
        return {
            "path": str(self.path),
            "vault_path": str(self.vault_path),
            "timestamp": self.timestamp,
        }


def _backup_dir(vault_path: Path) -> Path:
    return vault_path.parent / ".envault_backups"


def create_backup(vault_path: Path) -> BackupEntry:
    """Copy *vault_path* into the backup directory with a timestamp suffix."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise BackupError(f"Vault not found: {vault_path}")

    bak_dir = _backup_dir(vault_path)
    bak_dir.mkdir(parents=True, exist_ok=True)

    ts = time.strftime(_TIMESTAMP_FMT)
    stem = vault_path.stem
    dest = bak_dir / f"{stem}_{ts}{_BACKUP_SUFFIX}"
    shutil.copy2(vault_path, dest)
    return BackupEntry(path=dest, vault_path=vault_path, timestamp=ts)


def list_backups(vault_path: Path) -> List[BackupEntry]:
    """Return all backups for *vault_path*, newest first."""
    vault_path = Path(vault_path)
    bak_dir = _backup_dir(vault_path)
    if not bak_dir.exists():
        return []

    stem = vault_path.stem
    entries = []
    for p in sorted(bak_dir.glob(f"{stem}_*{_BACKUP_SUFFIX}"), reverse=True):
        ts = p.stem.replace(f"{stem}_", "", 1)
        entries.append(BackupEntry(path=p, vault_path=vault_path, timestamp=ts))
    return entries


def restore_backup(backup_path: Path, vault_path: Path) -> Path:
    """Overwrite *vault_path* with the contents of *backup_path*."""
    backup_path = Path(backup_path)
    vault_path = Path(vault_path)
    if not backup_path.exists():
        raise BackupError(f"Backup not found: {backup_path}")
    shutil.copy2(backup_path, vault_path)
    return vault_path


def prune_backups(vault_path: Path, keep: int = 5) -> List[Path]:
    """Delete old backups, keeping the *keep* most recent. Returns deleted paths."""
    if keep < 1:
        raise BackupError("keep must be >= 1")
    entries = list_backups(vault_path)
    to_delete = entries[keep:]
    removed = []
    for entry in to_delete:
        entry.path.unlink(missing_ok=True)
        removed.append(entry.path)
    return removed
