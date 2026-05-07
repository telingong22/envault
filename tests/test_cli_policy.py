"""Tests for envault.cli_policy."""
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_policy import policy_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PASS=secret123\nAPI_KEY=abcdef\n")
    return p


@pytest.fixture
def env_file_with_empty(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PASS=\n")
    return p


def test_check_command_exits_ok(runner, env_file):
    result = runner.invoke(policy_group, ["check", str(env_file)])
    assert result.exit_code == 0


def test_check_command_output_passed(runner, env_file):
    result = runner.invoke(policy_group, ["check", str(env_file)])
    assert "passed" in result.output


def test_check_no_empty_fails_on_empty_value(runner, env_file_with_empty):
    result = runner.invoke(policy_group, ["check", str(env_file_with_empty), "--no-empty"])
    assert result.exit_code != 0
    assert "DB_PASS" in result.output


def test_check_min_length_fails(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("KEY=hi\n")
    result = runner.invoke(policy_group, ["check", str(p), "--min-length", "5"])
    assert result.exit_code != 0
    assert "KEY" in result.output


def test_check_key_pattern_fails(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("lowercase=value\n")
    result = runner.invoke(policy_group, ["check", str(p), "--key-pattern", "[A-Z][A-Z0-9_]+"])
    assert result.exit_code != 0


def test_check_require_missing_key(runner, env_file):
    result = runner.invoke(policy_group, ["check", str(env_file), "--require", "MISSING"])
    assert result.exit_code != 0
    assert "MISSING" in result.output


def test_check_require_present_key_passes(runner, env_file):
    result = runner.invoke(policy_group, ["check", str(env_file), "--require", "DB_HOST"])
    assert result.exit_code == 0


def test_check_missing_file_errors(runner, tmp_path):
    result = runner.invoke(policy_group, ["check", str(tmp_path / "nope.env")])
    assert result.exit_code != 0


def test_json_command_exits_ok(runner, env_file):
    result = runner.invoke(policy_group, ["check-json", str(env_file)])
    assert result.exit_code == 0


def test_json_command_valid_json(runner, env_file):
    result = runner.invoke(policy_group, ["check-json", str(env_file)])
    data = json.loads(result.output)
    assert "ok" in data
    assert "violations" in data


def test_json_command_reports_violations(runner, env_file_with_empty):
    result = runner.invoke(policy_group, ["check-json", str(env_file_with_empty), "--no-empty"])
    data = json.loads(result.output)
    assert not data["ok"]
    assert data["violation_count"] >= 1
