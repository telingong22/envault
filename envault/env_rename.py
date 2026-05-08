"""Rename a key inside a locked vault without fully exposing all values."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.vault import Vault


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


def rename_key(
    vault_path: str | Path,
    passphrase: str,
    old_key: str,
    new_key: str,
    *,
    env_path: Optional[str | Path] = None,
) -> dict:
    """Rename *old_key* to *new_key* inside *vault_path*.

    The vault is unlocked into a temporary in-memory representation,
    the key is renamed, and the vault is re-locked in place.

    Returns a dict with ``old_key``, ``new_key``, and ``vault`` path.

    Raises
    ------
    RenameError
        If *old_key* does not exist or *new_key* already exists.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise RenameError(f"Vault not found: {vault_path}")

    # Resolve the companion .env path the same way Vault does.
    if env_path is None:
        env_path = vault_path.with_suffix("") if vault_path.suffix == ".vault" else Path(str(vault_path).replace(".vault", ""))
        # Fallback: derive from vault name
        stem = vault_path.stem  # e.g. ".env" from ".env.vault"
        env_path = vault_path.parent / stem

    env_path = Path(env_path)

    v = Vault(str(env_path))
    # Unlock restores env_path from the vault.
    v.unlock(passphrase, vault_path=str(vault_path))

    lines = env_path.read_text().splitlines(keepends=True)

    # Check key presence
    existing_keys = _parse_keys(lines)
    if old_key not in existing_keys:
        # Re-lock and abort
        v.lock(passphrase, vault_path=str(vault_path))
        raise RenameError(f"Key '{old_key}' not found in vault.")
    if new_key in existing_keys and new_key != old_key:
        v.lock(passphrase, vault_path=str(vault_path))
        raise RenameError(f"Key '{new_key}' already exists in vault.")

    new_lines = _rename_in_lines(lines, old_key, new_key)
    env_path.write_text("".join(new_lines))

    v.lock(passphrase, vault_path=str(vault_path))

    return {"old_key": old_key, "new_key": new_key, "vault": str(vault_path)}


def _parse_keys(lines: list[str]) -> set[str]:
    keys: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            keys.add(key)
    return keys


def _rename_in_lines(lines: list[str], old_key: str, new_key: str) -> list[str]:
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, rest = stripped.split("=", 1)
            if key.strip() == old_key:
                # Preserve original indentation/trailing newline style.
                indent = line[: len(line) - len(line.lstrip())]
                nl = "\n" if line.endswith("\n") else ""
                line = f"{indent}{new_key}={rest}{nl}"
        result.append(line)
    return result
