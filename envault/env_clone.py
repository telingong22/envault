"""Clone a vault to a new path, optionally re-encrypting with a different passphrase."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from envault.vault import Vault


class CloneError(Exception):
    """Raised when cloning fails."""


@dataclass
class CloneResult:
    source: str
    destination: str
    re_encrypted: bool

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "destination": self.destination,
            "re_encrypted": self.re_encrypted,
        }


def clone_vault(
    source_path: str | Path,
    dest_path: str | Path,
    passphrase: str,
    new_passphrase: str | None = None,
) -> CloneResult:
    """Clone *source_path* to *dest_path*.

    If *new_passphrase* is provided the clone is re-encrypted with it;
    otherwise the vault file is copied verbatim and the same passphrase
    is required to unlock it.

    Raises
    ------
    CloneError
        If the source vault does not exist, the passphrase is wrong, or
        the destination already exists.
    """
    source_path = Path(source_path)
    dest_path = Path(dest_path)

    if not source_path.exists():
        raise CloneError(f"Source vault not found: {source_path}")

    if dest_path.exists():
        raise CloneError(f"Destination already exists: {dest_path}")

    if new_passphrase is None:
        # Simple byte-for-byte copy — no decryption needed.
        shutil.copy2(source_path, dest_path)
        return CloneResult(
            source=str(source_path),
            destination=str(dest_path),
            re_encrypted=False,
        )

    # Re-encrypt: decrypt with old passphrase, re-encrypt with new one.
    tmp_env = dest_path.with_suffix(".env.clone_tmp")
    try:
        src_vault = Vault(source_path)
        src_vault.unlock(passphrase, output_path=tmp_env)

        dst_vault = Vault(dest_path)
        dst_vault.lock(tmp_env, new_passphrase)
    except Exception as exc:
        raise CloneError(f"Clone failed: {exc}") from exc
    finally:
        if tmp_env.exists():
            tmp_env.unlink()

    return CloneResult(
        source=str(source_path),
        destination=str(dest_path),
        re_encrypted=True,
    )
