"""High-level Vault operations: lock (encrypt) and unlock (decrypt) .env files."""

from pathlib import Path
from typing import Optional

from envault.crypto import encrypt, decrypt

DEFAULT_ENCRYPTED_SUFFIX = ".vault"


class Vault:
    """Manages encryption/decryption of a single .env file."""

    def __init__(self, env_path: str | Path, vault_path: Optional[str | Path] = None):
        self.env_path = Path(env_path)
        if vault_path is None:
            self.vault_path = self.env_path.with_suffix(
                self.env_path.suffix + DEFAULT_ENCRYPTED_SUFFIX
            )
        else:
            self.vault_path = Path(vault_path)

    def lock(self, passphrase: str) -> Path:
        """Encrypt *env_path* and write the result to *vault_path*.

        Returns the path of the created vault file.
        """
        if not self.env_path.exists():
            raise FileNotFoundError(f"{self.env_path} does not exist.")

        plaintext = self.env_path.read_bytes()
        blob = encrypt(plaintext, passphrase)
        self.vault_path.write_bytes(blob)
        return self.vault_path

    def unlock(self, passphrase: str, output_path: Optional[str | Path] = None) -> Path:
        """Decrypt *vault_path* and write the plaintext to *output_path*.

        If *output_path* is omitted the original *env_path* is used.
        Returns the path of the written plaintext file.
        """
        if not self.vault_path.exists():
            raise FileNotFoundError(f"{self.vault_path} does not exist.")

        blob = self.vault_path.read_bytes()
        plaintext = decrypt(blob, passphrase)

        dest = Path(output_path) if output_path else self.env_path
        dest.write_bytes(plaintext)
        return dest

    def is_locked(self) -> bool:
        """Return True if a vault file exists (regardless of env file state)."""
        return self.vault_path.exists()
