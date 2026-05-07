"""Import secrets from external sources into a vault."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

from envault.vault import Vault


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


def _parse_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env-formatted string into a key/value dict."""
    pairs: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            pairs[key] = value
    return pairs


def _parse_json(text: str) -> Dict[str, str]:
    """Parse a JSON object into a key/value dict (values coerced to str)."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object")
    return {str(k): str(v) for k, v in data.items()}


def import_into_vault(
    source: Path,
    vault_path: Path,
    passphrase: str,
    fmt: str = "dotenv",
    merge: bool = False,
) -> Dict[str, str]:
    """Import key/value pairs from *source* into *vault_path*.

    Parameters
    ----------
    source:
        Path to the file containing secrets (dotenv or JSON).
    vault_path:
        Destination vault file.
    passphrase:
        Master passphrase used to lock the vault.
    fmt:
        ``"dotenv"`` (default) or ``"json"``.
    merge:
        When *True*, existing vault contents are merged with the imported
        pairs (imported values win on conflict).  When *False* the vault is
        overwritten entirely.

    Returns
    -------
    dict
        The final key/value mapping written to the vault.
    """
    if not source.exists():
        raise ImportError(f"Source file not found: {source}")

    text = source.read_text(encoding="utf-8")

    parsers = {"dotenv": _parse_dotenv, "json": _parse_json}
    if fmt not in parsers:
        raise ImportError(f"Unsupported format '{fmt}'. Choose 'dotenv' or 'json'.")

    incoming: Dict[str, str] = parsers[fmt](text)

    if not incoming:
        raise ImportError("Source file contains no key/value pairs")

    base: Dict[str, str] = {}
    if merge and vault_path.exists():
        v = Vault(vault_path)
        env_tmp = vault_path.with_suffix(".env.tmp")
        try:
            v.unlock(passphrase, env_path=env_tmp)
            base = _parse_dotenv(env_tmp.read_text(encoding="utf-8"))
        finally:
            if env_tmp.exists():
                env_tmp.unlink()

    merged = {**base, **incoming}

    env_tmp = vault_path.with_suffix(".env.import_tmp")
    try:
        lines = [f"{k}={v}" for k, v in merged.items()]
        env_tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        v = Vault(vault_path)
        v.lock(passphrase, env_path=env_tmp)
    finally:
        if env_tmp.exists():
            env_tmp.unlink()

    return merged
