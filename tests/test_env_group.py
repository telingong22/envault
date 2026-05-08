"""Tests for envault.env_group."""
import json
import pytest
from pathlib import Path

from envault.env_group import (
    GroupError,
    add_to_group,
    remove_from_group,
    list_groups,
    delete_group,
    _groups_path,
)


@pytest.fixture
def vault_file(tmp_path):
    p = tmp_path / "test.vault"
    p.write_bytes(b"fake-vault-content")
    return p


def test_add_to_group_returns_list(vault_file):
    result = add_to_group(vault_file, "backend", ["DB_URL", "DB_PASS"])
    assert isinstance(result, list)


def test_add_to_group_contains_keys(vault_file):
    result = add_to_group(vault_file, "backend", ["DB_URL", "DB_PASS"])
    assert "DB_URL" in result
    assert "DB_PASS" in result


def test_add_to_group_creates_json_file(vault_file):
    add_to_group(vault_file, "backend", ["DB_URL"])
    assert _groups_path(vault_file).exists()


def test_add_to_group_idempotent(vault_file):
    add_to_group(vault_file, "backend", ["DB_URL"])
    result = add_to_group(vault_file, "backend", ["DB_URL"])
    assert result.count("DB_URL") == 1


def test_add_to_group_merges_keys(vault_file):
    add_to_group(vault_file, "backend", ["DB_URL"])
    result = add_to_group(vault_file, "backend", ["DB_PASS"])
    assert "DB_URL" in result
    assert "DB_PASS" in result


def test_add_to_group_empty_name_raises(vault_file):
    with pytest.raises(GroupError):
        add_to_group(vault_file, "", ["DB_URL"])


def test_add_to_group_empty_keys_raises(vault_file):
    with pytest.raises(GroupError):
        add_to_group(vault_file, "backend", [])


def test_list_groups_returns_dict(vault_file):
    add_to_group(vault_file, "backend", ["DB_URL"])
    result = list_groups(vault_file)
    assert isinstance(result, dict)


def test_list_groups_empty_when_no_file(vault_file):
    result = list_groups(vault_file)
    assert result == {}


def test_list_groups_contains_added_group(vault_file):
    add_to_group(vault_file, "frontend", ["API_KEY"])
    groups = list_groups(vault_file)
    assert "frontend" in groups


def test_remove_from_group_returns_remaining(vault_file):
    add_to_group(vault_file, "backend", ["DB_URL", "DB_PASS"])
    remaining = remove_from_group(vault_file, "backend", ["DB_URL"])
    assert "DB_URL" not in remaining
    assert "DB_PASS" in remaining


def test_remove_all_keys_deletes_group(vault_file):
    add_to_group(vault_file, "backend", ["DB_URL"])
    remove_from_group(vault_file, "backend", ["DB_URL"])
    groups = list_groups(vault_file)
    assert "backend" not in groups


def test_remove_from_nonexistent_group_raises(vault_file):
    with pytest.raises(GroupError):
        remove_from_group(vault_file, "ghost", ["KEY"])


def test_delete_group_removes_it(vault_file):
    add_to_group(vault_file, "ops", ["SECRET"])
    delete_group(vault_file, "ops")
    assert "ops" not in list_groups(vault_file)


def test_delete_nonexistent_group_raises(vault_file):
    with pytest.raises(GroupError):
        delete_group(vault_file, "nonexistent")
