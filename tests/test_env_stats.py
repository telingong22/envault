"""Tests for envault.env_stats."""
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_stats import StatsResult, StatsError, compute_stats

PASSPHRASE = "test-secret"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(
        "# database config\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_PASS=\n"
        "\n"
        "API_KEY=supersecret\n"
        "API_KEY=duplicate\n"
        "LONG_VALUE_KEY=averylongvaluethatexceedsothers\n",
        encoding="utf-8",
    )
    v = Vault(env)
    v.lock(PASSPHRASE)
    return tmp_path / ".env.vault"


def test_compute_stats_returns_stats_result(vault_file):
    result = compute_stats(vault_file, PASSPHRASE)
    assert isinstance(result, StatsResult)


def test_compute_stats_vault_path_in_result(vault_file):
    result = compute_stats(vault_file, PASSPHRASE)
    assert str(vault_file) in result.vault_path


def test_compute_stats_total_keys(vault_file):
    result = compute_stats(vault_file, PASSPHRASE)
    # DB_HOST, DB_PORT, DB_PASS, API_KEY (counted once), LONG_VALUE_KEY
    assert result.total_keys == 5


def test_compute_stats_empty_values(vault_file):
    result = compute_stats(vault_file, PASSPHRASE)
    assert "DB_PASS" in result.empty_values


def test_compute_stats_empty_count(vault_file):
    result = compute_stats(vault_file, PASSPHRASE)
    assert result.empty_count == 1


def test_compute_stats_commented_lines(vault_file):
    result = compute_stats(vault_file, PASSPHRASE)
    assert result.commented_lines == 1


def test_compute_stats_blank_lines(vault_file):
    result = compute_stats(vault_file, PASSPHRASE)
    assert result.blank_lines == 1


def test_compute_stats_duplicate_keys(vault_file):
    result = compute_stats(vault_file, PASSPHRASE)
    assert "API_KEY" in result.duplicate_keys


def test_compute_stats_duplicate_count(vault_file):
    result = compute_stats(vault_file, PASSPHRASE)
    assert result.duplicate_count == 1


def test_compute_stats_longest_key(vault_file):
    result = compute_stats(vault_file, PASSPHRASE)
    assert result.longest_key == "LONG_VALUE_KEY"


def test_compute_stats_longest_value_key(vault_file):
    result = compute_stats(vault_file, PASSPHRASE)
    assert result.longest_value_key == "LONG_VALUE_KEY"


def test_compute_stats_as_dict_has_expected_keys(vault_file):
    d = compute_stats(vault_file, PASSPHRASE).as_dict()
    for key in ("vault_path", "total_keys", "empty_count", "duplicate_count",
                "commented_lines", "blank_lines", "longest_key", "longest_value_key"):
        assert key in d


def test_compute_stats_missing_vault_raises(tmp_path):
    with pytest.raises(StatsError):
        compute_stats(tmp_path / "ghost.vault", PASSPHRASE)


def test_compute_stats_wrong_passphrase_raises(vault_file):
    with pytest.raises(StatsError):
        compute_stats(vault_file, "wrong-passphrase")
