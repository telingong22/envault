"""Tests for envault.env_comment."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_comment import CommentResult, CommentError, set_comments

PASSPHRASE = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("API_KEY=abc123\nDB_PASS=secret\nDEBUG=true\n")
    v = Vault(env)
    v.lock(PASSPHRASE)
    return tmp_path / ".env.vault"


def test_set_comment_returns_comment_result(vault_file: Path) -> None:
    result = set_comments(vault_file, PASSPHRASE, {"API_KEY": "my api key"})
    assert isinstance(result, CommentResult)


def test_set_comment_key_in_updated(vault_file: Path) -> None:
    result = set_comments(vault_file, PASSPHRASE, {"API_KEY": "my api key"})
    assert "API_KEY" in result.updated


def test_set_comment_vault_path_in_result(vault_file: Path) -> None:
    result = set_comments(vault_file, PASSPHRASE, {"API_KEY": "note"})
    assert result.vault_path == vault_file


def test_comment_appears_after_unlock(vault_file: Path, tmp_path: Path) -> None:
    set_comments(vault_file, PASSPHRASE, {"DB_PASS": "database password"})
    env = tmp_path / ".env"
    v = Vault(env)
    v.unlock(PASSPHRASE)
    content = env.read_text()
    assert "# database password" in content


def test_multiple_keys_updated(vault_file: Path) -> None:
    result = set_comments(
        vault_file, PASSPHRASE, {"API_KEY": "key", "DEBUG": "toggle"}
    )
    assert "API_KEY" in result.updated
    assert "DEBUG" in result.updated


def test_remove_comment_sets_none(vault_file: Path, tmp_path: Path) -> None:
    # First add a comment
    set_comments(vault_file, PASSPHRASE, {"API_KEY": "will be removed"})
    # Then remove it
    set_comments(vault_file, PASSPHRASE, {"API_KEY": None})
    env = tmp_path / ".env"
    Vault(env).unlock(PASSPHRASE)
    content = env.read_text()
    assert "will be removed" not in content


def test_unknown_key_raises(vault_file: Path) -> None:
    with pytest.raises(CommentError, match="Key not found"):
        set_comments(vault_file, PASSPHRASE, {"NONEXISTENT": "oops"})


def test_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(CommentError, match="Vault not found"):
        set_comments(tmp_path / "ghost.vault", PASSPHRASE, {"X": "y"})


def test_as_dict_contains_expected_keys(vault_file: Path) -> None:
    result = set_comments(vault_file, PASSPHRASE, {"API_KEY": "test"})
    d = result.as_dict()
    assert "vault_path" in d
    assert "updated" in d
    assert "unchanged" in d


def test_unchanged_key_not_in_updated(vault_file: Path) -> None:
    # Add comment first so re-applying same comment counts as unchanged
    set_comments(vault_file, PASSPHRASE, {"API_KEY": "stable"})
    result = set_comments(vault_file, PASSPHRASE, {"API_KEY": "stable"})
    assert "API_KEY" not in result.updated
    assert "API_KEY" in result.unchanged
