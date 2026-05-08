"""Copy one or more keys from one vault to another."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import Vault


class CopyError(Exception):
    """Raised when a key-copy operation fails."""


@dataclass
class CopyResult:
    source: Path
    destination: Path
    copied: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_skipped(self) -> bool:
        return len(self.skipped) > 0

    def as_dict(self) -> dict:
        return {
            "source": str(self.source),
            "destination": str(self.destination),
            "copied": self.copied,
            "skipped": self.skipped,
        }


def copy_keys(
    src_vault: Path,
    src_passphrase: str,
    dst_vault: Path,
    dst_passphrase: str,
    keys: List[str],
    *,
    overwrite: bool = False,
    env_file: Optional[Path] = None,
) -> CopyResult:
    """Copy *keys* from *src_vault* into *dst_vault*.

    Parameters
    ----------
    src_vault:       Path to the source .vault file.
    src_passphrase:  Passphrase for the source vault.
    dst_vault:       Path to the destination .vault file.
    dst_passphrase:  Passphrase for the destination vault.
    keys:            List of key names to copy.
    overwrite:       When False (default) existing keys in the destination
                     are skipped rather than overwritten.
    env_file:        Temporary .env path used while unlocking vaults.
                     Defaults to a sibling of each vault file.
    """
    src_vault = Path(src_vault)
    dst_vault = Path(dst_vault)

    if not src_vault.exists():
        raise CopyError(f"Source vault not found: {src_vault}")
    if not dst_vault.exists():
        raise CopyError(f"Destination vault not found: {dst_vault}")

    # ── read source ──────────────────────────────────────────────────────────
    src_env = env_file or src_vault.with_suffix(".env")
    src = Vault(src_env, src_vault)
    src_pairs = src.unlock(src_passphrase)

    # parse the returned content (KEY=VALUE lines)
    src_data: dict[str, str] = {}
    for line in src_pairs.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        src_data[k.strip()] = v.strip()

    # ── read destination ─────────────────────────────────────────────────────
    dst_env = env_file or dst_vault.with_suffix(".env")
    dst = Vault(dst_env, dst_vault)
    dst_pairs = dst.unlock(dst_passphrase)

    dst_data: dict[str, str] = {}
    for line in dst_pairs.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        dst_data[k.strip()] = v.strip()

    result = CopyResult(source=src_vault, destination=dst_vault)

    for key in keys:
        if key not in src_data:
            raise CopyError(f"Key '{key}' not found in source vault")
        if key in dst_data and not overwrite:
            result.skipped.append(key)
            continue
        dst_data[key] = src_data[key]
        result.copied.append(key)

    # ── write updated destination ─────────────────────────────────────────────
    new_content = "\n".join(f"{k}={v}" for k, v in dst_data.items()) + "\n"
    dst_env.write_text(new_content)
    dst_locking = Vault(dst_env, dst_vault)
    dst_locking.lock(dst_passphrase)

    return result
