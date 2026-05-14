"""Compute statistics and summary metrics about a vault's environment variables."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envault.vault import Vault


class StatsError(Exception):
    """Raised when stats cannot be computed."""


@dataclass
class StatsResult:
    vault_path: str
    total_keys: int
    empty_values: List[str] = field(default_factory=list)
    commented_lines: int = 0
    blank_lines: int = 0
    duplicate_keys: List[str] = field(default_factory=list)
    longest_key: str = ""
    longest_value_key: str = ""

    @property
    def empty_count(self) -> int:
        return len(self.empty_values)

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicate_keys)

    def as_dict(self) -> Dict:
        return {
            "vault_path": self.vault_path,
            "total_keys": self.total_keys,
            "empty_count": self.empty_count,
            "empty_values": self.empty_values,
            "commented_lines": self.commented_lines,
            "blank_lines": self.blank_lines,
            "duplicate_count": self.duplicate_count,
            "duplicate_keys": self.duplicate_keys,
            "longest_key": self.longest_key,
            "longest_value_key": self.longest_value_key,
        }


def compute_stats(vault_path: str | Path, passphrase: str) -> StatsResult:
    """Unlock *vault_path* and return a StatsResult describing its contents."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise StatsError(f"Vault not found: {vault_path}")

    v = Vault(vault_path.parent / vault_path.name.replace(".vault", ".env"))
    try:
        content = v.unlock(passphrase, write=False)
    except Exception as exc:
        raise StatsError(f"Could not unlock vault: {exc}") from exc

    lines = content.splitlines()
    seen_keys: Dict[str, int] = {}
    empty: List[str] = []
    commented = 0
    blank = 0
    longest_key = ""
    longest_value_key = ""
    longest_value_len = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank += 1
            continue
        if stripped.startswith("#"):
            commented += 1
            continue
        match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)', stripped)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip('"\'')
        seen_keys[key] = seen_keys.get(key, 0) + 1
        if not value:
            empty.append(key)
        if len(key) > len(longest_key):
            longest_key = key
        if len(value) > longest_value_len:
            longest_value_len = len(value)
            longest_value_key = key

    duplicates = [k for k, count in seen_keys.items() if count > 1]

    return StatsResult(
        vault_path=str(vault_path),
        total_keys=len(seen_keys),
        empty_values=empty,
        commented_lines=commented,
        blank_lines=blank,
        duplicate_keys=duplicates,
        longest_key=longest_key,
        longest_value_key=longest_value_key,
    )
