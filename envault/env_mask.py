"""env_mask.py – selectively mask (redact display of) keys in a vault.

Masked keys are stored in a sidecar JSON file alongside the vault.
When a masked key is displayed via summarise/export it shows '***'.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from envault.vault import Vault


class MaskError(Exception):
    """Raised when a masking operation fails."""


class MaskResult:
    def __init__(self, vault_path: Path, masked: List[str], unmasked: List[str]):
        self.vault_path = vault_path
        self.masked = masked
        self.unmasked = unmasked

    def as_dict(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "masked": self.masked,
            "unmasked": self.unmasked,
        }


def _mask_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".masks.json")


def _load_masks(vault_path: Path) -> List[str]:
    p = _mask_path(vault_path)
    if not p.exists():
        return []
    return json.loads(p.read_text())


def _save_masks(vault_path: Path, masks: List[str]) -> None:
    _mask_path(vault_path).write_text(json.dumps(sorted(set(masks)), indent=2))


def mask_keys(vault_path: Path, passphrase: str, keys: List[str]) -> MaskResult:
    """Add *keys* to the mask list for *vault_path*."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise MaskError(f"Vault not found: {vault_path}")
    v = Vault(vault_path.parent / vault_path.name.replace(".vault", ".env"))
    v.unlock(passphrase, vault_path=vault_path)
    existing = _load_masks(vault_path)
    updated = sorted(set(existing) | set(keys))
    _save_masks(vault_path, updated)
    return MaskResult(vault_path=vault_path, masked=sorted(keys), unmasked=[])


def unmask_keys(vault_path: Path, passphrase: str, keys: List[str]) -> MaskResult:
    """Remove *keys* from the mask list for *vault_path*."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise MaskError(f"Vault not found: {vault_path}")
    v = Vault(vault_path.parent / vault_path.name.replace(".vault", ".env"))
    v.unlock(passphrase, vault_path=vault_path)
    existing = set(_load_masks(vault_path))
    removed = sorted(existing & set(keys))
    remaining = sorted(existing - set(keys))
    _save_masks(vault_path, remaining)
    return MaskResult(vault_path=vault_path, masked=[], unmasked=removed)


def list_masked(vault_path: Path) -> List[str]:
    """Return the list of currently masked keys for *vault_path*."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise MaskError(f"Vault not found: {vault_path}")
    return _load_masks(vault_path)


def apply_masks(data: dict, vault_path: Path) -> dict:
    """Return a copy of *data* with masked values replaced by '***'."""
    masks = set(_load_masks(vault_path))
    return {k: ("***" if k in masks else v) for k, v in data.items()}
