"""Tests for envault.env_copy."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_copy import copy_keys, CopyError, CopyResult


PASSPHRASE_A = "passA"
PASSPHRASE_B = "passB"


def _make_vault(tmp_path: Path, name: str, passphrase: str, content: str) -> Path:
    env = tmp_path / f"{name}.env"
    vault = tmp_path / f"{name}.vault"
    env.write_text(content)
    Vault(env, vault).lock(passphrase)
    return vault


@pytest.fixture()
def vault_a(tmp_path):
    return _make_vault(tmp_path, "a", PASSPHRASE_A, "FOO=hello\nBAR=world\n")


@pytest.fixture()
def vault_b(tmp_path):
    return _make_vault(tmp_path, "b", PASSPHRASE_B, "BAZ=existing\n")


def test_copy_returns_copy_result(vault_a, vault_b):
    result = copy_keys(vault_a, PASSPHRASE_A, vault_b, PASSPHRASE_B, ["FOO"])
    assert isinstance(result, CopyResult)


def test_copy_copied_list_contains_key(vault_a, vault_b):
    result = copy_keys(vault_a, PASSPHRASE_A, vault_b, PASSPHRASE_B, ["FOO"])
    assert "FOO" in result.copied


def test_copy_key_present_in_destination_after_copy(vault_a, vault_b, tmp_path):
    copy_keys(vault_a, PASSPHRASE_A, vault_b, PASSPHRASE_B, ["FOO"])
    dst_env = vault_b.with_suffix(".env")
    dst = Vault(dst_env, vault_b)
    content = dst.unlock(PASSPHRASE_B)
    assert "FOO=hello" in content


def test_copy_preserves_existing_destination_keys(vault_a, vault_b, tmp_path):
    copy_keys(vault_a, PASSPHRASE_A, vault_b, PASSPHRASE_B, ["FOO"])
    dst_env = vault_b.with_suffix(".env")
    dst = Vault(dst_env, vault_b)
    content = dst.unlock(PASSPHRASE_B)
    assert "BAZ=existing" in content


def test_copy_multiple_keys(vault_a, vault_b, tmp_path):
    result = copy_keys(vault_a, PASSPHRASE_A, vault_b, PASSPHRASE_B, ["FOO", "BAR"])
    assert set(result.copied) == {"FOO", "BAR"}


def test_copy_skips_existing_key_without_overwrite(tmp_path):
    src = _make_vault(tmp_path, "src", PASSPHRASE_A, "KEY=new_value\n")
    dst = _make_vault(tmp_path, "dst", PASSPHRASE_B, "KEY=old_value\n")
    result = copy_keys(src, PASSPHRASE_A, dst, PASSPHRASE_B, ["KEY"], overwrite=False)
    assert "KEY" in result.skipped
    assert "KEY" not in result.copied


def test_copy_overwrites_when_flag_set(tmp_path):
    src = _make_vault(tmp_path, "src", PASSPHRASE_A, "KEY=new_value\n")
    dst = _make_vault(tmp_path, "dst", PASSPHRASE_B, "KEY=old_value\n")
    result = copy_keys(src, PASSPHRASE_A, dst, PASSPHRASE_B, ["KEY"], overwrite=True)
    assert "KEY" in result.copied
    dst_env = dst.with_suffix(".env")
    content = Vault(dst_env, dst).unlock(PASSPHRASE_B)
    assert "KEY=new_value" in content


def test_copy_missing_source_vault_raises(tmp_path, vault_b):
    with pytest.raises(CopyError, match="Source vault not found"):
        copy_keys(tmp_path / "ghost.vault", PASSPHRASE_A, vault_b, PASSPHRASE_B, ["X"])


def test_copy_missing_destination_vault_raises(tmp_path, vault_a):
    with pytest.raises(CopyError, match="Destination vault not found"):
        copy_keys(vault_a, PASSPHRASE_A, tmp_path / "ghost.vault", PASSPHRASE_B, ["FOO"])


def test_copy_missing_key_in_source_raises(vault_a, vault_b):
    with pytest.raises(CopyError, match="Key 'MISSING' not found"):
        copy_keys(vault_a, PASSPHRASE_A, vault_b, PASSPHRASE_B, ["MISSING"])


def test_as_dict_contains_expected_keys(vault_a, vault_b):
    result = copy_keys(vault_a, PASSPHRASE_A, vault_b, PASSPHRASE_B, ["FOO"])
    d = result.as_dict()
    assert set(d.keys()) == {"source", "destination", "copied", "skipped"}
