"""Group vault keys into named logical sets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class GroupError(Exception):
    """Raised when a group operation fails."""


def _groups_path(vault_path: str | Path) -> Path:
    return Path(vault_path).with_suffix(".groups.json")


def _load_groups(vault_path: str | Path) -> Dict[str, List[str]]:
    p = _groups_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_groups(vault_path: str | Path, groups: Dict[str, List[str]]) -> None:
    _groups_path(vault_path).write_text(json.dumps(groups, indent=2))


def add_to_group(vault_path: str | Path, group: str, keys: List[str]) -> List[str]:
    """Add *keys* to *group*, creating the group if necessary."""
    if not group:
        raise GroupError("Group name must not be empty.")
    if not keys:
        raise GroupError("At least one key must be provided.")
    groups = _load_groups(vault_path)
    existing = set(groups.get(group, []))
    existing.update(keys)
    groups[group] = sorted(existing)
    _save_groups(vault_path, groups)
    return groups[group]


def remove_from_group(vault_path: str | Path, group: str, keys: List[str]) -> List[str]:
    """Remove *keys* from *group*. Returns remaining keys."""
    groups = _load_groups(vault_path)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    remaining = [k for k in groups[group] if k not in keys]
    if remaining:
        groups[group] = remaining
    else:
        del groups[group]
    _save_groups(vault_path, groups)
    return remaining


def list_groups(vault_path: str | Path) -> Dict[str, List[str]]:
    """Return all groups and their keys."""
    return _load_groups(vault_path)


def delete_group(vault_path: str | Path, group: str) -> None:
    """Delete an entire group."""
    groups = _load_groups(vault_path)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    del groups[group]
    _save_groups(vault_path, groups)
