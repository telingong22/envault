"""CLI tests for envault mask commands."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_mask import mask_group
from envault.env_mask import list_masked
from envault.vault import Vault


PASSPHRASE = "hunter2"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text("API_KEY=secret\nDEBUG=true\nDB_PASS=s3cr3t\n")
    v = Vault(env)
    vault = v.lock(PASSPHRASE)
    return vault


def test_add_command_exits_ok(runner, vault_file):
    result = runner.invoke(
        mask_group, ["add", str(vault_file), "API_KEY", "--passphrase", PASSPHRASE]
    )
    assert result.exit_code == 0


def test_add_command_output_mentions_key(runner, vault_file):
    result = runner.invoke(
        mask_group, ["add", str(vault_file), "API_KEY", "--passphrase", PASSPHRASE]
    )
    assert "API_KEY" in result.output


def test_add_command_output_mentions_masked(runner, vault_file):
    result = runner.invoke(
        mask_group, ["add", str(vault_file), "API_KEY", "--passphrase", PASSPHRASE]
    )
    assert "asked" in result.output  # 'Masked'


def test_remove_command_exits_ok(runner, vault_file):
    runner.invoke(
        mask_group, ["add", str(vault_file), "API_KEY", "--passphrase", PASSPHRASE]
    )
    result = runner.invoke(
        mask_group, ["remove", str(vault_file), "API_KEY", "--passphrase", PASSPHRASE]
    )
    assert result.exit_code == 0


def test_remove_command_output_mentions_unmasked(runner, vault_file):
    runner.invoke(
        mask_group, ["add", str(vault_file), "API_KEY", "--passphrase", PASSPHRASE]
    )
    result = runner.invoke(
        mask_group, ["remove", str(vault_file), "API_KEY", "--passphrase", PASSPHRASE]
    )
    assert "nmasked" in result.output


def test_list_command_shows_masked_key(runner, vault_file):
    runner.invoke(
        mask_group, ["add", str(vault_file), "API_KEY", "--passphrase", PASSPHRASE]
    )
    result = runner.invoke(mask_group, ["list", str(vault_file)])
    assert result.exit_code == 0
    assert "API_KEY" in result.output


def test_list_command_empty_message(runner, vault_file):
    result = runner.invoke(mask_group, ["list", str(vault_file)])
    assert result.exit_code == 0
    assert "No masked" in result.output


def test_add_missing_vault_fails(runner, tmp_path):
    result = runner.invoke(
        mask_group,
        ["add", str(tmp_path / "ghost.vault"), "KEY", "--passphrase", PASSPHRASE],
    )
    assert result.exit_code != 0
