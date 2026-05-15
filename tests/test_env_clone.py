"""Tests for envault.env_clone."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_clone import CloneError, CloneResult, clone_vault


PASSPHRASE = "test-secret"
NEW_PASSPHRASE = "new-secret"

ENV_CONTENT = "API_KEY=abc123\nDB_URL=postgres://localhost/db\n"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    vault = tmp_path / ".env.vault"
    Vault(vault).lock(env, PASSPHRASE)
    return vault


# ---------------------------------------------------------------------------
# CloneResult
# ---------------------------------------------------------------------------

def test_clone_returns_clone_result(vault_file, tmp_path):
    dest = tmp_path / "clone.vault"
    result = clone_vault(vault_file, dest, PASSPHRASE)
    assert isinstance(result, CloneResult)


def test_clone_result_contains_source(vault_file, tmp_path):
    dest = tmp_path / "clone.vault"
    result = clone_vault(vault_file, dest, PASSPHRASE)
    assert result.source == str(vault_file)


def test_clone_result_contains_destination(vault_file, tmp_path):
    dest = tmp_path / "clone.vault"
    result = clone_vault(vault_file, dest, PASSPHRASE)
    assert result.destination == str(dest)


# ---------------------------------------------------------------------------
# Simple copy (no re-encryption)
# ---------------------------------------------------------------------------

def test_clone_creates_destination_file(vault_file, tmp_path):
    dest = tmp_path / "clone.vault"
    clone_vault(vault_file, dest, PASSPHRASE)
    assert dest.exists()


def test_clone_copy_not_re_encrypted(vault_file, tmp_path):
    dest = tmp_path / "clone.vault"
    result = clone_vault(vault_file, dest, PASSPHRASE)
    assert result.re_encrypted is False


def test_clone_copy_unlockable_with_original_passphrase(vault_file, tmp_path):
    dest = tmp_path / "clone.vault"
    clone_vault(vault_file, dest, PASSPHRASE)
    out = tmp_path / "unlocked.env"
    Vault(dest).unlock(PASSPHRASE, output_path=out)
    assert "API_KEY=abc123" in out.read_text()


# ---------------------------------------------------------------------------
# Re-encryption
# ---------------------------------------------------------------------------

def test_clone_re_encrypted_flag(vault_file, tmp_path):
    dest = tmp_path / "clone.vault"
    result = clone_vault(vault_file, dest, PASSPHRASE, new_passphrase=NEW_PASSPHRASE)
    assert result.re_encrypted is True


def test_clone_re_encrypted_unlockable_with_new_passphrase(vault_file, tmp_path):
    dest = tmp_path / "clone.vault"
    clone_vault(vault_file, dest, PASSPHRASE, new_passphrase=NEW_PASSPHRASE)
    out = tmp_path / "unlocked.env"
    Vault(dest).unlock(NEW_PASSPHRASE, output_path=out)
    assert "DB_URL=postgres://localhost/db" in out.read_text()


def test_clone_re_encrypted_old_passphrase_fails(vault_file, tmp_path):
    dest = tmp_path / "clone.vault"
    clone_vault(vault_file, dest, PASSPHRASE, new_passphrase=NEW_PASSPHRASE)
    out = tmp_path / "unlocked.env"
    with pytest.raises(Exception):
        Vault(dest).unlock(PASSPHRASE, output_path=out)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_clone_missing_source_raises(tmp_path):
    with pytest.raises(CloneError, match="Source vault not found"):
        clone_vault(tmp_path / "ghost.vault", tmp_path / "dest.vault", PASSPHRASE)


def test_clone_existing_destination_raises(vault_file, tmp_path):
    dest = tmp_path / "clone.vault"
    dest.write_bytes(b"exists")
    with pytest.raises(CloneError, match="Destination already exists"):
        clone_vault(vault_file, dest, PASSPHRASE)


def test_clone_as_dict(vault_file, tmp_path):
    dest = tmp_path / "clone.vault"
    result = clone_vault(vault_file, dest, PASSPHRASE)
    d = result.as_dict()
    assert set(d.keys()) == {"source", "destination", "re_encrypted"}
