"""Unit tests for envault.crypto."""

import pytest

from envault.crypto import encrypt, decrypt, MAGIC, VERSION


PASSPHRASE = "super-secret-passphrase"
PLAINTEXT = b"DB_HOST=localhost\nDB_PASS=hunter2\n"


def test_encrypt_returns_bytes():
    blob = encrypt(PLAINTEXT, PASSPHRASE)
    assert isinstance(blob, bytes)


def test_blob_starts_with_magic():
    blob = encrypt(PLAINTEXT, PASSPHRASE)
    assert blob[:4] == MAGIC


def test_blob_version_byte():
    blob = encrypt(PLAINTEXT, PASSPHRASE)
    assert blob[4] == VERSION


def test_encrypt_decrypt_roundtrip():
    blob = encrypt(PLAINTEXT, PASSPHRASE)
    recovered = decrypt(blob, PASSPHRASE)
    assert recovered == PLAINTEXT


def test_each_encryption_is_unique():
    blob1 = encrypt(PLAINTEXT, PASSPHRASE)
    blob2 = encrypt(PLAINTEXT, PASSPHRASE)
    assert blob1 != blob2  # different salt/nonce each time


def test_wrong_passphrase_raises():
    blob = encrypt(PLAINTEXT, PASSPHRASE)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(blob, "wrong-passphrase")


def test_bad_magic_raises():
    blob = bytearray(encrypt(PLAINTEXT, PASSPHRASE))
    blob[:4] = b"XXXX"
    with pytest.raises(ValueError, match="bad magic"):
        decrypt(bytes(blob), PASSPHRASE)


def test_truncated_data_raises():
    with pytest.raises(ValueError, match="too short"):
        decrypt(b"ENVT", PASSPHRASE)


def test_tampered_ciphertext_raises():
    blob = bytearray(encrypt(PLAINTEXT, PASSPHRASE))
    blob[-1] ^= 0xFF  # flip last byte
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(bytes(blob), PASSPHRASE)
