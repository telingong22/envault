"""env_chain.py – resolve a key across an ordered chain of vaults.

The first vault that contains the key wins (cascade lookup).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import Vault


class ChainError(Exception):
    """Raised when the chain cannot be resolved."""


@dataclass
class ChainResult:
    key: str
    value: Optional[str]
    found_in: Optional[Path]
    checked: List[Path] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return self.value is not None

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "found": self.found,
            "found_in": str(self.found_in) if self.found_in else None,
            "checked": [str(p) for p in self.checked],
        }


def resolve_key(
    key: str,
    vault_paths: List[Path],
    passphrase: str,
) -> ChainResult:
    """Walk *vault_paths* in order; return the first vault that holds *key*."""
    if not vault_paths:
        raise ChainError("vault_paths must not be empty")
    if not key:
        raise ChainError("key must not be empty")

    checked: List[Path] = []
    for vp in vault_paths:
        vp = Path(vp)
        if not vp.exists():
            raise ChainError(f"vault not found: {vp}")
        checked.append(vp)
        v = Vault(vp.parent / vp.name.replace(".vault", ".env"), vp)
        env_text = v.unlock(passphrase, write=False)
        pairs = _parse_pairs(env_text)
        if key in pairs:
            return ChainResult(
                key=key,
                value=pairs[key],
                found_in=vp,
                checked=checked,
            )

    return ChainResult(key=key, value=None, found_in=None, checked=checked)


def _parse_pairs(text: str) -> dict:
    pairs: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        pairs[k.strip()] = v.strip().strip('"').strip("'")
    return pairs
