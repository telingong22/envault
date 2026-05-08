"""Tests for envault.env_rename."""
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_rename import rename_key, RenameError


PASSPHRASE = "test-secret"


@pytest.fixture()
def vault_file(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY=abc123\n")
    v = Vault(str(env))
    vp = tmp_path / ".env.vault"
    v.lock(PASSPHRASE, vault_path=str(vp))
    env.unlink()  # remove plain .env so unlock is required
    return vp


def test_rename_returns_dict(vault_file):
    result = rename_key(vault_file, PASSPHRASE, "DB_HOST", "DATABASE_HOST")
    assert isinstance(result, dict)


def test_rename_dict_contains_keys(vault_file):
    result = rename_key(vault_file, PASSPHRASE, "DB_HOST", "DATABASE_HOST")
    assert result["old_key"] == "DB_HOST"
    assert result["new_key"] == "DATABASE_HOST"


def test_rename_dict_contains_vault_path(vault_file):
    result = rename_key(vault_file, PASSPHRASE, "DB_HOST", "DATABASE_HOST")
    assert str(vault_file) in result["vault"]


def test_rename_new_key_present_after_unlock(vault_file, tmp_path):
    rename_key(vault_file, PASSPHRASE, "DB_HOST", "DATABASE_HOST")
    env = tmp_path / ".env"
    v = Vault(str(env))
    v.unlock(PASSPHRASE, vault_path=str(vault_file))
    content = env.read_text()
    assert "DATABASE_HOST=" in content


def test_rename_old_key_absent_after_unlock(vault_file, tmp_path):
    rename_key(vault_file, PASSPHRASE, "DB_HOST", "DATABASE_HOST")
    env = tmp_path / ".env"
    v = Vault(str(env))
    v.unlock(PASSPHRASE, vault_path=str(vault_file))
    content = env.read_text()
    assert "DB_HOST=" not in content


def test_rename_value_preserved(vault_file, tmp_path):
    rename_key(vault_file, PASSPHRASE, "DB_HOST", "DATABASE_HOST")
    env = tmp_path / ".env"
    v = Vault(str(env))
    v.unlock(PASSPHRASE, vault_path=str(vault_file))
    content = env.read_text()
    assert "DATABASE_HOST=localhost" in content


def test_rename_other_keys_unchanged(vault_file, tmp_path):
    rename_key(vault_file, PASSPHRASE, "DB_HOST", "DATABASE_HOST")
    env = tmp_path / ".env"
    v = Vault(str(env))
    v.unlock(PASSPHRASE, vault_path=str(vault_file))
    content = env.read_text()
    assert "DB_PORT=5432" in content
    assert "API_KEY=abc123" in content


def test_rename_missing_key_raises(vault_file):
    with pytest.raises(RenameError, match="NONEXISTENT"):
        rename_key(vault_file, PASSPHRASE, "NONEXISTENT", "NEW_KEY")


def test_rename_duplicate_new_key_raises(vault_file):
    with pytest.raises(RenameError, match="DB_PORT"):
        rename_key(vault_file, PASSPHRASE, "DB_HOST", "DB_PORT")


def test_rename_missing_vault_raises(tmp_path):
    with pytest.raises(RenameError, match="Vault not found"):
        rename_key(tmp_path / "ghost.vault", PASSPHRASE, "A", "B")
