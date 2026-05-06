"""Tests for envault.merge."""

from pathlib import Path

import pytest

from envault.merge import (
    MergeError,
    MergeResult,
    MergeStrategy,
    merge_vaults,
)
from envault.vault import Vault

PASS_A = "secret-a"
PASS_B = "secret-b"


@pytest.fixture()
def base_vault(tmp_path: Path) -> Path:
    env = tmp_path / "base.env"
    env.write_text("DB_HOST=localhost\nDB_PORT=5432\nSHARED=old\n")
    v = Vault(tmp_path / "base.vault")
    v.lock(PASS_A, env_path=env)
    return tmp_path / "base.vault"


@pytest.fixture()
def other_vault(tmp_path: Path) -> Path:
    env = tmp_path / "other.env"
    env.write_text("DB_HOST=remotehost\nAPI_KEY=xyz\nSHARED=new\n")
    v = Vault(tmp_path / "other.vault")
    v.lock(PASS_B, env_path=env)
    return tmp_path / "other.vault"


def test_merge_returns_merge_result(base_vault, other_vault, tmp_path):
    out = tmp_path / "merged.env"
    result = merge_vaults(base_vault, other_vault, PASS_A, PASS_B, out)
    assert isinstance(result, MergeResult)


def test_merge_output_file_created(base_vault, other_vault, tmp_path):
    out = tmp_path / "merged.env"
    merge_vaults(base_vault, other_vault, PASS_A, PASS_B, out)
    assert out.exists()


def test_merge_added_keys(base_vault, other_vault, tmp_path):
    out = tmp_path / "merged.env"
    result = merge_vaults(base_vault, other_vault, PASS_A, PASS_B, out)
    assert "API_KEY" in result.added


def test_merge_removed_keys(base_vault, other_vault, tmp_path):
    out = tmp_path / "merged.env"
    result = merge_vaults(base_vault, other_vault, PASS_A, PASS_B, out)
    assert "DB_PORT" in result.removed


def test_merge_conflicted_keys(base_vault, other_vault, tmp_path):
    out = tmp_path / "merged.env"
    result = merge_vaults(base_vault, other_vault, PASS_A, PASS_B, out)
    assert "DB_HOST" in result.conflicted
    assert "SHARED" in result.conflicted


def test_merge_strategy_ours_keeps_base_value(base_vault, other_vault, tmp_path):
    out = tmp_path / "merged.env"
    result = merge_vaults(
        base_vault, other_vault, PASS_A, PASS_B, out, strategy=MergeStrategy.OURS
    )
    assert result.merged["DB_HOST"] == "localhost"
    assert result.merged["SHARED"] == "old"


def test_merge_strategy_theirs_takes_other_value(base_vault, other_vault, tmp_path):
    out = tmp_path / "merged.env"
    result = merge_vaults(
        base_vault, other_vault, PASS_A, PASS_B, out, strategy=MergeStrategy.THEIRS
    )
    assert result.merged["DB_HOST"] == "remotehost"
    assert result.merged["SHARED"] == "new"


def test_merge_strategy_theirs_drops_base_only_keys(base_vault, other_vault, tmp_path):
    out = tmp_path / "merged.env"
    result = merge_vaults(
        base_vault, other_vault, PASS_A, PASS_B, out, strategy=MergeStrategy.THEIRS
    )
    assert "DB_PORT" not in result.merged


def test_merge_has_conflicts_property(base_vault, other_vault, tmp_path):
    out = tmp_path / "merged.env"
    result = merge_vaults(base_vault, other_vault, PASS_A, PASS_B, out)
    assert result.has_conflicts is True


def test_merge_summary_contains_counts(base_vault, other_vault, tmp_path):
    out = tmp_path / "merged.env"
    result = merge_vaults(base_vault, other_vault, PASS_A, PASS_B, out)
    summary = result.summary()
    assert "Added" in summary
    assert "Removed" in summary
    assert "Conflicts" in summary


def test_merge_raises_on_unlocked_vault(tmp_path):
    env = tmp_path / "plain.env"
    env.write_text("KEY=val\n")
    other = tmp_path / "other.vault"
    v = Vault(other)
    v.lock(PASS_B, env_path=env)
    with pytest.raises(MergeError):
        merge_vaults(env, other, PASS_A, PASS_B, tmp_path / "out.env")
