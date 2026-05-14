"""Tests for envault.cli_freeze."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_freeze import freeze_group

PASSPHRASE = "test-secret"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("API_KEY=abc123\nDEBUG=true\n")
    v = Vault(env)
    v.lock(PASSPHRASE)
    return tmp_path / ".env.vault"


def test_save_command_exits_ok(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(
        freeze_group, ["save", str(vault_file), "--passphrase", PASSPHRASE]
    )
    assert result.exit_code == 0


def test_save_command_output_mentions_frozen(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(
        freeze_group, ["save", str(vault_file), "--passphrase", PASSPHRASE]
    )
    assert "Frozen" in result.output


def test_save_command_output_contains_key_count(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(
        freeze_group, ["save", str(vault_file), "--passphrase", PASSPHRASE]
    )
    assert "2" in result.output


def test_show_command_exits_ok(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(freeze_group, ["save", str(vault_file), "--passphrase", PASSPHRASE])
    result = runner.invoke(freeze_group, ["show", str(vault_file)])
    assert result.exit_code == 0


def test_show_command_json_flag(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(freeze_group, ["save", str(vault_file), "--passphrase", PASSPHRASE])
    result = runner.invoke(freeze_group, ["show", str(vault_file), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "keys" in data


def test_show_command_missing_freeze_fails(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(freeze_group, ["show", str(vault_file)])
    assert result.exit_code != 0


def test_diff_command_no_drift(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(freeze_group, ["save", str(vault_file), "--passphrase", PASSPHRASE])
    result = runner.invoke(
        freeze_group, ["diff", str(vault_file), "--passphrase", PASSPHRASE]
    )
    assert result.exit_code == 0
    assert "No drift" in result.output


def test_diff_command_json_flag(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(freeze_group, ["save", str(vault_file), "--passphrase", PASSPHRASE])
    result = runner.invoke(
        freeze_group, ["diff", str(vault_file), "--passphrase", PASSPHRASE, "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "added" in data and "removed" in data and "changed" in data
