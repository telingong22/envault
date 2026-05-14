"""Tests for envault.cli_promote."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_promote import promote_group
from envault.vault import Vault


PASSPHRASE_A = "source-pass"
PASSPHRASE_B = "target-pass"


def _make_vault(tmp_path: Path, name: str, passphrase: str, content: str) -> Path:
    env = tmp_path / name
    env.write_text(content)
    v = Vault(env)
    v.lock(passphrase)
    return Path(str(env) + ".vault")


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def source_vault(tmp_path):
    return _make_vault(tmp_path, "src.env", PASSPHRASE_A, "NEW_KEY=hello\nSHARED=old\n")


@pytest.fixture()
def target_vault(tmp_path):
    return _make_vault(tmp_path, "tgt.env", PASSPHRASE_B, "EXISTING=yes\nSHARED=keep\n")


def test_run_command_exits_ok(runner, source_vault, target_vault):
    result = runner.invoke(
        promote_group,
        ["run", str(source_vault), str(target_vault),
         "--source-pass", PASSPHRASE_A, "--target-pass", PASSPHRASE_B],
    )
    assert result.exit_code == 0


def test_run_command_output_contains_promoted(runner, source_vault, target_vault):
    result = runner.invoke(
        promote_group,
        ["run", str(source_vault), str(target_vault),
         "--source-pass", PASSPHRASE_A, "--target-pass", PASSPHRASE_B],
    )
    assert "Promoted" in result.output


def test_run_command_json_flag(runner, source_vault, target_vault):
    import json
    result = runner.invoke(
        promote_group,
        ["run", str(source_vault), str(target_vault),
         "--source-pass", PASSPHRASE_A, "--target-pass", PASSPHRASE_B, "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "promoted" in data
    assert "skipped" in data


def test_run_command_specific_key(runner, source_vault, target_vault):
    result = runner.invoke(
        promote_group,
        ["run", str(source_vault), str(target_vault),
         "--source-pass", PASSPHRASE_A, "--target-pass", PASSPHRASE_B,
         "--key", "NEW_KEY", "--json"],
    )
    import json
    data = json.loads(result.output)
    assert "NEW_KEY" in data["promoted"]


def test_run_command_missing_source_fails(runner, tmp_path, target_vault):
    result = runner.invoke(
        promote_group,
        ["run", str(tmp_path / "ghost.vault"), str(target_vault),
         "--source-pass", PASSPHRASE_A, "--target-pass", PASSPHRASE_B],
    )
    assert result.exit_code != 0
    assert "Error" in result.output
