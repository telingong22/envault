"""Profile support — named collections of env-var keys for selective operations."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class ProfileError(Exception):
    """Raised when a profile operation fails."""


def _profiles_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".profiles.json")


def _load_profiles(vault_path: Path) -> Dict[str, List[str]]:
    path = _profiles_path(vault_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_profiles(vault_path: Path, data: Dict[str, List[str]]) -> None:
    _profiles_path(vault_path).write_text(json.dumps(data, indent=2))


def create_profile(vault_path: Path, name: str, keys: List[str]) -> List[str]:
    """Create or replace a named profile with the given list of keys."""
    if not name:
        raise ProfileError("Profile name must not be empty.")
    data = _load_profiles(vault_path)
    data[name] = list(dict.fromkeys(keys))  # deduplicate, preserve order
    _save_profiles(vault_path, data)
    return data[name]


def delete_profile(vault_path: Path, name: str) -> None:
    """Remove a profile by name; raises ProfileError if it does not exist."""
    data = _load_profiles(vault_path)
    if name not in data:
        raise ProfileError(f"Profile '{name}' does not exist.")
    del data[name]
    _save_profiles(vault_path, data)


def get_profile(vault_path: Path, name: str) -> List[str]:
    """Return the key list for a named profile."""
    data = _load_profiles(vault_path)
    if name not in data:
        raise ProfileError(f"Profile '{name}' does not exist.")
    return data[name]


def list_profiles(vault_path: Path) -> Dict[str, List[str]]:
    """Return all profiles stored for *vault_path*."""
    return _load_profiles(vault_path)
