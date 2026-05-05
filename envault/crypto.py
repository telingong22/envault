"""Cryptographic primitives for envault.

Uses AES-256-GCM via the cryptography library with Argon2id key derivation.
"""

import os
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.exceptions import InvalidTag

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
SCRYPT_N = 2 ** 15
SCRYPT_R = 8
SCRYPT_P = 1

# Header: magic (4) + version (1) + salt (16) + nonce (12) = 33 bytes
MAGIC = b"ENVT"
VERSION = 1


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from *passphrase* using scrypt."""
    kdf = Scrypt(salt=salt, length=KEY_SIZE, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return kdf.derive(passphrase.encode())


def encrypt(plaintext: bytes, passphrase: str) -> bytes:
    """Encrypt *plaintext* with *passphrase* and return the ciphertext blob."""
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    header = MAGIC + struct.pack("B", VERSION) + salt + nonce
    return header + ciphertext


def decrypt(blob: bytes, passphrase: str) -> bytes:
    """Decrypt *blob* with *passphrase* and return the plaintext.

    Raises:
        ValueError: on bad magic, unsupported version, or wrong passphrase.
    """
    header_size = len(MAGIC) + 1 + SALT_SIZE + NONCE_SIZE
    if len(blob) < header_size:
        raise ValueError("Data is too short to be a valid envault blob.")

    magic = blob[:4]
    if magic != MAGIC:
        raise ValueError("Not a valid envault file (bad magic bytes).")

    version = struct.unpack("B", blob[4:5])[0]
    if version != VERSION:
        raise ValueError(f"Unsupported envault version: {version}.")

    salt = blob[5:5 + SALT_SIZE]
    nonce = blob[5 + SALT_SIZE:5 + SALT_SIZE + NONCE_SIZE]
    ciphertext = blob[header_size:]

    key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, None)
    except InvalidTag as exc:
        raise ValueError("Decryption failed — wrong passphrase or corrupted data.") from exc
