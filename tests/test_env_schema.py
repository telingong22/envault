"""Tests for envault.env_schema."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.env_schema import SchemaError, SchemaResult, validate
from envault.cli_schema import schema_group


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_URL=postgres://localhost/db\nSECRET_KEY=abc123\nDEBUG=true\n")
    return p


@pytest.fixture()
def schema_file(tmp_path: Path) -> Path:
    schema = {
        "required": ["DB_URL", "SECRET_KEY"],
        "optional": ["DEBUG"],
        "no_empty": False,
        "allow_extra": True,
    }
    p = tmp_path / "schema.json"
    p.write_text(json.dumps(schema))
    return p


def test_validate_returns_schema_result(env_file, schema_file):
    result = validate(env_file, schema_file)
    assert isinstance(result, SchemaResult)


def test_clean_env_passes(env_file, schema_file):
    result = validate(env_file, schema_file)
    assert result.ok
    assert result.violation_count == 0


def test_missing_required_key_fails(tmp_path, schema_file):
    env = tmp_path / ".env"
    env.write_text("DB_URL=postgres://localhost/db\n")  # SECRET_KEY missing
    result = validate(env, schema_file)
    assert not result.ok
    keys = [v.key for v in result.violations]
    assert "SECRET_KEY" in keys


def test_no_empty_detects_blank_value(tmp_path, tmp_path_factory):
    env = tmp_path / ".env"
    env.write_text("DB_URL=\nSECRET_KEY=abc\n")
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps({"required": ["DB_URL", "SECRET_KEY"], "no_empty": True}))
    result = validate(env, schema)
    assert not result.ok
    assert any(v.key == "DB_URL" for v in result.violations)


def test_unknown_key_flagged_when_allow_extra_false(tmp_path):
    env = tmp_path / ".env"
    env.write_text("DB_URL=x\nSECRET_KEY=y\nUNKNOWN_KEY=z\n")
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps({"required": ["DB_URL", "SECRET_KEY"], "allow_extra": False}))
    result = validate(env, schema)
    assert not result.ok
    assert any(v.key == "UNKNOWN_KEY" for v in result.violations)


def test_missing_env_file_raises(tmp_path, schema_file):
    with pytest.raises(SchemaError, match="Env file not found"):
        validate(tmp_path / "nonexistent.env", schema_file)


def test_invalid_schema_raises(env_file, tmp_path):
    bad_schema = tmp_path / "bad.json"
    bad_schema.write_text("not json{{")
    with pytest.raises(SchemaError):
        validate(env_file, bad_schema)


def test_summary_passed(env_file, schema_file):
    result = validate(env_file, schema_file)
    assert "passed" in result.summary()


def test_summary_failed_contains_key(tmp_path, schema_file):
    env = tmp_path / ".env"
    env.write_text("DB_URL=x\n")
    result = validate(env, schema_file)
    assert "SECRET_KEY" in result.summary()


def test_as_dict_structure(env_file, schema_file):
    d = validate(env_file, schema_file).as_dict()
    assert "ok" in d
    assert "violation_count" in d
    assert "violations" in d


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


def test_check_command_exits_ok(runner, env_file, schema_file):
    result = runner.invoke(schema_group, ["check", str(env_file), str(schema_file)])
    assert result.exit_code == 0


def test_check_command_output_passed(runner, env_file, schema_file):
    result = runner.invoke(schema_group, ["check", str(env_file), str(schema_file)])
    assert "passed" in result.output


def test_json_command_valid_json(runner, env_file, schema_file):
    result = runner.invoke(schema_group, ["json", str(env_file), str(schema_file)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True
