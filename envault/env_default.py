"""Apply default values to missing keys in a vault."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envault.vault import Vault


class DefaultError(Exception):
    """Raised when applying defaults fails."""


@dataclass
class DefaultResult:
    vault_path: Path
    applied: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.applied)

    def as_dict(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "applied": self.applied,
            "skipped": self.skipped,
        }


def _parse_env_lines(lines: List[str]) -> Dict[str, str]:
    pairs: Dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        pairs[key.strip()] = value.strip()
    return pairs


def apply_defaults(
    vault_path: Path,
    passphrase: str,
    defaults: Dict[str, str],
) -> DefaultResult:
    """Write *defaults* into the vault only for keys that are not already set.

    Parameters
    ----------
    vault_path:  Path to the ``.vault`` file.
    passphrase:  Master passphrase used to lock/unlock the vault.
    defaults:    Mapping of key → default value to apply when absent.

    Returns
    -------
    DefaultResult with lists of applied and skipped keys.
    """
    if not vault_path.exists():
        raise DefaultError(f"Vault not found: {vault_path}")
    if not defaults:
        raise DefaultError("No defaults provided.")

    result = DefaultResult(vault_path=vault_path)

    vault = Vault(vault_path)
    env_path = vault_path.with_suffix(".env")
    vault.unlock(passphrase, env_path)

    raw_lines = env_path.read_text().splitlines(keepends=True)
    existing = _parse_env_lines(raw_lines)

    new_lines = list(raw_lines)
    for key, value in defaults.items():
        if key in existing:
            result.skipped.append(key)
        else:
            new_lines.append(f"{key}={value}\n")
            result.applied.append(key)

    env_path.write_text("".join(new_lines))
    vault.lock(passphrase, env_path)
    env_path.unlink(missing_ok=True)

    return result
