"""Apply a diff (patch) between two env states to a vault."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envault.vault import Vault
from envault.diff import diff_envs


class ApplyError(Exception):
    """Raised when a diff cannot be applied."""


@dataclass
class ApplyResult:
    vault_path: str
    added: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.added or self.updated or self.removed)

    def as_dict(self) -> dict:
        return {
            "vault_path": self.vault_path,
            "added": self.added,
            "updated": self.updated,
            "removed": self.removed,
            "skipped": self.skipped,
            "has_changes": self.has_changes(),
        }


def apply_diff(
    vault_path: Path,
    passphrase: str,
    target: Dict[str, str],
    *,
    remove_missing: bool = False,
    dry_run: bool = False,
) -> ApplyResult:
    """Apply *target* key/value pairs to the vault, optionally removing keys absent from target.

    Args:
        vault_path: Path to the ``.vault`` file.
        passphrase: Master passphrase for the vault.
        target: Desired final env mapping.
        remove_missing: If ``True``, delete keys present in vault but absent from *target*.
        dry_run: If ``True``, compute the result without writing anything.

    Returns:
        :class:`ApplyResult` describing what changed.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise ApplyError(f"Vault not found: {vault_path}")

    v = Vault(vault_path.with_suffix(".env"), vault_path)
    env_path = vault_path.with_suffix(".env")
    v.unlock(passphrase)

    current: Dict[str, str] = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, val = line.partition("=")
        current[k.strip()] = val.strip()

    result = ApplyResult(vault_path=str(vault_path))

    lines = env_path.read_text().splitlines(keepends=True)
    new_lines = list(lines)

    # Update / add
    for key, value in target.items():
        if key in current:
            if current[key] != value:
                new_lines = [
                    f"{key}={value}\n" if l.startswith(f"{key}=") else l
                    for l in new_lines
                ]
                result.updated.append(key)
        else:
            new_lines.append(f"{key}={value}\n")
            result.added.append(key)

    # Remove
    if remove_missing:
        keys_to_remove = set(current) - set(target)
        new_lines = [l for l in new_lines if not any(l.startswith(f"{k}=") for k in keys_to_remove)]
        result.removed.extend(sorted(keys_to_remove))

    if not dry_run:
        env_path.write_text("".join(new_lines))
        v.lock(passphrase)
        env_path.unlink(missing_ok=True)

    return result
