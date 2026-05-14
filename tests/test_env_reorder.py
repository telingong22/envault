"""Tests for envault.env_reorder."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.vault import Vault
from envault.env_reorder import ReorderError, ReorderResult, reorder_keys


PASSPHRASE = "test-secret"

ENV_CONTENT = """ALPHA=1
BETA=2
GAMMA=3
DELTA=4
"""


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    v = Vault(env)
    vp = tmp_path / ".env.vault"
    v.lock(PASSPHRASE, vault_path=vp)
    env.unlink(missing_ok=True)
    return vp


def test_reorder_returns_reorder_result(vault_file: Path) -> None:
    result = reorder_keys(vault_file, PASSPHRASE, ["DELTA", "ALPHA"])
    assert isinstance(result, ReorderResult)


def test_reorder_result_contains_vault_path(vault_file: Path) -> None:
    result = reorder_keys(vault_file, PASSPHRASE, ["BETA"])
    assert result.vault_path == str(vault_file)


def test_reorder_ordered_list_contains_found_keys(vault_file: Path) -> None:
    result = reorder_keys(vault_file, PASSPHRASE, ["GAMMA", "ALPHA"])
    assert "GAMMA" in result.ordered
    assert "ALPHA" in result.ordered


def test_reorder_missing_key_goes_to_unchanged(vault_file: Path) -> None:
    result = reorder_keys(vault_file, PASSPHRASE, ["ALPHA", "MISSING"])
    assert "MISSING" in result.unchanged
    assert "ALPHA" not in result.unchanged


def test_reorder_keys_appear_first_after_unlock(vault_file: Path, tmp_path: Path) -> None:
    reorder_keys(vault_file, PASSPHRASE, ["DELTA", "BETA"])
    env = tmp_path / ".env"
    v = Vault(env)
    v.unlock(PASSPHRASE, vault_path=vault_file)
    lines = [l for l in env.read_text().splitlines() if "=" in l and not l.startswith("#")]
    keys_in_order = [l.split("=", 1)[0].strip() for l in lines]
    assert keys_in_order[0] == "DELTA"
    assert keys_in_order[1] == "BETA"


def test_reorder_all_keys_preserved(vault_file: Path, tmp_path: Path) -> None:
    reorder_keys(vault_file, PASSPHRASE, ["DELTA"])
    env = tmp_path / ".env"
    v = Vault(env)
    v.unlock(PASSPHRASE, vault_path=vault_file)
    content = env.read_text()
    for key in ["ALPHA", "BETA", "GAMMA", "DELTA"]:
        assert key in content


def test_reorder_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(ReorderError, match="Vault not found"):
        reorder_keys(tmp_path / "ghost.vault", PASSPHRASE, ["KEY"])


def test_reorder_empty_key_order_raises(vault_file: Path) -> None:
    with pytest.raises(ReorderError, match="key_order"):
        reorder_keys(vault_file, PASSPHRASE, [])
