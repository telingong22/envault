"""Tests for envault.env_patch."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.env_patch import PatchError, PatchResult, apply_patch
from envault.vault import Vault

PASSPHRASE = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\nDB_PORT=5432\nDEBUG=false\n")
    v = Vault(env)
    vp = v.lock(PASSPHRASE)
    env.unlink(missing_ok=True)
    return vp


def test_apply_patch_returns_patch_result(vault_file: Path) -> None:
    result = apply_patch(vault_file, PASSPHRASE, "DB_PORT=3306")
    assert isinstance(result, PatchResult)


def test_apply_patch_result_contains_vault_path(vault_file: Path) -> None:
    result = apply_patch(vault_file, PASSPHRASE, "DB_PORT=3306")
    assert result.vault_path == vault_file


def test_apply_patch_applied_list_contains_key(vault_file: Path) -> None:
    result = apply_patch(vault_file, PASSPHRASE, "DB_PORT=3306")
    assert "DB_PORT" in result.applied


def test_apply_patch_new_value_persists(vault_file: Path) -> None:
    apply_patch(vault_file, PASSPHRASE, "DB_PORT=9999")
    v = Vault(vault_file.parent / ".env")
    content = v.unlock(PASSPHRASE, write=False)
    assert "DB_PORT=9999" in content


def test_apply_patch_adds_new_key(vault_file: Path) -> None:
    apply_patch(vault_file, PASSPHRASE, "NEW_KEY=hello")
    v = Vault(vault_file.parent / ".env")
    content = v.unlock(PASSPHRASE, write=False)
    assert "NEW_KEY=hello" in content


def test_apply_patch_no_overwrite_skips_existing(vault_file: Path) -> None:
    result = apply_patch(vault_file, PASSPHRASE, "DB_HOST=newhost", overwrite=False)
    assert "DB_HOST" in result.skipped
    assert "DB_HOST" not in result.applied


def test_apply_patch_no_overwrite_keeps_original_value(vault_file: Path) -> None:
    apply_patch(vault_file, PASSPHRASE, "DB_HOST=newhost", overwrite=False)
    v = Vault(vault_file.parent / ".env")
    content = v.unlock(PASSPHRASE, write=False)
    assert "DB_HOST=localhost" in content


def test_apply_patch_keys_only_filters(vault_file: Path) -> None:
    result = apply_patch(
        vault_file,
        PASSPHRASE,
        "DB_PORT=1111\nDEBUG=true",
        keys_only=["DEBUG"],
    )
    assert "DEBUG" in result.applied
    assert "DB_PORT" not in result.applied


def test_apply_patch_dict_input(vault_file: Path) -> None:
    result = apply_patch(vault_file, PASSPHRASE, {"DB_HOST": "remotehost"})
    assert "DB_HOST" in result.applied


def test_apply_patch_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(PatchError):
        apply_patch(tmp_path / "no.vault", PASSPHRASE, "KEY=val")


def test_has_skipped_false_when_all_applied(vault_file: Path) -> None:
    result = apply_patch(vault_file, PASSPHRASE, "BRAND_NEW=1")
    assert result.has_skipped is False


def test_has_skipped_true_when_some_skipped(vault_file: Path) -> None:
    result = apply_patch(vault_file, PASSPHRASE, "DB_HOST=x", overwrite=False)
    assert result.has_skipped is True
