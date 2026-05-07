"""Tests for envault.compare."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.compare import compare_vaults, CompareError, CompareResult
from envault.cli_compare import compare_group

PASS_A = "secret-a"
PASS_B = "secret-b"


@pytest.fixture()
def vault_a(tmp_path: Path) -> Path:
    env = tmp_path / "a.env"
    env.write_text("FOO=bar\nSHARED=same\nCHANGED=original\n")
    v = Vault(env, tmp_path / "a.vault")
    v.lock(PASS_A)
    return tmp_path / "a.vault"


@pytest.fixture()
def vault_b(tmp_path: Path) -> Path:
    env = tmp_path / "b.env"
    env.write_text("BAR=baz\nSHARED=same\nCHANGED=modified\n")
    v = Vault(env, tmp_path / "b.vault")
    v.lock(PASS_B)
    return tmp_path / "b.vault"


def test_compare_returns_compare_result(vault_a, vault_b):
    result = compare_vaults(vault_a, vault_b, PASS_A, PASS_B)
    assert isinstance(result, CompareResult)


def test_compare_only_in_a(vault_a, vault_b):
    result = compare_vaults(vault_a, vault_b, PASS_A, PASS_B)
    assert "FOO" in result.only_in_a


def test_compare_only_in_b(vault_a, vault_b):
    result = compare_vaults(vault_a, vault_b, PASS_A, PASS_B)
    assert "BAR" in result.only_in_b


def test_compare_changed_key(vault_a, vault_b):
    result = compare_vaults(vault_a, vault_b, PASS_A, PASS_B)
    assert "CHANGED" in result.changed


def test_compare_identical_key(vault_a, vault_b):
    result = compare_vaults(vault_a, vault_b, PASS_A, PASS_B)
    assert "SHARED" in result.identical


def test_compare_has_differences(vault_a, vault_b):
    result = compare_vaults(vault_a, vault_b, PASS_A, PASS_B)
    assert result.has_differences is True


def test_compare_identical_vaults_no_differences(tmp_path):
    env = tmp_path / "c.env"
    env.write_text("KEY=val\n")
    v1 = Vault(env, tmp_path / "c1.vault")
    v1.lock(PASS_A)
    v2 = Vault(env, tmp_path / "c2.vault")
    v2.lock(PASS_A)
    result = compare_vaults(tmp_path / "c1.vault", tmp_path / "c2.vault", PASS_A)
    assert result.has_differences is False


def test_compare_missing_vault_raises(tmp_path, vault_b):
    with pytest.raises(CompareError):
        compare_vaults(tmp_path / "ghost.vault", vault_b, PASS_A, PASS_B)


def test_cli_run_exits_ok(vault_a, vault_b):
    runner = CliRunner()
    result = runner.invoke(
        compare_group,
        ["run", str(vault_a), str(vault_b), "--passphrase", PASS_A, "--passphrase-b", PASS_B],
    )
    assert result.exit_code == 0


def test_cli_run_json_output(vault_a, vault_b):
    runner = CliRunner()
    result = runner.invoke(
        compare_group,
        ["run", str(vault_a), str(vault_b), "--passphrase", PASS_A, "--passphrase-b", PASS_B, "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "only_in_a" in data
    assert "only_in_b" in data
    assert "changed" in data
