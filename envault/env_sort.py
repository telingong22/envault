"""Sort keys in an env vault alphabetically or by a custom order."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import Vault


class SortError(Exception):
    """Raised when sorting fails."""


@dataclass
class SortResult:
    vault_path: Path
    original_order: List[str]
    sorted_order: List[str]
    changed: bool

    def as_dict(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "original_order": self.original_order,
            "sorted_order": self.sorted_order,
            "changed": self.changed,
        }


def _parse_lines(text: str):
    """Return list of (key_or_none, raw_line) tuples preserving comments/blanks."""
    result = []
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("#") or stripped == "":
            result.append((None, line))
        elif "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            result.append((key, line))
        else:
            result.append((None, line))
    return result


def sort_keys(
    vault_path: Path,
    passphrase: str,
    *,
    reverse: bool = False,
    key_order: Optional[List[str]] = None,
) -> SortResult:
    """Sort env keys inside *vault_path* and re-lock the vault.

    Args:
        vault_path: Path to the ``.vault`` file.
        passphrase: Master passphrase used to unlock/re-lock the vault.
        reverse: If ``True`` sort descending (ignored when *key_order* given).
        key_order: Explicit ordered list of keys; unmentioned keys are appended
                   alphabetically after the explicit ones.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise SortError(f"Vault not found: {vault_path}")

    v = Vault(vault_path.with_suffix(""), passphrase=passphrase)
    env_path = v.unlock(vault_path=vault_path)

    text = Path(env_path).read_text()
    parsed = _parse_lines(text)

    key_lines = [(k, ln) for k, ln in parsed if k is not None]
    non_key_lines = [(k, ln) for k, ln in parsed if k is None]

    original_order = [k for k, _ in key_lines]

    if key_order:
        order_index = {k: i for i, k in enumerate(key_order)}
        key_lines.sort(
            key=lambda t: (order_index.get(t[0], len(key_order)), t[0])
        )
    else:
        key_lines.sort(key=lambda t: t[0], reverse=reverse)

    sorted_order = [k for k, _ in key_lines]
    changed = original_order != sorted_order

    sorted_text = "".join(ln for _, ln in key_lines)
    if non_key_lines:
        trailing = "".join(ln for _, ln in non_key_lines if ln.strip() == "")
        sorted_text = sorted_text.rstrip("\n") + ("\n" if trailing else "")

    Path(env_path).write_text(sorted_text)
    v.lock(env_path=env_path, vault_path=vault_path)

    return SortResult(
        vault_path=vault_path,
        original_order=original_order,
        sorted_order=sorted_order,
        changed=changed,
    )
