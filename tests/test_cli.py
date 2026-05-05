"""Tests for the envault CLI commands."""

import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli import cli


PASSPHRASE = "test-passphrase-123"
ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=supersecret\n"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(ENV_CONTENT)
    return p


def test_lock_command_creates_vault(runner, env_file):
    vault_path = env_file.with_suffix(".vault")
    result = runner.invoke(
        cli, ["lock", str(env_file), "--passphrase", PASSPHRASE]
    )
    assert result.exit_code == 0, result.output
    assert vault_path.exists()
    assert "Locked" in result.output


def test_lock_command_custom_vault_path(runner, env_file, tmp_path):
    vault_path = tmp_path / "secrets.vault"
    result = runner.invoke(
        cli,
        ["lock", str(env_file), "--vault-file", str(vault_path), "--passphrase", PASSPHRASE],
    )
    assert result.exit_code == 0, result.output
    assert vault_path.exists()


def test_unlock_command_restores_env(runner, env_file, tmp_path):
    vault_path = env_file.with_suffix(".vault")
    runner.invoke(cli, ["lock", str(env_file), "--passphrase", PASSPHRASE])
    env_file.unlink()

    result = runner.invoke(
        cli, ["unlock", str(vault_path), "--env-file", str(env_file), "--passphrase", PASSPHRASE]
    )
    assert result.exit_code == 0, result.output
    assert env_file.read_text() == ENV_CONTENT
    assert "Unlocked" in result.output


def test_unlock_wrong_passphrase_exits_nonzero(runner, env_file):
    vault_path = env_file.with_suffix(".vault")
    runner.invoke(cli, ["lock", str(env_file), "--passphrase", PASSPHRASE])
    env_file.unlink()

    result = runner.invoke(
        cli,
        ["unlock", str(vault_path), "--env-file", str(env_file), "--passphrase", "wrongpass"],
    )
    assert result.exit_code != 0
    assert "Error" in result.output


def test_unlock_no_overwrite_flag(runner, env_file):
    vault_path = env_file.with_suffix(".vault")
    runner.invoke(cli, ["lock", str(env_file), "--passphrase", PASSPHRASE])
    # env_file still exists — should fail with --no-overwrite
    result = runner.invoke(
        cli,
        ["unlock", str(vault_path), "--env-file", str(env_file), "--passphrase", PASSPHRASE, "--no-overwrite"],
    )
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_passphrase_mismatch_on_lock(runner, env_file):
    result = runner.invoke(
        cli, ["lock", str(env_file)], input="passA\npassB\n"
    )
    assert result.exit_code != 0
    assert "do not match" in result.output
