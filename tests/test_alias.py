"""Tests for envault.alias."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.alias import (
    AliasError,
    set_alias,
    remove_alias,
    list_aliases,
    resolve_alias,
    aliases_for_key,
    _aliases_path,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    p.write_bytes(b"dummy-vault-content")
    return p


def test_set_alias_returns_dict(vault_file: Path) -> None:
    result = set_alias(vault_file, "db", "DATABASE_URL")
    assert isinstance(result, dict)


def test_set_alias_creates_aliases_file(vault_file: Path) -> None:
    set_alias(vault_file, "db", "DATABASE_URL")
    assert _aliases_path(vault_file).exists()


def test_set_alias_persists(vault_file: Path) -> None:
    set_alias(vault_file, "db", "DATABASE_URL")
    data = json.loads(_aliases_path(vault_file).read_text())
    assert data["db"] == "DATABASE_URL"


def test_set_alias_overwrites_existing(vault_file: Path) -> None:
    set_alias(vault_file, "db", "DATABASE_URL")
    set_alias(vault_file, "db", "REPLICA_URL")
    assert list_aliases(vault_file)["db"] == "REPLICA_URL"


def test_set_alias_empty_name_raises(vault_file: Path) -> None:
    with pytest.raises(AliasError, match="empty"):
        set_alias(vault_file, "  ", "DATABASE_URL")


def test_set_alias_empty_key_raises(vault_file: Path) -> None:
    with pytest.raises(AliasError, match="empty"):
        set_alias(vault_file, "db", "")


def test_set_alias_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(AliasError, match="Vault not found"):
        set_alias(tmp_path / "no.vault", "db", "KEY")


def test_remove_alias(vault_file: Path) -> None:
    set_alias(vault_file, "db", "DATABASE_URL")
    remaining = remove_alias(vault_file, "db")
    assert "db" not in remaining


def test_remove_alias_unknown_raises(vault_file: Path) -> None:
    with pytest.raises(AliasError, match="not found"):
        remove_alias(vault_file, "ghost")


def test_list_aliases_empty(vault_file: Path) -> None:
    assert list_aliases(vault_file) == {}


def test_list_aliases_multiple(vault_file: Path) -> None:
    set_alias(vault_file, "db", "DATABASE_URL")
    set_alias(vault_file, "cache", "REDIS_URL")
    result = list_aliases(vault_file)
    assert result == {"db": "DATABASE_URL", "cache": "REDIS_URL"}


def test_resolve_alias(vault_file: Path) -> None:
    set_alias(vault_file, "db", "DATABASE_URL")
    assert resolve_alias(vault_file, "db") == "DATABASE_URL"


def test_resolve_alias_unknown_raises(vault_file: Path) -> None:
    with pytest.raises(AliasError, match="not defined"):
        resolve_alias(vault_file, "nope")


def test_aliases_for_key(vault_file: Path) -> None:
    set_alias(vault_file, "db", "DATABASE_URL")
    set_alias(vault_file, "primary", "DATABASE_URL")
    set_alias(vault_file, "cache", "REDIS_URL")
    result = aliases_for_key(vault_file, "DATABASE_URL")
    assert sorted(result) == ["db", "primary"]


def test_aliases_for_key_none_found(vault_file: Path) -> None:
    assert aliases_for_key(vault_file, "MISSING_KEY") == []
