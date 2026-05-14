"""Tests for envault.env_format."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_format import FormatError, FormatResult, _format_lines, format_vault
from envault.vault import Vault

PASSPHRASE = "test-passphrase"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost  \nDB_PORT = 5432\nSECRET=abc \n")
    v = Vault(env)
    vault = tmp_path / ".env.vault"
    v.lock(PASSPHRASE, vault_path=vault)
    return vault


# --- _format_lines unit tests ---


def test_format_lines_removes_trailing_whitespace():
    text = "KEY=value   \n"
    formatted, changes = _format_lines(text)
    assert "   " not in formatted
    assert any("trailing" in c for c in changes)


def test_format_lines_normalises_spaces_around_equals():
    text = "KEY = value\n"
    formatted, changes = _format_lines(text)
    assert "KEY=value" in formatted
    assert any("normalised" in c for c in changes)


def test_format_lines_preserves_comments():
    text = "# a comment\nKEY=val\n"
    formatted, _ = _format_lines(text)
    assert "# a comment" in formatted


def test_format_lines_preserves_blank_lines():
    text = "KEY=val\n\nOTHER=x\n"
    formatted, _ = _format_lines(text)
    assert "\n\n" in formatted


def test_format_lines_no_changes_for_clean_file():
    text = "KEY=value\nOTHER=123\n"
    _, changes = _format_lines(text)
    assert changes == []


def test_format_lines_ensures_trailing_newline():
    text = "KEY=val"
    formatted, _ = _format_lines(text)
    assert formatted.endswith("\n")


# --- format_vault integration tests ---


def test_format_vault_returns_format_result(vault_file: Path):
    result = format_vault(vault_file, PASSPHRASE)
    assert isinstance(result, FormatResult)


def test_format_vault_result_contains_vault_path(vault_file: Path):
    result = format_vault(vault_file, PASSPHRASE)
    assert result.vault_path == vault_file


def test_format_vault_detects_changes(vault_file: Path):
    result = format_vault(vault_file, PASSPHRASE)
    assert result.changed


def test_format_vault_vault_still_decryptable(vault_file: Path, tmp_path: Path):
    format_vault(vault_file, PASSPHRASE)
    env_out = tmp_path / "out.env"
    v = Vault(env_out)
    content = v.unlock(PASSPHRASE, vault_path=vault_file)
    assert "DB_HOST" in content
    assert "DB_PORT" in content


def test_format_vault_values_preserved(vault_file: Path, tmp_path: Path):
    format_vault(vault_file, PASSPHRASE)
    env_out = tmp_path / "out.env"
    v = Vault(env_out)
    content = v.unlock(PASSPHRASE, vault_path=vault_file)
    assert "localhost" in content
    assert "5432" in content


def test_format_vault_missing_vault_raises(tmp_path: Path):
    with pytest.raises(FormatError):
        format_vault(tmp_path / "nonexistent.vault", PASSPHRASE)
