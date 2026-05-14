"""Tests for envault.env_promote."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.vault import Vault
from envault.env_promote import PromoteError, PromoteResult, promote_keys


PASSPHRASE_A = "source-secret"
PASSPHRASE_B = "target-secret"


def _make_vault(tmp_path: Path, name: str, passphrase: str, content: str) -> Path:
    env = tmp_path / name
    env.write_text(content)
    v = Vault(env)
    v.lock(passphrase)
    vault_path = Path(str(env) + ".vault")
    return vault_path


@pytest.fixture()
def source_vault(tmp_path: Path) -> Path:
    return _make_vault(
        tmp_path, "source.env", PASSPHRASE_A,
        "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n",
    )


@pytest.fixture()
def target_vault(tmp_path: Path) -> Path:
    return _make_vault(
        tmp_path, "target.env", PASSPHRASE_B,
        "APP_ENV=production\nDB_HOST=prod-host\n",
    )


def test_promote_returns_promote_result(source_vault, target_vault):
    result = promote_keys(source_vault, PASSPHRASE_A, target_vault, PASSPHRASE_B)
    assert isinstance(result, PromoteResult)


def test_promote_result_contains_vault_paths(source_vault, target_vault):
    result = promote_keys(source_vault, PASSPHRASE_A, target_vault, PASSPHRASE_B)
    assert result.vault_path == str(target_vault)
    assert result.source_path == str(source_vault)


def test_promote_all_keys_no_overwrite(source_vault, target_vault):
    result = promote_keys(source_vault, PASSPHRASE_A, target_vault, PASSPHRASE_B)
    # DB_HOST exists in target → skipped by default
    assert "DB_HOST" in result.skipped
    # DB_PORT and SECRET_KEY are new → promoted
    assert "DB_PORT" in result.promoted
    assert "SECRET_KEY" in result.promoted


def test_promote_with_overwrite(source_vault, target_vault):
    result = promote_keys(
        source_vault, PASSPHRASE_A, target_vault, PASSPHRASE_B, overwrite=True
    )
    assert "DB_HOST" in result.overwritten
    assert "DB_HOST" not in result.skipped


def test_promote_specific_keys(source_vault, target_vault):
    result = promote_keys(
        source_vault, PASSPHRASE_A, target_vault, PASSPHRASE_B,
        keys=["SECRET_KEY"],
    )
    assert "SECRET_KEY" in result.promoted
    assert "DB_PORT" not in result.promoted
    assert "DB_PORT" not in result.skipped


def test_promote_persists_new_key(source_vault, target_vault):
    promote_keys(source_vault, PASSPHRASE_A, target_vault, PASSPHRASE_B)
    v = Vault(target_vault.with_suffix(""))
    v.unlock(PASSPHRASE_B)
    content = target_vault.with_suffix("").read_text()
    assert "SECRET_KEY=abc123" in content


def test_promote_missing_source_raises(tmp_path, target_vault):
    with pytest.raises(PromoteError, match="Source vault not found"):
        promote_keys(
            tmp_path / "ghost.vault", PASSPHRASE_A, target_vault, PASSPHRASE_B
        )


def test_promote_missing_target_raises(source_vault, tmp_path):
    with pytest.raises(PromoteError, match="Target vault not found"):
        promote_keys(
            source_vault, PASSPHRASE_A, tmp_path / "ghost.vault", PASSPHRASE_B
        )


def test_promote_has_skipped_flag(source_vault, target_vault):
    result = promote_keys(source_vault, PASSPHRASE_A, target_vault, PASSPHRASE_B)
    assert result.has_skipped() is True


def test_promote_as_dict_keys(source_vault, target_vault):
    result = promote_keys(source_vault, PASSPHRASE_A, target_vault, PASSPHRASE_B)
    d = result.as_dict()
    assert set(d.keys()) == {"vault_path", "source_path", "promoted", "skipped", "overwritten"}
