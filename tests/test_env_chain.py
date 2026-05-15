"""Tests for envault.env_chain."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_chain import ChainError, ChainResult, resolve_key

PASS = "test-pass"


def _make_vault(tmp_path: Path, name: str, content: str) -> Path:
    env = tmp_path / f"{name}.env"
    vault = tmp_path / f"{name}.vault"
    env.write_text(content)
    Vault(env, vault).lock(PASS)
    env.unlink()
    return vault


@pytest.fixture()
def vault_a(tmp_path):
    return _make_vault(tmp_path, "a", "APP_ENV=production\nDB_HOST=prod-db\n")


@pytest.fixture()
def vault_b(tmp_path):
    return _make_vault(tmp_path, "b", "APP_ENV=staging\nDB_HOST=staging-db\nEXTRA=only-b\n")


def test_resolve_returns_chain_result(vault_a, vault_b):
    result = resolve_key("DB_HOST", [vault_a, vault_b], PASS)
    assert isinstance(result, ChainResult)


def test_resolve_first_vault_wins(vault_a, vault_b):
    result = resolve_key("APP_ENV", [vault_a, vault_b], PASS)
    assert result.value == "production"
    assert result.found_in == vault_a


def test_resolve_falls_through_to_second_vault(vault_a, vault_b):
    result = resolve_key("EXTRA", [vault_a, vault_b], PASS)
    assert result.found
    assert result.value == "only-b"
    assert result.found_in == vault_b


def test_resolve_missing_key_returns_not_found(vault_a, vault_b):
    result = resolve_key("NONEXISTENT", [vault_a, vault_b], PASS)
    assert not result.found
    assert result.value is None
    assert result.found_in is None


def test_resolve_checked_list_contains_all_vaults(vault_a, vault_b):
    result = resolve_key("NONEXISTENT", [vault_a, vault_b], PASS)
    assert vault_a in result.checked
    assert vault_b in result.checked


def test_resolve_empty_vaults_raises():
    with pytest.raises(ChainError):
        resolve_key("KEY", [], PASS)


def test_resolve_empty_key_raises(vault_a):
    with pytest.raises(ChainError):
        resolve_key("", [vault_a], PASS)


def test_resolve_missing_vault_raises(tmp_path, vault_a):
    ghost = tmp_path / "ghost.vault"
    with pytest.raises(ChainError, match="vault not found"):
        resolve_key("APP_ENV", [ghost], PASS)


def test_as_dict_structure(vault_a, vault_b):
    result = resolve_key("DB_HOST", [vault_a, vault_b], PASS)
    d = result.as_dict()
    assert "key" in d
    assert "value" in d
    assert "found" in d
    assert "found_in" in d
    assert "checked" in d
