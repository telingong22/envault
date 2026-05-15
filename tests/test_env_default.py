"""Tests for envault.env_default."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_default import apply_defaults, DefaultError, DefaultResult

PASSPHRASE = "test-passphrase"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("EXISTING_KEY=hello\nANOTHER=world\n")
    vault = tmp_path / ".env.vault"
    Vault(vault).lock(PASSPHRASE, env)
    env.unlink()
    return vault


def test_apply_defaults_returns_default_result(vault_file: Path) -> None:
    result = apply_defaults(vault_file, PASSPHRASE, {"NEW_KEY": "default_val"})
    assert isinstance(result, DefaultResult)


def test_apply_defaults_vault_path_in_result(vault_file: Path) -> None:
    result = apply_defaults(vault_file, PASSPHRASE, {"NEW_KEY": "v"})
    assert result.vault_path == vault_file


def test_new_key_appears_in_applied(vault_file: Path) -> None:
    result = apply_defaults(vault_file, PASSPHRASE, {"BRAND_NEW": "42"})
    assert "BRAND_NEW" in result.applied


def test_existing_key_appears_in_skipped(vault_file: Path) -> None:
    result = apply_defaults(vault_file, PASSPHRASE, {"EXISTING_KEY": "override"})
    assert "EXISTING_KEY" in result.skipped


def test_existing_key_not_in_applied(vault_file: Path) -> None:
    result = apply_defaults(vault_file, PASSPHRASE, {"EXISTING_KEY": "override"})
    assert "EXISTING_KEY" not in result.applied


def test_new_key_persists_after_unlock(vault_file: Path, tmp_path: Path) -> None:
    apply_defaults(vault_file, PASSPHRASE, {"INJECTED": "yes"})
    env_out = tmp_path / "out.env"
    Vault(vault_file).unlock(PASSPHRASE, env_out)
    content = env_out.read_text()
    assert "INJECTED=yes" in content


def test_existing_key_value_unchanged(vault_file: Path, tmp_path: Path) -> None:
    apply_defaults(vault_file, PASSPHRASE, {"EXISTING_KEY": "CHANGED"})
    env_out = tmp_path / "out.env"
    Vault(vault_file).unlock(PASSPHRASE, env_out)
    content = env_out.read_text()
    assert "EXISTING_KEY=hello" in content


def test_has_changes_true_when_applied(vault_file: Path) -> None:
    result = apply_defaults(vault_file, PASSPHRASE, {"FRESH": "1"})
    assert result.has_changes() is True


def test_has_changes_false_when_all_skipped(vault_file: Path) -> None:
    result = apply_defaults(vault_file, PASSPHRASE, {"EXISTING_KEY": "x"})
    assert result.has_changes() is False


def test_as_dict_contains_expected_keys(vault_file: Path) -> None:
    result = apply_defaults(vault_file, PASSPHRASE, {"K": "v"})
    d = result.as_dict()
    assert set(d.keys()) == {"vault_path", "applied", "skipped"}


def test_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(DefaultError, match="Vault not found"):
        apply_defaults(tmp_path / "ghost.vault", PASSPHRASE, {"K": "v"})


def test_empty_defaults_raises(vault_file: Path) -> None:
    with pytest.raises(DefaultError, match="No defaults provided"):
        apply_defaults(vault_file, PASSPHRASE, {})
