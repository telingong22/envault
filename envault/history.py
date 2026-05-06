"""Vault operation history: track lock/unlock/rotate events per vault file."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


class HistoryError(Exception):
    """Raised when history operations fail."""


@dataclass
class HistoryEntry:
    operation: str          # e.g. 'lock', 'unlock', 'rotate'
    vault_path: str
    timestamp: str          # ISO-8601
    extra: dict             # arbitrary metadata

    def as_dict(self) -> dict:
        return asdict(self)


def _history_path(vault_path: Path) -> Path:
    """Return the .history file path alongside the vault file."""
    return vault_path.with_suffix(".history")


def record(vault_path: Path, operation: str, **extra) -> HistoryEntry:
    """Append an operation record to the vault's history file."""
    vault_path = Path(vault_path)
    entry = HistoryEntry(
        operation=operation,
        vault_path=str(vault_path),
        timestamp=datetime.now(timezone.utc).isoformat(),
        extra=extra,
    )
    hist_file = _history_path(vault_path)
    with hist_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.as_dict()) + "\n")
    return entry


def read_history(vault_path: Path) -> List[HistoryEntry]:
    """Return all history entries for *vault_path*, oldest first."""
    hist_file = _history_path(Path(vault_path))
    if not hist_file.exists():
        return []
    entries: List[HistoryEntry] = []
    for line in hist_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        entries.append(
            HistoryEntry(
                operation=data["operation"],
                vault_path=data["vault_path"],
                timestamp=data["timestamp"],
                extra=data.get("extra", {}),
            )
        )
    return entries


def last_operation(vault_path: Path) -> Optional[HistoryEntry]:
    """Return the most recent history entry, or None if no history exists."""
    entries = read_history(vault_path)
    return entries[-1] if entries else None


def clear_history(vault_path: Path) -> int:
    """Delete the history file; return number of entries that were present."""
    hist_file = _history_path(Path(vault_path))
    count = len(read_history(vault_path))
    if hist_file.exists():
        hist_file.unlink()
    return count
