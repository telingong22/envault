"""Tests for envault.env_filter."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.vault import Vault
from envault.env_filter import FilterError, FilterResult, filter_keys

PASSPHRASE = "test-passphrase"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "AWS_ACCESS_KEY=AKIA123\n"
        "AWS_SECRET=supersecret\n"
        "APP_DEBUG=true\n"
        "APP_NAME=myapp\n"
    )
    v = Vault(tmp_path / ".env.vault")
    v.lock(env, PASSPHRASE)
    return tmp_path / ".env.vault"


def test_filter_returns_filter_result(vault_file: Path) -> None:
    result = filter_keys(vault_file, PASSPHRASE, prefix="DB_")
    assert isinstance(result, FilterResult)


def test_filter_result_contains_vault_path(vault_file: Path) -> None:
    result = filter_keys(vault_file, PASSPHRASE, prefix="DB_")
    assert result.vault_path == vault_file


def test_filter_by_prefix(vault_file: Path) -> None:
    result = filter_keys(vault_file, PASSPHRASE, prefix="DB_")
    assert set(result.matched.keys()) == {"DB_HOST", "DB_PORT"}


def test_filter_by_glob_pattern(vault_file: Path) -> None:
    result = filter_keys(vault_file, PASSPHRASE, pattern="AWS_*")
    assert set(result.matched.keys()) == {"AWS_ACCESS_KEY", "AWS_SECRET"}


def test_filter_by_regex(vault_file: Path) -> None:
    result = filter_keys(vault_file, PASSPHRASE, regex=r"^APP_")
    assert set(result.matched.keys()) == {"APP_DEBUG", "APP_NAME"}


def test_filter_combined_pattern_and_prefix(vault_file: Path) -> None:
    result = filter_keys(vault_file, PASSPHRASE, prefix="DB_", pattern="*PORT*")
    assert list(result.matched.keys()) == ["DB_PORT"]


def test_filter_no_criteria_raises(vault_file: Path) -> None:
    with pytest.raises(FilterError):
        filter_keys(vault_file, PASSPHRASE)


def test_filter_total_keys_count(vault_file: Path) -> None:
    result = filter_keys(vault_file, PASSPHRASE, prefix="AWS_")
    assert result.total_keys == 6


def test_filter_matched_values_accessible(vault_file: Path) -> None:
    result = filter_keys(vault_file, PASSPHRASE, prefix="DB_")
    assert result.matched["DB_HOST"] == "localhost"
    assert result.matched["DB_PORT"] == "5432"


def test_filter_as_dict_keys(vault_file: Path) -> None:
    result = filter_keys(vault_file, PASSPHRASE, prefix="AWS_")
    d = result.as_dict()
    assert "vault_path" in d
    assert "matched" in d
    assert "match_count" in d
    assert "total_keys" in d


def test_filter_no_match_returns_empty(vault_file: Path) -> None:
    result = filter_keys(vault_file, PASSPHRASE, prefix="NONEXISTENT_")
    assert result.matched == {}
