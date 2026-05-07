"""Vault alias management — assign friendly names to vault file paths."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class AliasError(Exception):
    """Raised when an alias operation fails."""


def _aliases_path(vault_path: Path) -> Path:
    return vault_path.parent / (vault_path.stem + ".aliases.json")


def _load_aliases(vault_path: Path) -> Dict[str, str]:
    p = _aliases_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_aliases(vault_path: Path, data: Dict[str, str]) -> None:
    _aliases_path(vault_path).write_text(json.dumps(data, indent=2))


def set_alias(vault_path: Path, alias: str, key: str) -> Dict[str, str]:
    """Map *alias* to an env *key* inside *vault_path*.

    Returns the full alias mapping after the update.
    """
    alias = alias.strip()
    key = key.strip()
    if not alias:
        raise AliasError("Alias name must not be empty.")
    if not key:
        raise AliasError("Key must not be empty.")
    if not vault_path.exists():
        raise AliasError(f"Vault not found: {vault_path}")

    data = _load_aliases(vault_path)
    data[alias] = key
    _save_aliases(vault_path, data)
    return dict(data)


def remove_alias(vault_path: Path, alias: str) -> Dict[str, str]:
    """Remove *alias* from the mapping.  Raises if the alias does not exist."""
    data = _load_aliases(vault_path)
    if alias not in data:
        raise AliasError(f"Alias '{alias}' not found.")
    del data[alias]
    _save_aliases(vault_path, data)
    return dict(data)


def list_aliases(vault_path: Path) -> Dict[str, str]:
    """Return all aliases defined for *vault_path*."""
    return _load_aliases(vault_path)


def resolve_alias(vault_path: Path, alias: str) -> str:
    """Return the env key that *alias* points to.  Raises if not found."""
    data = _load_aliases(vault_path)
    if alias not in data:
        raise AliasError(f"Alias '{alias}' is not defined.")
    return data[alias]


def aliases_for_key(vault_path: Path, key: str) -> List[str]:
    """Return every alias that maps to *key*."""
    data = _load_aliases(vault_path)
    return [a for a, k in data.items() if k == key]
