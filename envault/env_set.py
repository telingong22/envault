"""env_set.py — Add or update individual key/value pairs inside a vault."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envault.vault import Vault


class SetError(Exception):
    """Raised when a key/value set operation cannot be completed."""


@dataclass
class SetResult:
    vault_path: Path
    updated: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "updated": self.updated,
            "added": self.added,
        }


_KEY_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _validate_key(key: str) -> None:
    if not _KEY_RE.match(key):
        raise SetError(
            f"Invalid key {key!r}: keys must start with a letter or underscore "
            "and contain only letters, digits, or underscores."
        )


def _parse_env_lines(text: str) -> Dict[str, str]:
    """Parse .env content into an ordered dict preserving insertion order."""
    pairs: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if '=' not in stripped:
            continue
        k, _, v = stripped.partition('=')
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        pairs[k] = v
    return pairs


def _render_env(pairs: Dict[str, str]) -> str:
    return '\n'.join(f'{k}={v}' for k, v in pairs.items()) + '\n'


def set_keys(
    vault_path: Path | str,
    passphrase: str,
    pairs: Dict[str, str],
) -> SetResult:
    """Set one or more key/value pairs in *vault_path*, re-encrypting afterwards.

    Parameters
    ----------
    vault_path:
        Path to the ``.vault`` file.
    passphrase:
        Master passphrase used to decrypt and re-encrypt the vault.
    pairs:
        Mapping of key → value pairs to insert or overwrite.

    Returns
    -------
    SetResult
        Lists which keys were *added* (new) and which were *updated* (existing).
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise SetError(f"Vault not found: {vault_path}")

    for key in pairs:
        _validate_key(key)

    v = Vault(vault_path.parent / (vault_path.stem.replace('.vault', '') + '.env'))
    # Unlock into a temp location so we can read current content
    import tempfile, shutil
    with tempfile.TemporaryDirectory() as tmp:
        tmp_env = Path(tmp) / 'current.env'
        v2 = Vault(tmp_env)
        # We need raw decrypt
        from envault.crypto import decrypt
        raw = decrypt(vault_path.read_bytes(), passphrase)
        tmp_env.write_bytes(raw)

        existing = _parse_env_lines(tmp_env.read_text())

    result = SetResult(vault_path=vault_path)
    for key, value in pairs.items():
        if key in existing:
            result.updated.append(key)
        else:
            result.added.append(key)
        existing[key] = value

    new_content = _render_env(existing)

    from envault.crypto import encrypt
    vault_path.write_bytes(encrypt(new_content.encode(), passphrase))

    return result
