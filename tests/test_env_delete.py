"""Tests for envault.env_delete."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.vault import Vault
from envault.env_delete import DeleteError, DeleteResult, delete_keys

PASSPHRASE = "test-passphrase"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("API_KEY=abc123\nDB_URL=postgres://localhost\nDEBUG=true\n")
    v = Vault(tmp_path / ".env.vault")
    v.lock(PASSPHRASE, env_path=env)
    return tmp_path / ".env.vault"


def test_delete_returns_delete_result(vault_file: Path) -> None:
    result = delete_keys(vault_file, ["DEBUG"], PASSPHRASE)
    assert isinstance(result, DeleteResult)


def test_delete_result_contains_vault_path(vault_file: Path) -> None:
    result = delete_keys(vault_file, ["DEBUG"], PASSPHRASE)
    assert result.vault_path == vault_file


def test_deleted_key_in_result(vault_file: Path) -> None:
    result = delete_keys(vault_file, ["DEBUG"], PASSPHRASE)
    assert "DEBUG" in result.deleted


def test_deleted_key_absent_after_unlock(vault_file: Path, tmp_path: Path) -> None:
    delete_keys(vault_file, ["DEBUG"], PASSPHRASE)
    v = Vault(vault_file)
    env_path = v.unlock(PASSPHRASE)
    content = Path(env_path).read_text()
    assert "DEBUG" not in content


def test_remaining_keys_preserved(vault_file: Path, tmp_path: Path) -> None:
    delete_keys(vault_file, ["DEBUG"], PASSPHRASE)
    v = Vault(vault_file)
    env_path = v.unlock(PASSPHRASE)
    content = Path(env_path).read_text()
    assert "API_KEY" in content
    assert "DB_URL" in content


def test_delete_multiple_keys(vault_file: Path, tmp_path: Path) -> None:
    result = delete_keys(vault_file, ["API_KEY", "DEBUG"], PASSPHRASE)
    assert set(result.deleted) == {"API_KEY", "DEBUG"}
    v = Vault(vault_file)
    env_path = v.unlock(PASSPHRASE)
    content = Path(env_path).read_text()
    assert "API_KEY" not in content
    assert "DEBUG" not in content


def test_missing_key_raises_by_default(vault_file: Path) -> None:
    with pytest.raises(DeleteError, match="NONEXISTENT"):
        delete_keys(vault_file, ["NONEXISTENT"], PASSPHRASE)


def test_missing_key_ok_when_missing_ok(vault_file: Path) -> None:
    result = delete_keys(vault_file, ["NONEXISTENT"], PASSPHRASE, missing_ok=True)
    assert "NONEXISTENT" in result.not_found
    assert result.deleted == []


def test_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(DeleteError, match="Vault not found"):
        delete_keys(tmp_path / "missing.vault", ["KEY"], PASSPHRASE)


def test_as_dict_shape(vault_file: Path) -> None:
    result = delete_keys(vault_file, ["DEBUG"], PASSPHRASE)
    d = result.as_dict()
    assert "vault_path" in d
    assert "deleted" in d
    assert "not_found" in d
