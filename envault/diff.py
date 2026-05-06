"""Compare two .env files or a .env file against a vault's decrypted contents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.inspector import parse_env
from envault.vault import Vault


@dataclass
class DiffResult:
    added: List[str] = field(default_factory=list)       # keys only in right
    removed: List[str] = field(default_factory=list)     # keys only in left
    changed: List[str] = field(default_factory=list)     # keys in both but different values
    unchanged: List[str] = field(default_factory=list)   # keys identical in both

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = []
        for key in sorted(self.added):
            lines.append(f"+ {key}")
        for key in sorted(self.removed):
            lines.append(f"- {key}")
        for key in sorted(self.changed):
            lines.append(f"~ {key}")
        for key in sorted(self.unchanged):
            lines.append(f"  {key}")
        return "\n".join(lines) if lines else "(no keys)"


def diff_envs(left: Dict[str, str], right: Dict[str, str]) -> DiffResult:
    """Return a DiffResult comparing two parsed env dicts."""
    left_keys = set(left)
    right_keys = set(right)

    result = DiffResult()
    result.added = sorted(right_keys - left_keys)
    result.removed = sorted(left_keys - right_keys)

    for key in left_keys & right_keys:
        if left[key] == right[key]:
            result.unchanged.append(key)
        else:
            result.changed.append(key)

    return result


def diff_files(left_path: str, right_path: str) -> DiffResult:
    """Diff two .env files on disk."""
    with open(left_path, "r") as fh:
        left = parse_env(fh.read())
    with open(right_path, "r") as fh:
        right = parse_env(fh.read())
    return diff_envs(left, right)


def diff_vault(
    env_path: str,
    vault_path: str,
    passphrase: str,
) -> DiffResult:
    """Diff a live .env file against the contents stored in a vault."""
    vault = Vault(vault_path)
    decrypted_text = vault.unlock(passphrase, target_path=None, overwrite=False)
    vault_env = parse_env(decrypted_text)

    with open(env_path, "r") as fh:
        live_env = parse_env(fh.read())

    return diff_envs(vault_env, live_env)
