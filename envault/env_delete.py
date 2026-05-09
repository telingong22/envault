"""Delete one or more keys from an encrypted vault."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.vault import Vault


class DeleteError(Exception):
    """Raised when a key deletion fails."""


@dataclass
class DeleteResult:
    vault_path: Path
    deleted: List[str] = field(default_factory=list)
    not_found: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "vault_path": str(self.vault_path),
            "deleted": self.deleted,
            "not_found": self.not_found,
        }


def delete_keys(
    vault_path: Path,
    keys: List[str],
    passphrase: str,
    *,
    missing_ok: bool = False,
) -> DeleteResult:
    """Remove *keys* from the vault at *vault_path*.

    Parameters
    ----------
    vault_path:
        Path to the ``.vault`` file.
    keys:
        Key names to remove from the env file.
    passphrase:
        Master passphrase used to lock/unlock the vault.
    missing_ok:
        When ``True`` silently ignore keys that do not exist.
        When ``False`` (default) raise :class:`DeleteError`.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise DeleteError(f"Vault not found: {vault_path}")

    v = Vault(vault_path)
    env_path = v.unlock(passphrase)

    lines = Path(env_path).read_text().splitlines(keepends=True)
    existing_keys = _parse_keys(lines)

    result = DeleteResult(vault_path=vault_path)

    for key in keys:
        if key in existing_keys:
            result.deleted.append(key)
        else:
            if not missing_ok:
                raise DeleteError(f"Key not found in vault: {key!r}")
            result.not_found.append(key)

    if result.deleted:
        new_lines = _remove_keys(lines, set(result.deleted))
        Path(env_path).write_text("".join(new_lines))
        v.lock(passphrase)

    return result


def _parse_keys(lines: List[str]) -> set:
    keys: set = set()
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            keys.add(stripped.split("=", 1)[0].strip())
    return keys


def _remove_keys(lines: List[str], keys: set) -> List[str]:
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in keys:
                continue
        result.append(line)
    return result
