"""Tests for envault.env_trim."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_trim import TrimResult, TrimError, trim_values, _trim_lines

PASSPHRASE = "test-passphrase"


@pytest.fixture
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(
        "API_KEY=  secret123  \n"
        "DB_HOST=localhost\n"
        "DB_PORT=  5432\n"
        "# a comment\n"
        "EMPTY=\n"
    )
    v = Vault(tmp_path / ".env.vault")
    v.lock(PASSPHRASE, src=env)
    return tmp_path / ".env.vault"


# --- unit tests for _trim_lines ---

def test_trim_lines_removes_leading_whitespace():
    lines = ["KEY=  value\n"]
    new_lines, trimmed, _ = _trim_lines(lines)
    assert new_lines == ["KEY=value\n"]
    assert "KEY" in trimmed


def test_trim_lines_removes_trailing_whitespace():
    lines = ["KEY=value   \n"]
    new_lines, trimmed, _ = _trim_lines(lines)
    assert new_lines == ["KEY=value\n"]
    assert "KEY" in trimmed


def test_trim_lines_leaves_clean_values_unchanged():
    lines = ["KEY=value\n"]
    _, trimmed, unchanged = _trim_lines(lines)
    assert trimmed == []
    assert "KEY" in unchanged


def test_trim_lines_ignores_comments():
    lines = ["# KEY=  value\n"]
    new_lines, trimmed, unchanged = _trim_lines(lines)
    assert new_lines == ["# KEY=  value\n"]
    assert trimmed == []


def test_trim_lines_ignores_blank_lines():
    lines = ["\n", "  \n"]
    new_lines, trimmed, _ = _trim_lines(lines)
    assert new_lines == ["\n", "  \n"]
    assert trimmed == []


# --- integration tests for trim_values ---

def test_trim_returns_trim_result(vault_file: Path):
    result = trim_values(vault_file, PASSPHRASE)
    assert isinstance(result, TrimResult)


def test_trim_result_contains_vault_path(vault_file: Path):
    result = trim_values(vault_file, PASSPHRASE)
    assert result.vault_path == str(vault_file)


def test_trim_detects_trimmed_keys(vault_file: Path):
    result = trim_values(vault_file, PASSPHRASE)
    assert "API_KEY" in result.trimmed
    assert "DB_PORT" in result.trimmed


def test_trim_unchanged_keys_not_in_trimmed(vault_file: Path):
    result = trim_values(vault_file, PASSPHRASE)
    assert "DB_HOST" not in result.trimmed
    assert "DB_HOST" in result.unchanged


def test_trim_has_changes_true_when_trimmed(vault_file: Path):
    result = trim_values(vault_file, PASSPHRASE)
    assert result.has_changes() is True


def test_trim_values_persisted(vault_file: Path, tmp_path: Path):
    trim_values(vault_file, PASSPHRASE)
    dest = tmp_path / "out.env"
    Vault(vault_file).unlock(PASSPHRASE, dest=dest)
    content = dest.read_text()
    assert "API_KEY=secret123" in content
    assert "DB_PORT=5432" in content


def test_trim_missing_vault_raises(tmp_path: Path):
    with pytest.raises(TrimError, match="Vault not found"):
        trim_values(tmp_path / "ghost.vault", PASSPHRASE)


def test_trim_as_dict_keys(vault_file: Path):
    result = trim_values(vault_file, PASSPHRASE)
    d = result.as_dict()
    assert {"vault_path", "trimmed", "unchanged", "has_changes"} <= d.keys()
