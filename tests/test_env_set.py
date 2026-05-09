"""Tests for envault.env_set — set_keys."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.crypto import encrypt, decrypt
from envault.env_set import SetError, SetResult, set_keys


PASSPHRASE = "test-passphrase-42"
INITIAL_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc123\n"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.vault"
    path.write_bytes(encrypt(INITIAL_ENV.encode(), PASSPHRASE))
    return path


# --- return type ---

def test_set_keys_returns_set_result(vault_file):
    result = set_keys(vault_file, PASSPHRASE, {"NEW_KEY": "new_val"})
    assert isinstance(result, SetResult)


# --- added vs updated ---

def test_new_key_appears_in_added(vault_file):
    result = set_keys(vault_file, PASSPHRASE, {"BRAND_NEW": "yes"})
    assert "BRAND_NEW" in result.added


def test_new_key_not_in_updated(vault_file):
    result = set_keys(vault_file, PASSPHRASE, {"BRAND_NEW": "yes"})
    assert "BRAND_NEW" not in result.updated


def test_existing_key_appears_in_updated(vault_file):
    result = set_keys(vault_file, PASSPHRASE, {"DB_HOST": "remotehost"})
    assert "DB_HOST" in result.updated


def test_existing_key_not_in_added(vault_file):
    result = set_keys(vault_file, PASSPHRASE, {"DB_HOST": "remotehost"})
    assert "DB_HOST" not in result.added


# --- persistence ---

def test_new_value_persists_after_decrypt(vault_file):
    set_keys(vault_file, PASSPHRASE, {"INJECTED": "hello"})
    raw = decrypt(vault_file.read_bytes(), PASSPHRASE).decode()
    assert "INJECTED=hello" in raw


def test_updated_value_overwrites_old(vault_file):
    set_keys(vault_file, PASSPHRASE, {"SECRET": "new_secret"})
    raw = decrypt(vault_file.read_bytes(), PASSPHRASE).decode()
    assert "SECRET=new_secret" in raw
    assert "SECRET=abc123" not in raw


def test_other_keys_preserved(vault_file):
    set_keys(vault_file, PASSPHRASE, {"NEW_KEY": "v"})
    raw = decrypt(vault_file.read_bytes(), PASSPHRASE).decode()
    assert "DB_HOST=localhost" in raw
    assert "DB_PORT=5432" in raw


# --- multiple pairs ---

def test_multiple_pairs_all_persisted(vault_file):
    set_keys(vault_file, PASSPHRASE, {"K1": "v1", "K2": "v2"})
    raw = decrypt(vault_file.read_bytes(), PASSPHRASE).decode()
    assert "K1=v1" in raw
    assert "K2=v2" in raw


# --- as_dict ---

def test_as_dict_contains_vault_path(vault_file):
    result = set_keys(vault_file, PASSPHRASE, {"X": "1"})
    d = result.as_dict()
    assert str(vault_file) in d["vault_path"]


def test_as_dict_has_added_and_updated(vault_file):
    result = set_keys(vault_file, PASSPHRASE, {"X": "1"})
    d = result.as_dict()
    assert "added" in d and "updated" in d


# --- error cases ---

def test_missing_vault_raises(tmp_path):
    with pytest.raises(SetError, match="Vault not found"):
        set_keys(tmp_path / "no.vault", PASSPHRASE, {"K": "v"})


def test_invalid_key_raises(vault_file):
    with pytest.raises(SetError, match="Invalid key"):
        set_keys(vault_file, PASSPHRASE, {"123BAD": "v"})
