"""Reorder keys in a vault by specifying an explicit key order."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.vault import Vault


class ReorderError(Exception):
    """Raised when reordering fails."""


@dataclass
class ReorderResult:
    vault_path: str
    ordered: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "vault_path": self.vault_path,
            "ordered": self.ordered,
            "unchanged": self.unchanged,
        }


def _reorder_lines(lines: list[str], key_order: list[str]) -> list[str]:
    """Return lines reordered so that keys in *key_order* appear first."""
    keyed: dict[str, list[str]] = {}
    remainder: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=", 1)[0].strip()
            if key in key_order:
                keyed.setdefault(key, []).append(line)
                i += 1
                continue
        remainder.append(line)
        i += 1

    result: list[str] = []
    for key in key_order:
        result.extend(keyed.get(key, []))
    result.extend(remainder)
    return result


def reorder_keys(
    vault_path: str | Path,
    passphrase: str,
    key_order: list[str],
) -> ReorderResult:
    """Reorder keys in *vault_path* according to *key_order*.

    Keys listed in *key_order* are moved to the top of the file in the
    specified sequence.  Keys not mentioned keep their relative order and
    appear after the explicitly ordered keys.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise ReorderError(f"Vault not found: {vault_path}")
    if not key_order:
        raise ReorderError("key_order must contain at least one key")

    v = Vault(vault_path.parent / vault_path.name.replace(".vault", ".env"))
    v.unlock(passphrase, vault_path=vault_path)

    env_path = v.env_path
    original_lines = env_path.read_text().splitlines(keepends=True)

    reordered = _reorder_lines(original_lines, key_order)
    env_path.write_text("".join(reordered))

    # Determine which requested keys were actually present
    present_keys = set()
    for line in original_lines:
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            k = stripped.split("=", 1)[0].strip()
            if k in key_order:
                present_keys.add(k)

    ordered = [k for k in key_order if k in present_keys]
    unchanged = [k for k in key_order if k not in present_keys]

    v.lock(passphrase, vault_path=vault_path)
    return ReorderResult(
        vault_path=str(vault_path),
        ordered=ordered,
        unchanged=unchanged,
    )
