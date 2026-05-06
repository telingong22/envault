"""Tests for envault.search."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.search import search_vault, SearchError, SearchResult, SearchMatch


PASSPHRASE = "hunter2"
ENV_CONTENT = """DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=supersecret
API_KEY=abc123
DEBUG=true
"""


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    vault = Vault(env)
    return vault.lock(PASSPHRASE)


def test_search_returns_search_result(vault_file):
    result = search_vault(vault_file, PASSPHRASE, "DB")
    assert isinstance(result, SearchResult)


def test_search_keys_by_default(vault_file):
    result = search_vault(vault_file, PASSPHRASE, "DB")
    keys = [m.key for m in result.matches]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "DB_PASSWORD" in keys


def test_search_excludes_non_matching_keys(vault_file):
    result = search_vault(vault_file, PASSPHRASE, "DB")
    keys = [m.key for m in result.matches]
    assert "API_KEY" not in keys
    assert "DEBUG" not in keys


def test_search_values(vault_file):
    result = search_vault(vault_file, PASSPHRASE, "secret", search_keys=False, search_values=True)
    assert result.found
    keys = [m.key for m in result.matches]
    assert "DB_PASSWORD" in keys


def test_search_match_in_field(vault_file):
    result = search_vault(vault_file, PASSPHRASE, "DB", search_keys=True, search_values=False)
    for m in result.matches:
        assert m.match_in in ("key", "value", "both")


def test_search_case_insensitive_by_default(vault_file):
    result = search_vault(vault_file, PASSPHRASE, "db_host")
    assert result.found


def test_search_case_sensitive(vault_file):
    result = search_vault(vault_file, PASSPHRASE, "db_host", case_sensitive=True)
    assert not result.found


def test_search_no_matches(vault_file):
    result = search_vault(vault_file, PASSPHRASE, "NONEXISTENT_KEY_XYZ")
    assert not result.found
    assert result.matches == []


def test_search_summary_with_matches(vault_file):
    result = search_vault(vault_file, PASSPHRASE, "DB")
    summary = result.summary()
    assert "DB" in summary
    assert "match" in summary


def test_search_summary_no_matches(vault_file):
    result = search_vault(vault_file, PASSPHRASE, "NOTHING")
    assert "No matches" in result.summary()


def test_search_missing_vault(tmp_path):
    with pytest.raises(SearchError, match="not found"):
        search_vault(tmp_path / "missing.vault", PASSPHRASE, "KEY")


def test_search_invalid_pattern(vault_file):
    with pytest.raises(SearchError, match="Invalid pattern"):
        search_vault(vault_file, PASSPHRASE, "[unclosed")


def test_search_wrong_passphrase(vault_file):
    with pytest.raises(SearchError, match="Could not decrypt"):
        search_vault(vault_file, "wrongpass", "DB")
