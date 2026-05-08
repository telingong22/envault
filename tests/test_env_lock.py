"""Tests for envault.env_lock."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_lock import (
    LockError,
    lock_key,
    unlock_key,
    list_locked,
    is_key_locked,
)

PASS = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("API_KEY=abc123\nDB_PASS=secret\nDEBUG=true\n")
    v = Vault(env, tmp_path / ".env.vault")
    v.lock(PASS)
    return tmp_path / ".env.vault"


# ---------------------------------------------------------------------------
# lock_key
# ---------------------------------------------------------------------------

def test_lock_key_returns_list(vault_file):
    result = lock_key(vault_file, "API_KEY")
    assert isinstance(result, list)


def test_lock_key_contains_key(vault_file):
    result = lock_key(vault_file, "API_KEY")
    assert "API_KEY" in result


def test_lock_key_creates_keylocks_file(vault_file):
    lock_key(vault_file, "API_KEY")
    keylocks = vault_file.with_suffix(".keylocks.json")
    assert keylocks.exists()


def test_lock_key_idempotent(vault_file):
    lock_key(vault_file, "API_KEY")
    result = lock_key(vault_file, "API_KEY")
    assert result.count("API_KEY") == 1


def test_lock_multiple_keys(vault_file):
    lock_key(vault_file, "API_KEY")
    result = lock_key(vault_file, "DB_PASS")
    assert "API_KEY" in result
    assert "DB_PASS" in result


def test_lock_key_missing_vault_raises(tmp_path):
    with pytest.raises(LockError):
        lock_key(tmp_path / "ghost.vault", "KEY")


def test_lock_key_empty_name_raises(vault_file):
    with pytest.raises(LockError):
        lock_key(vault_file, "")


# ---------------------------------------------------------------------------
# unlock_key
# ---------------------------------------------------------------------------

def test_unlock_key_removes_key(vault_file):
    lock_key(vault_file, "API_KEY")
    result = unlock_key(vault_file, "API_KEY")
    assert "API_KEY" not in result


def test_unlock_nonexistent_key_is_noop(vault_file):
    lock_key(vault_file, "DB_PASS")
    result = unlock_key(vault_file, "MISSING_KEY")
    assert "DB_PASS" in result


def test_unlock_key_missing_vault_raises(tmp_path):
    with pytest.raises(LockError):
        unlock_key(tmp_path / "ghost.vault", "KEY")


# ---------------------------------------------------------------------------
# list_locked / is_key_locked
# ---------------------------------------------------------------------------

def test_list_locked_empty_by_default(vault_file):
    assert list_locked(vault_file) == []


def test_list_locked_reflects_additions(vault_file):
    lock_key(vault_file, "API_KEY")
    lock_key(vault_file, "DEBUG")
    assert set(list_locked(vault_file)) == {"API_KEY", "DEBUG"}


def test_is_key_locked_true(vault_file):
    lock_key(vault_file, "API_KEY")
    assert is_key_locked(vault_file, "API_KEY") is True


def test_is_key_locked_false(vault_file):
    assert is_key_locked(vault_file, "API_KEY") is False
