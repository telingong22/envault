"""CLI tests for envault.cli_chain."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_chain import chain_group
from envault.vault import Vault

PASS = "test-pass"


@pytest.fixture()
def runner():
    return CliRunner()


def _make_vault(tmp_path: Path, name: str, content: str) -> Path:
    env = tmp_path / f"{name}.env"
    vault = tmp_path / f"{name}.vault"
    env.write_text(content)
    Vault(env, vault).lock(PASS)
    env.unlink()
    return vault


@pytest.fixture()
def vault_a(tmp_path):
    return _make_vault(tmp_path, "a", "APP_ENV=production\nDB_HOST=prod-db\n")


@pytest.fixture()
def vault_b(tmp_path):
    return _make_vault(tmp_path, "b", "APP_ENV=staging\nEXTRA=only-b\n")


def test_resolve_command_exits_ok(runner, vault_a, vault_b):
    result = runner.invoke(
        chain_group,
        ["resolve", "APP_ENV", "--vault", str(vault_a), "--vault", str(vault_b),
         "--passphrase", PASS],
    )
    assert result.exit_code == 0


def test_resolve_command_shows_value(runner, vault_a, vault_b):
    result = runner.invoke(
        chain_group,
        ["resolve", "APP_ENV", "--vault", str(vault_a), "--vault", str(vault_b),
         "--passphrase", PASS],
    )
    assert "production" in result.output


def test_resolve_command_shows_found_in(runner, vault_a, vault_b):
    result = runner.invoke(
        chain_group,
        ["resolve", "EXTRA", "--vault", str(vault_a), "--vault", str(vault_b),
         "--passphrase", PASS],
    )
    assert str(vault_b) in result.output


def test_resolve_command_json_flag(runner, vault_a, vault_b):
    result = runner.invoke(
        chain_group,
        ["resolve", "DB_HOST", "--vault", str(vault_a), "--vault", str(vault_b),
         "--passphrase", PASS, "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["key"] == "DB_HOST"
    assert data["found"] is True


def test_resolve_missing_key_exits_nonzero(runner, vault_a):
    result = runner.invoke(
        chain_group,
        ["resolve", "GHOST", "--vault", str(vault_a), "--passphrase", PASS],
    )
    assert result.exit_code != 0
