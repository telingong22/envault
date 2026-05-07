"""CLI tests for envault alias commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_alias import alias_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    p.write_bytes(b"dummy-vault-content")
    return p


def test_set_command_exits_ok(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(
        alias_group, ["set", "db", "DATABASE_URL", "--vault", str(vault_file)]
    )
    assert result.exit_code == 0


def test_set_command_output_contains_alias(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(
        alias_group, ["set", "db", "DATABASE_URL", "--vault", str(vault_file)]
    )
    assert "db" in result.output


def test_set_command_missing_vault_fails(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(
        alias_group,
        ["set", "db", "DATABASE_URL", "--vault", str(tmp_path / "no.vault")],
    )
    assert result.exit_code != 0
    assert "Vault not found" in result.output


def test_list_command_empty(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(alias_group, ["list", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "No aliases" in result.output


def test_list_command_shows_aliases(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(alias_group, ["set", "db", "DATABASE_URL", "--vault", str(vault_file)])
    runner.invoke(alias_group, ["set", "cache", "REDIS_URL", "--vault", str(vault_file)])
    result = runner.invoke(alias_group, ["list", "--vault", str(vault_file)])
    assert "db" in result.output
    assert "cache" in result.output


def test_remove_command_exits_ok(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(alias_group, ["set", "db", "DATABASE_URL", "--vault", str(vault_file)])
    result = runner.invoke(alias_group, ["remove", "db", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_unknown_alias_fails(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(alias_group, ["remove", "ghost", "--vault", str(vault_file)])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_resolve_command_prints_key(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(alias_group, ["set", "db", "DATABASE_URL", "--vault", str(vault_file)])
    result = runner.invoke(alias_group, ["resolve", "db", "--vault", str(vault_file)])
    assert result.exit_code == 0
    assert "DATABASE_URL" in result.output


def test_resolve_unknown_alias_fails(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(alias_group, ["resolve", "nope", "--vault", str(vault_file)])
    assert result.exit_code != 0
    assert "not defined" in result.output
