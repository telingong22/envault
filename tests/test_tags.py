"""Tests for envault.tags."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.tags import (
    TagError,
    add_tag,
    find_vaults_by_tag,
    list_tags,
    remove_tag,
    _tags_path,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    p.write_bytes(b"dummy vault content")
    return p


def test_add_tag_returns_list(vault_file: Path) -> None:
    result = add_tag(vault_file, "production")
    assert isinstance(result, list)
    assert "production" in result


def test_add_tag_creates_tags_file(vault_file: Path) -> None:
    add_tag(vault_file, "staging")
    assert _tags_path(vault_file).exists()


def test_add_tag_persists(vault_file: Path) -> None:
    add_tag(vault_file, "ci")
    assert "ci" in list_tags(vault_file)


def test_add_duplicate_tag_is_idempotent(vault_file: Path) -> None:
    add_tag(vault_file, "demo")
    result = add_tag(vault_file, "demo")
    assert result.count("demo") == 1


def test_add_tag_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(TagError, match="Vault not found"):
        add_tag(tmp_path / "ghost.vault", "x")


def test_add_empty_tag_raises(vault_file: Path) -> None:
    with pytest.raises(TagError, match="empty"):
        add_tag(vault_file, "   ")


def test_remove_tag(vault_file: Path) -> None:
    add_tag(vault_file, "old")
    remaining = remove_tag(vault_file, "old")
    assert "old" not in remaining
    assert "old" not in list_tags(vault_file)


def test_remove_nonexistent_tag_is_safe(vault_file: Path) -> None:
    result = remove_tag(vault_file, "ghost")
    assert "ghost" not in result


def test_list_tags_empty_by_default(vault_file: Path) -> None:
    assert list_tags(vault_file) == []


def test_list_tags_multiple(vault_file: Path) -> None:
    add_tag(vault_file, "a")
    add_tag(vault_file, "b")
    tags = list_tags(vault_file)
    assert "a" in tags and "b" in tags


def test_find_vaults_by_tag(tmp_path: Path) -> None:
    v1 = tmp_path / "one.vault"
    v2 = tmp_path / "two.vault"
    v1.write_bytes(b"v1")
    v2.write_bytes(b"v2")
    add_tag(v1, "prod")
    add_tag(v2, "dev")
    found = find_vaults_by_tag(tmp_path, "prod")
    assert v1 in found
    assert v2 not in found


def test_find_vaults_by_tag_no_match(tmp_path: Path) -> Path:
    v = tmp_path / "only.vault"
    v.write_bytes(b"x")
    add_tag(v, "staging")
    assert find_vaults_by_tag(tmp_path, "prod") == []


def test_corrupt_tags_file_raises(vault_file: Path) -> None:
    _tags_path(vault_file).write_text("NOT JSON")
    with pytest.raises(TagError, match="Corrupt"):
        list_tags(vault_file)
