"""env_lock.py – per-key locking that prevents specific keys from being
modified or exported until explicitly unlocked.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List


class LockError(Exception):
    """Raised when a key-lock operation fails."""


def _lock_path(vault_path: str | Path) -> Path:
    return Path(vault_path).with_suffix(".keylocks.json")


def _load(vault_path: str | Path) -> dict:
    p = _lock_path(vault_path)
    if not p.exists():
        return {"locked_keys": []}
    return json.loads(p.read_text())


def _save(vault_path: str | Path, data: dict) -> None:
    _lock_path(vault_path).write_text(json.dumps(data, indent=2))


def lock_key(vault_path: str | Path, key: str) -> List[str]:
    """Mark *key* as locked.  Returns the full list of locked keys."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise LockError(f"Vault not found: {vault_path}")
    if not key.strip():
        raise LockError("Key name must not be empty.")
    data = _load(vault_path)
    locked: List[str] = data["locked_keys"]
    if key not in locked:
        locked.append(key)
    data["locked_keys"] = locked
    _save(vault_path, data)
    return list(locked)


def unlock_key(vault_path: str | Path, key: str) -> List[str]:
    """Remove *key* from the locked list.  Returns remaining locked keys."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise LockError(f"Vault not found: {vault_path}")
    data = _load(vault_path)
    locked: List[str] = data["locked_keys"]
    locked = [k for k in locked if k != key]
    data["locked_keys"] = locked
    _save(vault_path, data)
    return list(locked)


def list_locked(vault_path: str | Path) -> List[str]:
    """Return all currently locked keys for *vault_path*."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise LockError(f"Vault not found: {vault_path}")
    return list(_load(vault_path)["locked_keys"])


def is_key_locked(vault_path: str | Path, key: str) -> bool:
    """Return True if *key* is locked in *vault_path*."""
    return key in list_locked(vault_path)
