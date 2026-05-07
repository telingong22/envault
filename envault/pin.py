"""PIN-based quick-unlock: derive a short numeric PIN from the master passphrase
and store a verification token so the user can unlock with a 4-8 digit PIN
instead of typing the full passphrase every time.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
from pathlib import Path

_PIN_FILE = ".envault_pin"


class PinError(Exception):
    """Raised for PIN-related failures."""


def _pin_path(vault_path: str | Path) -> Path:
    return Path(vault_path).with_suffix(".pin")


def _hash_pin(pin: str, salt: str) -> str:
    """Return a hex digest binding *pin* to *salt*."""
    dk = hashlib.scrypt(
        pin.encode(),
        salt=bytes.fromhex(salt),
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )
    return dk.hex()


def set_pin(vault_path: str | Path, passphrase: str, pin: str) -> Path:
    """Register *pin* as a quick-unlock alias for *passphrase*.

    Writes a JSON token file next to the vault.  Returns the token path.
    """
    if not pin.isdigit() or not (4 <= len(pin) <= 8):
        raise PinError("PIN must be 4-8 digits.")

    salt = secrets.token_hex(16)
    token = {
        "salt": salt,
        "pin_hash": _hash_pin(pin, salt),
        # Store a passphrase verifier so unlock can retrieve it.
        # We encrypt the passphrase under the PIN hash itself.
        "passphrase_hint": _encrypt_hint(passphrase, _hash_pin(pin, salt)),
    }
    path = _pin_path(vault_path)
    path.write_text(json.dumps(token, indent=2))
    return path


def unlock_with_pin(vault_path: str | Path, pin: str) -> str:
    """Return the master passphrase if *pin* matches the stored token."""
    path = _pin_path(vault_path)
    if not path.exists():
        raise PinError("No PIN registered for this vault.")

    token = json.loads(path.read_text())
    candidate = _hash_pin(pin, token["salt"])
    if not secrets.compare_digest(candidate, token["pin_hash"]):
        raise PinError("Incorrect PIN.")

    return _decrypt_hint(token["passphrase_hint"], candidate)


def clear_pin(vault_path: str | Path) -> None:
    """Remove the PIN token file for *vault_path* if it exists."""
    path = _pin_path(vault_path)
    if path.exists():
        path.unlink()


# ---------------------------------------------------------------------------
# Tiny XOR-based hint encryption (not secret-storage grade; PIN hash is key)
# ---------------------------------------------------------------------------

def _xor_bytes(data: bytes, key: bytes) -> bytes:
    key_cycle = (key * (len(data) // len(key) + 1))[: len(data)]
    return bytes(a ^ b for a, b in zip(data, key_cycle))


def _encrypt_hint(plaintext: str, key_hex: str) -> str:
    raw = _xor_bytes(plaintext.encode(), bytes.fromhex(key_hex))
    return raw.hex()


def _decrypt_hint(ciphertext_hex: str, key_hex: str) -> str:
    raw = _xor_bytes(bytes.fromhex(ciphertext_hex), bytes.fromhex(key_hex))
    return raw.decode()
