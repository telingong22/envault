"""Tests for envault.env_diff_apply."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_diff_apply import apply_diff, ApplyResult, ApplyError

PASSPHRASE = "test-secret"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\nDB_PORT=5432\nDEBUG=false\n")
    vf = tmp_path / ".env.vault"
    v = Vault(env, vf)
    v.lock(PASSPHRASE)
    env.unlink(missing_ok=True)
    return vf


def test_apply_diff_returns_apply_result(vault_file):
    result = apply_diff(vault_file, PASSPHRASE, {"DB_HOST": "localhost", "DB_PORT": "5432", "DEBUG": "false"})
    assert isinstance(result, ApplyResult)


def test_apply_diff_vault_path_in_result(vault_file):
    result = apply_diff(vault_file, PASSPHRASE, {})
    assert result.vault_path == str(vault_file)


def test_apply_diff_adds_new_key(vault_file):
    result = apply_diff(vault_file, PASSPHRASE, {"NEW_KEY": "hello"})
    assert "NEW_KEY" in result.added


def test_apply_diff_updates_existing_key(vault_file):
    result = apply_diff(vault_file, PASSPHRASE, {"DB_HOST": "remotehost"})
    assert "DB_HOST" in result.updated


def test_apply_diff_no_change_for_same_value(vault_file):
    result = apply_diff(vault_file, PASSPHRASE, {"DB_HOST": "localhost"})
    assert "DB_HOST" not in result.updated
    assert "DB_HOST" not in result.added


def test_apply_diff_remove_missing_flag(vault_file):
    result = apply_diff(vault_file, PASSPHRASE, {"DB_HOST": "localhost"}, remove_missing=True)
    assert "DB_PORT" in result.removed
    assert "DEBUG" in result.removed


def test_apply_diff_remove_missing_false_by_default(vault_file):
    result = apply_diff(vault_file, PASSPHRASE, {"DB_HOST": "localhost"})
    assert result.removed == []


def test_apply_diff_persists_new_key(vault_file):
    apply_diff(vault_file, PASSPHRASE, {"BRAND_NEW": "value99"})
    v = Vault(vault_file.with_suffix(".env"), vault_file)
    v.unlock(PASSPHRASE)
    content = vault_file.with_suffix(".env").read_text()
    assert "BRAND_NEW=value99" in content


def test_apply_diff_dry_run_does_not_modify_vault(vault_file):
    mtime_before = vault_file.stat().st_mtime
    apply_diff(vault_file, PASSPHRASE, {"EXTRA": "1"}, dry_run=True)
    mtime_after = vault_file.stat().st_mtime
    assert mtime_before == mtime_after


def test_apply_diff_missing_vault_raises(tmp_path):
    with pytest.raises(ApplyError):
        apply_diff(tmp_path / "nonexistent.vault", PASSPHRASE, {})


def test_apply_diff_has_changes_true_when_added(vault_file):
    result = apply_diff(vault_file, PASSPHRASE, {"NEW": "val"})
    assert result.has_changes() is True


def test_apply_diff_has_changes_false_when_noop(vault_file):
    result = apply_diff(vault_file, PASSPHRASE, {})
    assert result.has_changes() is False


def test_apply_diff_as_dict_keys(vault_file):
    result = apply_diff(vault_file, PASSPHRASE, {})
    d = result.as_dict()
    assert set(d.keys()) == {"vault_path", "added", "updated", "removed", "skipped", "has_changes"}
