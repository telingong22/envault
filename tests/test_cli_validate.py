"""Tests for envault.cli_validate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_validate import validate_group

PASS = "s3cret"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("API_KEY=abc123\nENV=production\n")
    v = Vault(env)
    v.lock(PASS)
    return tmp_path / ".env.vault"


def test_check_command_exits_ok(runner, vault_file):
    result = runner.invoke(
        validate_group,
        ["check", str(vault_file), "--passphrase", PASS],
    )
    assert result.exit_code == 0


def test_check_command_output_passed(runner, vault_file):
    result = runner.invoke(
        validate_group,
        ["check", str(vault_file), "--passphrase", PASS],
    )
    assert "passed" in result.output.lower()


def test_check_command_regex_pass(runner, vault_file):
    result = runner.invoke(
        validate_group,
        ["check", str(vault_file), "--passphrase", PASS, "--regex", "API_KEY=[a-z0-9]+"],
    )
    assert result.exit_code == 0


def test_check_command_regex_fail(runner, vault_file):
    result = runner.invoke(
        validate_group,
        ["check", str(vault_file), "--passphrase", PASS, "--regex", r"API_KEY=\d+"],
    )
    assert result.exit_code == 1
    assert "failed" in result.output.lower()


def test_check_command_choices_fail(runner, vault_file):
    result = runner.invoke(
        validate_group,
        ["check", str(vault_file), "--passphrase", PASS, "--choices", "ENV=dev,staging"],
    )
    assert result.exit_code == 1


def test_check_command_json_flag(runner, vault_file):
    result = runner.invoke(
        validate_group,
        ["check", str(vault_file), "--passphrase", PASS, "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "ok" in data
    assert "violations" in data


def test_check_command_missing_vault(runner, tmp_path):
    result = runner.invoke(
        validate_group,
        ["check", str(tmp_path / "ghost.vault"), "--passphrase", PASS],
    )
    assert result.exit_code == 1
