"""Tests for envault.env_freeze."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.vault import Vault
from envault.env_freeze import (
    FreezeError,
    FreezeResult,
    _freeze_path,
    diff_freeze,
    freeze_vault,
    load_freeze,
)

PASSPHRASE = "test-secret"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("API_KEY=abc123\nDEBUG=true\n")
    v = Vault(env)
    v.lock(PASSPHRASE)
    return tmp_path / ".env.vault"


def test_freeze_vault_returns_freeze_result(vault_file: Path) -> None:
    result = freeze_vault(vault_file, PASSPHRASE)
    assert isinstance(result, FreezeResult)


def test_freeze_result_contains_vault_path(vault_file: Path) -> None:
    result = freeze_vault(vault_file, PASSPHRASE)
    assert result.vault_path == vault_file


def test_freeze_result_keys_populated(vault_file: Path) -> None:
    result = freeze_vault(vault_file, PASSPHRASE)
    assert "API_KEY" in result.keys
    assert "DEBUG" in result.keys


def test_freeze_creates_json_file(vault_file: Path) -> None:
    result = freeze_vault(vault_file, PASSPHRASE)
    assert result.freeze_path.exists()


def test_freeze_file_is_valid_json(vault_file: Path) -> None:
    freeze_vault(vault_file, PASSPHRASE)
    data = json.loads(_freeze_path(vault_file).read_text())
    assert "keys" in data
    assert "timestamp" in data


def test_freeze_timestamp_format(vault_file: Path) -> None:
    result = freeze_vault(vault_file, PASSPHRASE)
    assert "T" in result.timestamp
    assert result.timestamp.endswith("Z")


def test_load_freeze_returns_dict(vault_file: Path) -> None:
    freeze_vault(vault_file, PASSPHRASE)
    data = load_freeze(vault_file)
    assert isinstance(data, dict)


def test_load_freeze_missing_raises(vault_file: Path) -> None:
    with pytest.raises(FreezeError):
        load_freeze(vault_file)


def test_diff_freeze_no_drift(vault_file: Path) -> None:
    freeze_vault(vault_file, PASSPHRASE)
    result = diff_freeze(vault_file, PASSPHRASE)
    assert result["added"] == {}
    assert result["removed"] == {}
    assert result["changed"] == {}


def test_diff_freeze_detects_added_key(vault_file: Path, tmp_path: Path) -> None:
    freeze_vault(vault_file, PASSPHRASE)
    # Add a new key to the vault
    env = tmp_path / ".env"
    env.write_text("API_KEY=abc123\nDEBUG=true\nNEW_KEY=hello\n")
    v = Vault(env)
    v.lock(PASSPHRASE)
    result = diff_freeze(vault_file, PASSPHRASE)
    assert "NEW_KEY" in result["added"]


def test_diff_freeze_detects_changed_value(vault_file: Path, tmp_path: Path) -> None:
    freeze_vault(vault_file, PASSPHRASE)
    env = tmp_path / ".env"
    env.write_text("API_KEY=changed\nDEBUG=true\n")
    v = Vault(env)
    v.lock(PASSPHRASE)
    result = diff_freeze(vault_file, PASSPHRASE)
    assert "API_KEY" in result["changed"]
    assert result["changed"]["API_KEY"]["before"] == "abc123"


def test_freeze_vault_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FreezeError):
        freeze_vault(tmp_path / "nonexistent.vault", PASSPHRASE)


def test_freeze_result_as_dict(vault_file: Path) -> None:
    result = freeze_vault(vault_file, PASSPHRASE)
    d = result.as_dict()
    assert "vault_path" in d
    assert "freeze_path" in d
    assert "keys" in d
    assert "timestamp" in d
