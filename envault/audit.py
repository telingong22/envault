"""Audit log for vault operations — records lock/unlock events with timestamps."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

AUDIT_LOG_FILENAME = ".envault_audit.json"


def _default_log_path(env_path: str | Path) -> Path:
    """Return audit log path adjacent to the given .env file."""
    return Path(env_path).parent / AUDIT_LOG_FILENAME


def record_event(
    action: str,
    env_path: str | Path,
    vault_path: str | Path,
    log_path: str | Path | None = None,
    success: bool = True,
    detail: str = "",
) -> Dict[str, Any]:
    """Append a single audit event to the JSON log and return the event dict."""
    log_path = Path(log_path) if log_path else _default_log_path(env_path)

    entry: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "env_path": os.fspath(env_path),
        "vault_path": os.fspath(vault_path),
        "success": success,
    }
    if detail:
        entry["detail"] = detail

    events = read_log(log_path)
    events.append(entry)

    log_path.write_text(json.dumps(events, indent=2), encoding="utf-8")
    return entry


def read_log(log_path: str | Path) -> List[Dict[str, Any]]:
    """Read and return all audit events from *log_path* (empty list if missing)."""
    path = Path(log_path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def last_event(
    log_path: str | Path, action: str | None = None
) -> Dict[str, Any] | None:
    """Return the most recent event, optionally filtered by *action*."""
    events = read_log(log_path)
    if action:
        events = [e for e in events if e.get("action") == action]
    return events[-1] if events else None
