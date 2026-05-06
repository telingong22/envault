"""Tests for envault.rotate."""

from __future__ import annotations

import pytest

from envault.crypto import decrypt, encrypt
from envault.rotate import RotationError, rotate


OLD_PASS = "old-secret"
NEW_PASS = "new-secret"
PLAINTEXT = b"API_KEY=abc123\nDEBUG=true\n"


@pytest.fixture()
def vault_file(tmp_path):
    """A temporary vault file encrypted with OLD_PASS."""
    path = tmp_path / ".env.vault"
    path.write_bytes(encrypt(PLAINTEXT, OLD_PASS))
    return path


def test_rotate_returns_vault_path(vault_file):
    result = rotate(vault_file, OLD_PASS, NEW_PASS)
    assert result == vault_file


def test_rotate_new_passphrase_decrypts(vault_file):
    rotate(vault_file, OLD_PASS, NEW_PASS)
    recovered = decrypt(vault_file.read_bytes(), NEW_PASS)
    assert recovered == PLAINTEXT


def test_rotate_old_passphrase_no_longer_works(vault_file):
    rotate(vault_file, OLD_PASS, NEW_PASS)
    with pytest.raises(Exception):
        decrypt(vault_file.read_bytes(), OLD_PASS)


def test_rotate_creates_backup_by_default(vault_file):
    original_blob = vault_file.read_bytes()
    rotate(vault_file, OLD_PASS, NEW_PASS)
    backup = vault_file.with_suffix(".vault.bak")
    assert backup.exists()
    assert backup.read_bytes() == original_blob


def test_rotate_no_backup_when_disabled(vault_file):
    rotate(vault_file, OLD_PASS, NEW_PASS, backup=False)
    backup = vault_file.with_suffix(".vault.bak")
    assert not backup.exists()


def test_rotate_raises_on_wrong_old_passphrase(vault_file):
    with pytest.raises(RotationError, match="Failed to decrypt"):
        rotate(vault_file, "wrong-pass", NEW_PASS)


def test_rotate_raises_when_vault_missing(tmp_path):
    missing = tmp_path / "ghost.vault"
    with pytest.raises(RotationError, match="not found"):
        rotate(missing, OLD_PASS, NEW_PASS)


def test_rotate_backup_decryptable_with_old_pass(vault_file):
    rotate(vault_file, OLD_PASS, NEW_PASS)
    backup = vault_file.with_suffix(".vault.bak")
    recovered = decrypt(backup.read_bytes(), OLD_PASS)
    assert recovered == PLAINTEXT
