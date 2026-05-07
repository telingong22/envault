"""Tests for envault.cli_ttl."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_ttl import ttl_group
from envault.vault import Vault

PASSPHRASE = "test-pass"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("KEY=value\n", encoding="utf-8")
    return Vault(env).lock(PASSPHRASE)


def test_set_command_exits_ok(runner: CliRunner, vault_file: Path):
    result = runner.invoke(ttl_group, ["set", str(vault_file), "3600"])
    assert result.exit_code == 0


def test_set_command_output_contains_expires(runner: CliRunner, vault_file: Path):
    result = runner.invoke(ttl_group, ["set", str(vault_file), "3600"])
    assert "expires" in result.output.lower()


def test_set_command_with_note(runner: CliRunner, vault_file: Path):
    result = runner.invoke(
        ttl_group, ["set", str(vault_file), "7200", "--note", "ci-run"]
    )
    assert result.exit_code == 0


def test_set_command_zero_seconds_fails(runner: CliRunner, vault_file: Path):
    result = runner.invoke(ttl_group, ["set", str(vault_file), "0"])
    assert result.exit_code != 0


def test_status_command_exits_ok(runner: CliRunner, vault_file: Path):
    runner.invoke(ttl_group, ["set", str(vault_file), "3600"])
    result = runner.invoke(ttl_group, ["status", str(vault_file)])
    assert result.exit_code == 0


def test_status_command_shows_valid(runner: CliRunner, vault_file: Path):
    runner.invoke(ttl_group, ["set", str(vault_file), "3600"])
    result = runner.invoke(ttl_group, ["status", str(vault_file)])
    assert "valid" in result.output.lower()


def test_status_command_json_flag(runner: CliRunner, vault_file: Path):
    import json
    runner.invoke(ttl_group, ["set", str(vault_file), "3600"])
    result = runner.invoke(ttl_group, ["status", str(vault_file), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "expires_at" in data


def test_status_no_ttl_fails(runner: CliRunner, vault_file: Path):
    result = runner.invoke(ttl_group, ["status", str(vault_file)])
    assert result.exit_code != 0


def test_clear_command_exits_ok(runner: CliRunner, vault_file: Path):
    runner.invoke(ttl_group, ["set", str(vault_file), "3600"])
    result = runner.invoke(ttl_group, ["clear", str(vault_file)])
    assert result.exit_code == 0
    assert "cleared" in result.output.lower()


def test_clear_command_no_ttl_reports(runner: CliRunner, vault_file: Path):
    result = runner.invoke(ttl_group, ["clear", str(vault_file)])
    assert result.exit_code == 0
    assert "no ttl" in result.output.lower()
