"""Tests for envault.cli_diff_apply."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_diff_apply import diff_apply_group

PASSPHRASE = "cli-test-secret"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("API_KEY=abc123\nDEBUG=true\n")
    vf = tmp_path / ".env.vault"
    v = Vault(env, vf)
    v.lock(PASSPHRASE)
    env.unlink(missing_ok=True)
    return vf


def test_run_command_exits_ok(runner, vault_file):
    result = runner.invoke(diff_apply_group, ["run", str(vault_file), "-p", PASSPHRASE])
    assert result.exit_code == 0


def test_run_command_no_changes_message(runner, vault_file):
    result = runner.invoke(diff_apply_group, ["run", str(vault_file), "-p", PASSPHRASE])
    assert "No changes" in result.output


def test_run_command_set_adds_key(runner, vault_file):
    result = runner.invoke(
        diff_apply_group,
        ["run", str(vault_file), "-p", PASSPHRASE, "--set", "NEW_KEY=hello"],
    )
    assert result.exit_code == 0
    assert "Added" in result.output
    assert "NEW_KEY" in result.output


def test_run_command_set_updates_key(runner, vault_file):
    result = runner.invoke(
        diff_apply_group,
        ["run", str(vault_file), "-p", PASSPHRASE, "--set", "DEBUG=false"],
    )
    assert result.exit_code == 0
    assert "Updated" in result.output


def test_run_command_json_flag(runner, vault_file):
    result = runner.invoke(
        diff_apply_group,
        ["run", str(vault_file), "-p", PASSPHRASE, "--set", "X=1", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "added" in data
    assert "updated" in data
    assert "removed" in data


def test_run_command_dry_run_prefix(runner, vault_file):
    result = runner.invoke(
        diff_apply_group,
        ["run", str(vault_file), "-p", PASSPHRASE, "--set", "DRY=1", "--dry-run"],
    )
    assert result.exit_code == 0
    assert "dry-run" in result.output


def test_run_command_from_target_file(runner, vault_file, tmp_path):
    target = tmp_path / "target.env"
    target.write_text("FROM_FILE=yes\n")
    result = runner.invoke(
        diff_apply_group,
        ["run", str(vault_file), "-p", PASSPHRASE, "--target", str(target)],
    )
    assert result.exit_code == 0
    assert "FROM_FILE" in result.output


def test_run_command_missing_vault_fails(runner, tmp_path):
    result = runner.invoke(
        diff_apply_group,
        ["run", str(tmp_path / "ghost.vault"), "-p", PASSPHRASE],
    )
    assert result.exit_code != 0
