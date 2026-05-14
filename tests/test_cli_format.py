"""Tests for the format CLI group."""
from __future__ import annotations

from pathlib import Path
import json

import pytest
from click.testing import CliRunner

from envault.cli_format import format_group
from envault.vault import Vault

PASSPHRASE = "cli-format-pass"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("API_KEY = secret  \nDEBUG=true \n")
    v = Vault(env)
    vault = tmp_path / ".env.vault"
    v.lock(PASSPHRASE, vault_path=vault)
    return vault


def test_run_command_exits_ok(runner: CliRunner, vault_file: Path):
    result = runner.invoke(
        format_group, ["run", str(vault_file), "--passphrase", PASSPHRASE]
    )
    assert result.exit_code == 0


def test_run_command_output_contains_formatted(runner: CliRunner, vault_file: Path):
    result = runner.invoke(
        format_group, ["run", str(vault_file), "--passphrase", PASSPHRASE]
    )
    assert "Formatted" in result.output or "formatted" in result.output


def test_run_command_json_flag(runner: CliRunner, vault_file: Path):
    result = runner.invoke(
        format_group, ["run", str(vault_file), "--passphrase", PASSPHRASE, "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "vault_path" in data
    assert "changed" in data


def test_run_command_json_contains_changes(runner: CliRunner, vault_file: Path):
    result = runner.invoke(
        format_group, ["run", str(vault_file), "--passphrase", PASSPHRASE, "--json"]
    )
    data = json.loads(result.output)
    assert isinstance(data["changes"], list)


def test_run_command_missing_vault_fails(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(
        format_group,
        ["run", str(tmp_path / "no.vault"), "--passphrase", PASSPHRASE],
    )
    assert result.exit_code != 0


def test_run_command_vault_still_valid_after_format(runner: CliRunner, vault_file: Path, tmp_path: Path):
    runner.invoke(
        format_group, ["run", str(vault_file), "--passphrase", PASSPHRASE]
    )
    env_out = tmp_path / "out.env"
    v = Vault(env_out)
    content = v.unlock(PASSPHRASE, vault_path=vault_file)
    assert "API_KEY" in content
