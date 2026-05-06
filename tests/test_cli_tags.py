"""Tests for envault.cli_tags."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_tags import tags_group
from envault.tags import add_tag


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.vault"
    p.write_bytes(b"dummy")
    return p


def test_add_command_exits_ok(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(tags_group, ["add", str(vault_file), "production"])
    assert result.exit_code == 0


def test_add_command_output_contains_tag(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(tags_group, ["add", str(vault_file), "staging"])
    assert "staging" in result.output


def test_add_multiple_tags_shown(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(tags_group, ["add", str(vault_file), "a"])
    result = runner.invoke(tags_group, ["add", str(vault_file), "b"])
    assert "a" in result.output
    assert "b" in result.output


def test_remove_command_exits_ok(runner: CliRunner, vault_file: Path) -> None:
    add_tag(vault_file, "temp")
    result = runner.invoke(tags_group, ["remove", str(vault_file), "temp"])
    assert result.exit_code == 0


def test_remove_command_tag_no_longer_in_output(
    runner: CliRunner, vault_file: Path
) -> None:
    add_tag(vault_file, "temp")
    result = runner.invoke(tags_group, ["remove", str(vault_file), "temp"])
    assert "temp" not in result.output or "none" in result.output.lower()


def test_list_command_no_tags(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(tags_group, ["list", str(vault_file)])
    assert result.exit_code == 0
    assert "No tags" in result.output


def test_list_command_shows_tags(runner: CliRunner, vault_file: Path) -> None:
    add_tag(vault_file, "live")
    result = runner.invoke(tags_group, ["list", str(vault_file)])
    assert "live" in result.output


def test_find_command_matches_vault(runner: CliRunner, vault_file: Path) -> None:
    add_tag(vault_file, "prod")
    result = runner.invoke(
        tags_group, ["find", "prod", "--dir", str(vault_file.parent)]
    )
    assert result.exit_code == 0
    assert vault_file.name in result.output


def test_find_command_no_match(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(
        tags_group, ["find", "ghost", "--dir", str(vault_file.parent)]
    )
    assert result.exit_code == 0
    assert "No matching" in result.output
