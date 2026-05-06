"""High-level Vault abstraction: lock/unlock .env files."""

from __future__ import annotations

import os
from typing import Optional

from envault.crypto import encrypt, decrypt

_VAULT_SUFFIX = ".vault"


class Vault:
    """Manages a single encrypted vault file."""

    def __init__(self, vault_path: str) -> None:
        self.vault_path = vault_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def lock(
        self,
        env_path: str,
        passphrase: str,
        remove_original: bool = False,
    ) -> str:
        """Encrypt *env_path* and write the vault file.

        Returns the vault file path.
        """
        with open(env_path, "rb") as fh:
            plaintext = fh.read()

        blob = encrypt(plaintext, passphrase)

        with open(self.vault_path, "wb") as fh:
            fh.write(blob)

        if remove_original:
            os.remove(env_path)

        return self.vault_path

    def unlock(
        self,
        passphrase: str,
        target_path: Optional[str],
        overwrite: bool = True,
    ) -> str:
        """Decrypt the vault and optionally write *target_path*.

        Returns the decrypted content as a string.
        Raises ``FileNotFoundError`` if the vault does not exist.
        Raises ``ValueError`` (from crypto layer) on bad passphrase.
        """
        if not os.path.exists(self.vault_path):
            raise FileNotFoundError(f"Vault not found: {self.vault_path}")

        with open(self.vault_path, "rb") as fh:
            blob = fh.read()

        plaintext_bytes = decrypt(blob, passphrase)
        plaintext = plaintext_bytes.decode("utf-8")

        if target_path is not None:
            if not overwrite and os.path.exists(target_path):
                raise FileExistsError(
                    f"{target_path} already exists; pass overwrite=True to replace it."
                )
            with open(target_path, "w") as fh:
                fh.write(plaintext)

        return plaintext

    def is_locked(self, env_path: str) -> bool:
        """Return True when a vault file exists for *env_path*.

        A vault is considered active when the vault file is present AND
        the original env file is absent.
        """
        return os.path.exists(self.vault_path) and not os.path.exists(env_path)
