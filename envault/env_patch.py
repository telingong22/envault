"""Apply a patch (key=value pairs from a string or file) to an existing vault."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault


class PatchError(Exception):
    """Raised when a patch operation fails."""


@dataclass
class PatchResult:
    vault_path: Path
    applied: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "applied": self.applied,
            "skipped": self.skipped,
        }

    @property
    def has_skipped(self) -> bool:
        return bool(self.skipped)


def _parse_patch_lines(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE lines; ignore blanks and comments."""
    pairs: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            pairs[key] = value
    return pairs


def apply_patch(
    vault_path: Path,
    passphrase: str,
    patch: str | Dict[str, str],
    *,
    keys_only: Optional[List[str]] = None,
    overwrite: bool = True,
) -> PatchResult:
    """Decrypt *vault_path*, merge *patch* into it, and re-encrypt.

    Args:
        vault_path: Path to the ``.vault`` file.
        passphrase: Master passphrase.
        patch: Either a KEY=VALUE string or a pre-parsed dict.
        keys_only: If given, only patch these specific keys.
        overwrite: When False, skip keys that already exist in the vault.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise PatchError(f"Vault not found: {vault_path}")

    pairs: Dict[str, str] = (
        patch if isinstance(patch, dict) else _parse_patch_lines(patch)
    )

    if keys_only is not None:
        pairs = {k: v for k, v in pairs.items() if k in keys_only}

    v = Vault(vault_path.parent / (vault_path.stem.removesuffix(".vault") + ".env"))
    env_text = v.unlock(passphrase, write=False)

    existing: Dict[str, str] = {}
    for line in env_text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, val = line.partition("=")
            existing[k.strip()] = val.strip()

    result = PatchResult(vault_path=vault_path)

    for key, value in pairs.items():
        if not overwrite and key in existing:
            result.skipped.append(key)
        else:
            existing[key] = value
            result.applied.append(key)

    new_env = "\n".join(f"{k}={v}" for k, v in existing.items()) + "\n"

    env_file = v.env_path
    env_file.write_text(new_env)
    v.lock(passphrase)
    env_file.unlink(missing_ok=True)

    return result
