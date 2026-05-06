"""Merge two .env vault files, resolving key conflicts by strategy."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Dict, Tuple

from envault.vault import Vault


class MergeStrategy(str, Enum):
    OURS = "ours"       # keep value from base vault on conflict
    THEIRS = "theirs"   # take value from other vault on conflict
    UNION = "union"     # keep all keys; conflicts favour OURS


class MergeError(Exception):
    """Raised when a merge cannot be completed."""


class MergeResult:
    def __init__(
        self,
        merged: Dict[str, str],
        added: list[str],
        removed: list[str],
        conflicted: list[str],
    ) -> None:
        self.merged = merged
        self.added = added
        self.removed = removed
        self.conflicted = conflicted

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicted) > 0

    def summary(self) -> str:
        lines = [
            f"Added   : {len(self.added)}",
            f"Removed : {len(self.removed)}",
            f"Conflicts: {len(self.conflicted)}",
        ]
        return "\n".join(lines)


def _parse_vault(vault_path: Path, passphrase: str) -> Dict[str, str]:
    v = Vault(vault_path)
    if not v.is_locked():
        raise MergeError(f"Vault is not locked: {vault_path}")
    tmp = vault_path.parent / f".merge_tmp_{vault_path.name}.env"
    try:
        v.unlock(passphrase, env_path=tmp)
        pairs: Dict[str, str] = {}
        for line in tmp.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, val = line.partition("=")
            pairs[k.strip()] = val.strip()
        return pairs
    finally:
        if tmp.exists():
            tmp.unlink()


def merge_vaults(
    base_vault: Path,
    other_vault: Path,
    base_passphrase: str,
    other_passphrase: str,
    output_env: Path,
    strategy: MergeStrategy = MergeStrategy.OURS,
) -> MergeResult:
    """Merge *other_vault* into *base_vault* and write a plain .env to *output_env*."""
    base = _parse_vault(base_vault, base_passphrase)
    other = _parse_vault(other_vault, other_passphrase)

    all_keys = set(base) | set(other)
    added: list[str] = [k for k in other if k not in base]
    removed: list[str] = [k for k in base if k not in other]
    conflicted: list[str] = [
        k for k in base if k in other and base[k] != other[k]
    ]

    merged: Dict[str, str] = {}
    for key in sorted(all_keys):
        if key in base and key in other:
            merged[key] = other[key] if strategy == MergeStrategy.THEIRS else base[key]
        elif key in base:
            if strategy != MergeStrategy.THEIRS:
                merged[key] = base[key]
        else:
            merged[key] = other[key]

    lines = [f"{k}={v}" for k, v in merged.items()]
    output_env.write_text("\n".join(lines) + "\n")

    return MergeResult(
        merged=merged,
        added=added,
        removed=removed,
        conflicted=conflicted,
    )
