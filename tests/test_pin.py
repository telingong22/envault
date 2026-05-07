"""Tests for envault.pin — PIN-based quick-unlock."""
import pytest
from pathlib import Path

from envault.pin import set_pin, unlock_with_pin, clear_pin, PinError, _pin_path
from envault.vault import Vault


PASSPHRASE = "super-secret-master"
PIN = "19283"


@pytest.fixture
def vault_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text("API_KEY=abc123\nDEBUG=true\n")
    v = Vault(env)
    v.lock(PASSPHRASE)
    return tmp_path / ".env.vault"


# --- set_pin ---

def test_set_pin_returns_path(vault_file):
    path = set_pin(vault_file, PASSPHRASE, PIN)
    assert isinstance(path, Path)


def test_set_pin_creates_file(vault_file):
    path = set_pin(vault_file, PASSPHRASE, PIN)
    assert path.exists()


def test_set_pin_file_is_json(vault_file):
    import json
    path = set_pin(vault_file, PASSPHRASE, PIN)
    data = json.loads(path.read_text())
    assert "salt" in data
    assert "pin_hash" in data
    assert "passphrase_hint" in data


def test_set_pin_too_short_raises(vault_file):
    with pytest.raises(PinError, match="4-8 digits"):
        set_pin(vault_file, PASSPHRASE, "123")


def test_set_pin_too_long_raises(vault_file):
    with pytest.raises(PinError, match="4-8 digits"):
        set_pin(vault_file, PASSPHRASE, "123456789")


def test_set_pin_non_digit_raises(vault_file):
    with pytest.raises(PinError, match="4-8 digits"):
        set_pin(vault_file, PASSPHRASE, "abcd")


# --- unlock_with_pin ---

def test_unlock_with_pin_returns_passphrase(vault_file):
    set_pin(vault_file, PASSPHRASE, PIN)
    result = unlock_with_pin(vault_file, PIN)
    assert result == PASSPHRASE


def test_unlock_wrong_pin_raises(vault_file):
    set_pin(vault_file, PASSPHRASE, PIN)
    with pytest.raises(PinError, match="Incorrect PIN"):
        unlock_with_pin(vault_file, "0000")


def test_unlock_no_pin_file_raises(vault_file):
    with pytest.raises(PinError, match="No PIN registered"):
        unlock_with_pin(vault_file, PIN)


def test_unlock_passphrase_works_with_vault(vault_file, tmp_path):
    """End-to-end: PIN → passphrase → vault unlock."""
    env = vault_file.with_suffix("")
    set_pin(vault_file, PASSPHRASE, PIN)
    recovered = unlock_with_pin(vault_file, PIN)
    v = Vault(env)
    v.unlock(recovered)
    assert env.read_text().strip() != ""


# --- clear_pin ---

def test_clear_pin_removes_file(vault_file):
    set_pin(vault_file, PASSPHRASE, PIN)
    clear_pin(vault_file)
    assert not _pin_path(vault_file).exists()


def test_clear_pin_no_file_is_silent(vault_file):
    """clear_pin should not raise when no token exists."""
    clear_pin(vault_file)  # no exception expected
