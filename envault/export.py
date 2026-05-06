"""Export decrypted vault contents to various formats."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Literal

from envault.inspector import parse_env
from envault.vault import Vault

ExportFormat = Literal["dotenv", "json", "shell"]


class ExportError(Exception):
    """Raised when an export operation fails."""


def _to_dotenv(pairs: Dict[str, str]) -> str:
    lines = []
    for key, value in pairs.items():
        # Re-quote values that contain spaces or special characters
        if any(c in value for c in (" ", "\t", "#", "'", '"')):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return os.linesep.join(lines) + os.linesep


def _to_json(pairs: Dict[str, str]) -> str:
    return json.dumps(pairs, indent=2) + "\n"


def _to_shell(pairs: Dict[str, str]) -> str:
    lines = []
    for key, value in pairs.items():
        escaped = value.replace("'", "'\"'\"'")
        lines.append(f"export {key}='{escaped}'")
    return os.linesep.join(lines) + os.linesep


_FORMATTERS = {
    "dotenv": _to_dotenv,
    "json": _to_json,
    "shell": _to_shell,
}


def export_vault(
    vault_path: str | Path,
    passphrase: str,
    fmt: ExportFormat = "dotenv",
    output_path: str | Path | None = None,
) -> str:
    """Decrypt *vault_path* and return (or write) its contents in *fmt*.

    Parameters
    ----------
    vault_path:  Path to the ``.vault`` file.
    passphrase:  Master passphrase used to decrypt the vault.
    fmt:         One of ``dotenv``, ``json``, or ``shell``.
    output_path: Optional file path to write the result to.

    Returns
    -------
    The formatted string regardless of whether it was written to a file.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise ExportError(f"Vault file not found: {vault_path}")

    if fmt not in _FORMATTERS:
        raise ExportError(f"Unknown format '{fmt}'. Choose from: {', '.join(_FORMATTERS)}")

    # Decrypt to a temporary in-memory env string via Vault
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".env", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        v = Vault(env_path=tmp_path, vault_path=vault_path)
        v.unlock(passphrase)
        pairs = parse_env(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    result = _FORMATTERS[fmt](pairs)

    if output_path is not None:
        Path(output_path).write_text(result, encoding="utf-8")

    return result
