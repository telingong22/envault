"""Freeze a vault: record the current key/value state as a read-only snapshot
that can later be diffed against the live vault to detect drift."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envault.vault import Vault


class FreezeError(Exception):
    """Raised when a freeze operation fails."""


@dataclass
class FreezeResult:
    vault_path: Path
    freeze_path: Path
    keys: List[str]
    timestamp: str

    def as_dict(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "freeze_path": str(self.freeze_path),
            "keys": self.keys,
            "timestamp": self.timestamp,
        }


def _freeze_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".freeze.json")


def freeze_vault(vault_path: Path, passphrase: str) -> FreezeResult:
    """Encrypt current .env state into a freeze file alongside the vault."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise FreezeError(f"Vault not found: {vault_path}")

    v = Vault(vault_path.parent / vault_path.name.replace(".vault", ".env"))
    env_text = v.unlock(passphrase, write=False)

    pairs: Dict[str, str] = {}
    for line in env_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, val = line.partition("=")
        pairs[k.strip()] = val.strip().strip('"').strip("'")

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    fp = _freeze_path(vault_path)
    fp.write_text(json.dumps({"timestamp": timestamp, "keys": pairs}, indent=2))

    return FreezeResult(
        vault_path=vault_path,
        freeze_path=fp,
        keys=list(pairs.keys()),
        timestamp=timestamp,
    )


def load_freeze(vault_path: Path) -> dict:
    """Return the stored freeze data for *vault_path*."""
    fp = _freeze_path(Path(vault_path))
    if not fp.exists():
        raise FreezeError(f"No freeze file found for {vault_path}")
    return json.loads(fp.read_text())


def diff_freeze(vault_path: Path, passphrase: str) -> Dict[str, dict]:
    """Compare live vault contents against the frozen state.

    Returns a dict with keys 'added', 'removed', 'changed'.
    """
    frozen = load_freeze(vault_path)
    frozen_keys: Dict[str, str] = frozen["keys"]

    v = Vault(vault_path.parent / vault_path.name.replace(".vault", ".env"))
    env_text = v.unlock(passphrase, write=False)

    live: Dict[str, str] = {}
    for line in env_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, val = line.partition("=")
        live[k.strip()] = val.strip().strip('"').strip("'")

    added = {k: live[k] for k in live if k not in frozen_keys}
    removed = {k: frozen_keys[k] for k in frozen_keys if k not in live}
    changed = {
        k: {"before": frozen_keys[k], "after": live[k]}
        for k in live
        if k in frozen_keys and live[k] != frozen_keys[k]
    }
    return {"added": added, "removed": removed, "changed": changed}
