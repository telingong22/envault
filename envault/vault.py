"""Vault: high-level lock/unlock operations wrapping crypto primitives."""

from __future__ import annotations

from pathlib import Path

from envault.crypto import encrypt, decrypt
from envault import audit

DEFAULT_VAULT_SUFFIX = ".vault"


class Vault:
    """Manages locking and unlocking a single .env file."""

    def __init__(self, env_path: str | Path, vault_path: str | Path | None = None):
        self.env_path = Path(env_path)
        self.vault_path = (
            Path(vault_path)
            if vault_path
            else self.env_path.with_suffix(DEFAULT_VAULT_SUFFIX)
        )

    # ------------------------------------------------------------------
    def lock(self, passphrase: str) -> None:
        """Encrypt *env_path* into *vault_path* and remove the plaintext file."""
        plaintext = self.env_path.read_bytes()
        blob = encrypt(plaintext, passphrase)
        self.vault_path.write_bytes(blob)
        self.env_path.unlink()
        audit.record_event(
            "lock",
            env_path=self.env_path,
            vault_path=self.vault_path,
        )

    # ------------------------------------------------------------------
    def unlock(self, passphrase: str, overwrite: bool = True) -> bytes:
        """Decrypt *vault_path* and restore *env_path*.

        Returns the decrypted plaintext bytes.
        Raises ``FileExistsError`` if *env_path* already exists and
        *overwrite* is ``False``.
        """
        if self.env_path.exists() and not overwrite:
            raise FileExistsError(
                f"{self.env_path} already exists. Pass overwrite=True to replace it."
            )
        blob = self.vault_path.read_bytes()
        try:
            plaintext = decrypt(blob, passphrase)
        except Exception as exc:
            audit.record_event(
                "unlock",
                env_path=self.env_path,
                vault_path=self.vault_path,
                success=False,
                detail=str(exc),
            )
            raise
        self.env_path.write_bytes(plaintext)
        audit.record_event(
            "unlock",
            env_path=self.env_path,
            vault_path=self.vault_path,
        )
        return plaintext

    # ------------------------------------------------------------------
    def is_locked(self) -> bool:
        """Return True when the vault file exists and the plaintext file does not."""
        return self.vault_path.exists() and not self.env_path.exists()
