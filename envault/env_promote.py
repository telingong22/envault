"""Promote keys from one vault (e.g. staging) into another (e.g. production)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import Vault


class PromoteError(Exception):
    """Raised when promotion fails."""


@dataclass
class PromoteResult:
    vault_path: str
    source_path: str
    promoted: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)

    def has_skipped(self) -> bool:
        return len(self.skipped) > 0

    def as_dict(self) -> dict:
        return {
            "vault_path": self.vault_path,
            "source_path": self.source_path,
            "promoted": self.promoted,
            "skipped": self.skipped,
            "overwritten": self.overwritten,
        }


def promote_keys(
    source_vault: Path,
    source_passphrase: str,
    target_vault: Path,
    target_passphrase: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> PromoteResult:
    """Copy selected keys (or all) from *source_vault* into *target_vault*.

    Args:
        source_vault: Path to the source .vault file.
        source_passphrase: Passphrase for the source vault.
        target_vault: Path to the target .vault file.
        target_passphrase: Passphrase for the target vault.
        keys: Explicit list of key names to promote; *None* means all keys.
        overwrite: When *True*, existing keys in target are overwritten.

    Returns:
        A :class:`PromoteResult` describing what changed.
    """
    source_vault = Path(source_vault)
    target_vault = Path(target_vault)

    if not source_vault.exists():
        raise PromoteError(f"Source vault not found: {source_vault}")
    if not target_vault.exists():
        raise PromoteError(f"Target vault not found: {target_vault}")

    # Unlock source
    src = Vault(source_vault.with_suffix(""))
    src.unlock(source_passphrase)

    source_env = source_vault.with_suffix("")  # .env path
    source_lines = Path(source_env).read_text().splitlines()

    # Parse source key/value pairs
    source_pairs: dict[str, str] = {}
    for line in source_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        k, _, v = stripped.partition("=")
        source_pairs[k.strip()] = v.strip()

    # Unlock target
    tgt = Vault(target_vault.with_suffix(""))
    tgt.unlock(target_passphrase)

    target_env = target_vault.with_suffix("")
    target_lines = Path(target_env).read_text().splitlines()

    # Parse existing target keys
    existing_keys: set[str] = set()
    for line in target_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        k, _, _ = stripped.partition("=")
        existing_keys.add(k.strip())

    candidates = keys if keys is not None else list(source_pairs.keys())

    result = PromoteResult(
        vault_path=str(target_vault),
        source_path=str(source_vault),
    )

    new_lines = list(target_lines)
    for key in candidates:
        if key not in source_pairs:
            continue
        value = source_pairs[key]
        if key in existing_keys:
            if not overwrite:
                result.skipped.append(key)
                continue
            # Replace existing line
            new_lines = [
                f"{key}={value}" if (l.strip().startswith(key + "=") or l.strip().startswith(key + " ="))
                else l
                for l in new_lines
            ]
            result.overwritten.append(key)
        else:
            new_lines.append(f"{key}={value}")
            result.promoted.append(key)

    Path(target_env).write_text("\n".join(new_lines) + "\n")
    tgt.lock(target_passphrase)

    # Re-lock source
    src.lock(source_passphrase)

    return result
