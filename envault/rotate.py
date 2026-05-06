"""Passphrase rotation for encrypted vault files."""

from __future__ import annotations

from pathlib import Path

from envault.crypto import decrypt, encrypt


class RotationError(Exception):
    """Raised when vault rotation fails."""


def rotate(
    vault_path: str | Path,
    old_passphrase: str,
    new_passphrase: str,
    *,
    backup: bool = True,
) -> Path:
    """Re-encrypt *vault_path* under *new_passphrase*.

    Parameters
    ----------
    vault_path:
        Path to the ``.vault`` file produced by :func:`envault.vault.Vault.lock`.
    old_passphrase:
        The passphrase currently protecting the vault.
    new_passphrase:
        The passphrase that will protect the vault after rotation.
    backup:
        When *True* (default) a ``.vault.bak`` copy of the original file is
        written before the vault is overwritten.

    Returns
    -------
    Path
        The path to the rotated vault file (same as *vault_path*).

    Raises
    ------
    RotationError
        If the vault file does not exist, the old passphrase is incorrect, or
        the new passphrase is identical to the old one.
    """
    vault_path = Path(vault_path)

    if not vault_path.exists():
        raise RotationError(f"Vault file not found: {vault_path}")

    if old_passphrase == new_passphrase:
        raise RotationError("New passphrase must differ from the old passphrase.")

    blob = vault_path.read_bytes()

    try:
        plaintext = decrypt(blob, old_passphrase)
    except Exception as exc:
        raise RotationError("Failed to decrypt vault with the supplied passphrase.") from exc

    new_blob = encrypt(plaintext, new_passphrase)

    if backup:
        backup_path = vault_path.with_suffix(".vault.bak")
        backup_path.write_bytes(blob)

    vault_path.write_bytes(new_blob)
    return vault_path
